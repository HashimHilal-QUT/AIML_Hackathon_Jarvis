# Bedtime Story Backend — Implementation Plan

## Context
The "One Thousand and One Night" project needs its backend built from scratch. The repo has an empty scaffold on the `backend` branch: `main.py`, `models/`, `routes/`, `utils/` all exist but are empty. The `llmops/` directory with `system_prompt.txt` and `pipeline.py` is also empty. The frontend is React 19 + Vite + Tailwind (boilerplate only). Deployment targets an Azure VM via GitHub Actions SSH.
This plan covers the full backend: story generation via LLM, narrated audio via TTS with circuit-breaker failover, and a voice command pipeline (STT + intent parsing) that lets users control the app hands-free.

---

## File Structure
All paths relative to `F:/document/aiml_hackathon/AIML_Hackathon_Jarvis/`.

```
backend/
  .env.example                          # env template
  requirements.txt                      # Python deps
  src/
    main.py                             # FastAPI app + CORS + router mounts
    config.py                           # [NEW] pydantic-settings loader
    models/
      __init__.py                       # [NEW]
      schemas.py                        # [NEW] all Pydantic request/response models
    routes/
      __init__.py                       # [NEW]
      stories.py                        # [NEW] POST /api/stories/generate, /api/stories/audio
      voice.py                          # [NEW] POST /api/voice/command
      health.py                         # [NEW] GET /api/health
      feedback.py                       # [NEW] POST /api/feedback
    services/                           # [NEW dir]
      __init__.py
      story_generator.py                # LLM story generation
      tts.py                            # TTS orchestrator (primary + fallback + circuit breaker)
      stt.py                            # STT orchestrator (primary + fallback + circuit breaker)
      intent_parser.py                  # transcript -> action JSON via LLM
      storage.py                        # Azure Blob upload + SAS URL generation
    providers/                          # [NEW dir]
      __init__.py
      tts_elevenlabs.py                 # ElevenLabs TTS wrapper
      tts_google.py                     # Google Cloud TTS wrapper (fallback)
      stt_whisper.py                    # OpenAI Whisper STT wrapper
      stt_google.py                     # Google Cloud STT wrapper (fallback)
    utils/
      __init__.py                       # [NEW]
      circuit_breaker.py                # [NEW] CircuitBreaker class
      provider_config.py                # [NEW] voice/speed/mood -> provider param mapping
  tests/
    test_main.py                        # integration smoke tests
    test_circuit_breaker.py             # [NEW] circuit breaker unit tests
llmops/
  prompts/
    system_prompt.txt                   # story generation system prompt
    intent_prompt.txt                   # [NEW] intent parsing system prompt

```

---

## Implementation Phases
### Phase 1 — Skeleton & Health (~30 min)
**Files:** `requirements.txt`, `.env.example`, `config.py`, `models/schemas.py`, `main.py`, `routes/health.py`
1. **`requirements.txt`** — populate:
   ```
   fastapi==0.115.0
   uvicorn[standard]==0.30.0
   pydantic==2.9.0
   pydantic-settings==2.5.0
   python-dotenv==1.0.1
   python-multipart==0.0.9
   anthropic==0.39.0
   openai==1.50.0
   elevenlabs==1.9.0
   google-cloud-texttospeech==2.17.0
   google-cloud-speech==2.27.0
   azure-storage-blob==12.22.0
   httpx==0.27.0
   pytest==8.3.0
   pytest-asyncio==0.24.0
   ```
2. **`.env.example`** — all config vars:
   ```
   ANTHROPIC_API_KEY=
   OPENAI_API_KEY=
   LLM_PROVIDER=anthropic
   LLM_MODEL=claude-sonnet-4-20250514
   ELEVENLABS_API_KEY=
   GOOGLE_TTS_CREDENTIALS_JSON=
   TTS_PRIMARY_PROVIDER=elevenlabs
   OPENAI_API_KEY_STT=
   GOOGLE_STT_CREDENTIALS_JSON=
   STT_PRIMARY_PROVIDER=whisper
   AZURE_STORAGE_CONNECTION_STRING=
   AZURE_STORAGE_CONTAINER=story-audio
   AZURE_SAS_EXPIRY_HOURS=24
   CB_FAILURE_THRESHOLD=3
   CB_RECOVERY_TIMEOUT_SECONDS=60
   CORS_ORIGINS=http://localhost:5173,http://localhost:3000
   DEBUG=false
   ```
3. **`config.py`** — `Settings(BaseSettings)` loading all env vars via `pydantic-settings`. Single `settings = Settings()` instance.
4. **`models/schemas.py`** — all Pydantic models in one file:
   - Enums: `Genre`, `Mood`, `StoryLength`, `VoiceGender`, `VoiceSpeed`, `ActionType`
   - Requests: `StoryGenerateRequest`, `AudioGenerateRequest`, `FeedbackRequest`
   - Responses: `StoryGenerateResponse`, `AudioGenerateResponse`, `VoiceAction`, `VoiceCommandResponse`, `HealthResponse`, `FeedbackResponse`
5. **`main.py`** — FastAPI app, CORS middleware (origins from config), include all routers.
6. **`routes/health.py`** — `GET /api/health` returning static healthy status initially.
**Verify:** `uvicorn src.main:app --reload` starts, `/api/health` returns JSON.

---

### Phase 2 — Story Generation (~45 min)
**Files:** `system_prompt.txt`, `services/story_generator.py`, `routes/stories.py`
7. **`llmops/prompts/system_prompt.txt`** — bedtime storyteller system prompt. Includes genre guidelines (heartwarming, horror=cozy-creepy, study, fantasy, adventure, scifi), mood modifiers (cozy, calm, adventurous, fun, mysterious), and output format: `{"title": "...", "body": "..."}`.
8. **`services/story_generator.py`**:
   - Load system prompt once at module level (cached)
   - Map `StoryLength` to target word count: `{"3": 450, "5": 750, "10": 1500}`
   - `async def generate_story(genre, mood, length) -> dict` — calls Anthropic (or OpenAI based on config) with system prompt + user prompt, parses JSON response, generates UUID story_id
   - For Anthropic: use `cache_control` on system message for prompt caching
9. **`routes/stories.py`** — `POST /api/stories/generate` wired to `story_generator.generate_story`.
**Verify:** curl POST with `{"genre":"fantasy","mood":"cozy","length":"3"}`, get story back.

---

### Phase 3 — Circuit Breaker (~30 min)
**Files:** `utils/circuit_breaker.py`, `tests/test_circuit_breaker.py`
10. **`utils/circuit_breaker.py`** — `CircuitBreaker` class with:
    - Three states: `CLOSED` (normal), `OPEN` (blocked), `HALF_OPEN` (testing recovery)
    - Constructor: `name`, `failure_threshold`, `recovery_timeout`
    - `async call(func, *args, **kwargs)` — executes func through the breaker
    - On success → reset failure count, go CLOSED
    - On failure → increment count, if >= threshold go OPEN
    - When OPEN and recovery timeout elapsed → transition to HALF_OPEN, allow one call
    - `get_state()` — returns current state string (rechecks timeout)
    - `CircuitOpenError` exception
    - Async lock for thread safety
11. **`tests/test_circuit_breaker.py`** — test state transitions: closed→open on failures, open→half_open after timeout, half_open→closed on success, half_open→open on failure.
**Verify:** `pytest tests/test_circuit_breaker.py` passes.

---

### Phase 4 — TTS Pipeline (~60 min)
**Files:** `utils/provider_config.py`, `providers/tts_elevenlabs.py`, `providers/tts_google.py`, `services/storage.py`, `services/tts.py`, update `routes/stories.py`
12. **`utils/provider_config.py`** — mapping tables:
    - `ELEVENLABS_VOICES = {"male": "<voice_id>", "female": "<voice_id>"}`
    - `GOOGLE_TTS_VOICES = {"male": "en-US-Neural2-D", "female": "en-US-Neural2-F"}`
    - Speed maps: app values → provider-specific floats
    - Mood maps: mood → ElevenLabs stability/style params, mood → Google pitch
    - `get_elevenlabs_params(mood, gender, speed) -> dict`
    - `get_google_tts_params(mood, gender, speed) -> dict`
13. **`providers/tts_elevenlabs.py`** — `async def synthesize(text, voice_id, speed, stability, style) -> bytes` — calls ElevenLabs API, returns MP3 bytes.
14. **`providers/tts_google.py`** — `async def synthesize(text, voice_name, speaking_rate, pitch) -> bytes` — calls Google Cloud TTS, returns MP3 bytes.
15. **`services/storage.py`** — `async def upload_audio(audio_bytes, filename) -> str` — uploads to Azure Blob container, generates SAS URL with configurable expiry, returns URL.
16. **`services/tts.py`** — TTS orchestrator:
    - Two `CircuitBreaker` instances: `_cb_primary`, `_cb_fallback`
    - `async def generate_audio(story_text, mood, voice_gender, voice_speed) -> dict`
    - Try primary provider through `_cb_primary.call()`, on any failure try fallback through `_cb_fallback.call()`
    - Upload audio bytes via `storage.upload_audio()`
    - Return `AudioGenerateResponse` fields including `provider_used`
17. Update **`routes/stories.py`** — add `POST /api/stories/audio` wired to `tts.generate_audio`.
**Verify:** POST audio generation, get SAS URL, audio plays in browser.

---

### Phase 5 — Voice Command Pipeline (~45 min)
**Files:** `providers/stt_whisper.py`, `providers/stt_google.py`, `services/stt.py`, `intent_prompt.txt`, `services/intent_parser.py`, `routes/voice.py`
18. **`providers/stt_whisper.py`** — `async def transcribe(audio_bytes, content_type) -> str` — calls OpenAI Whisper API.
19. **`providers/stt_google.py`** — `async def transcribe(audio_bytes, content_type) -> str` — calls Google Cloud STT.
20. **`services/stt.py`** — STT orchestrator with circuit breaker (same pattern as TTS).
21. **`llmops/prompts/intent_prompt.txt`** — describes all valid actions, valid parameter values, output JSON format, and few-shot examples.
22. **`services/intent_parser.py`** — `async def parse_intent(transcript) -> dict` — loads intent prompt (cached), sends transcript to LLM, parses structured action JSON.
23. **`routes/voice.py`** — `POST /api/voice/command` receives `UploadFile`, calls `stt.transcribe()` then `intent_parser.parse_intent()`, returns `VoiceCommandResponse`.
**Verify:** POST audio file to `/api/voice/command`, get action JSON back.

---

### Phase 6 — Polish (~30 min)
**Files:** `routes/feedback.py`, update `routes/health.py`, `tests/test_main.py`
24. **`routes/feedback.py`** — `POST /api/feedback` logs feedback (stdout for hackathon).
25. Update **`routes/health.py`** — wire in circuit breaker states from `tts._cb_primary`, `stt._cb_primary`, report "degraded" if any circuit is open.
26. **`tests/test_main.py`** — integration smoke tests: app starts, health returns 200, routes exist.
**Verify:** Full end-to-end flow works. Health endpoint shows circuit states.

---

## API Endpoints Summary
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/stories/generate` | Generate story from genre/mood/length |
| POST | `/api/stories/audio` | Generate narrated audio from story text |
| POST | `/api/voice/command` | Voice command: audio in -> action JSON out |
| GET | `/api/health` | Health + circuit breaker status |
| POST | `/api/feedback` | Record like/dislike feedback |

---

## Key Design Decisions
- **`services/` vs `providers/`**: Providers are thin API wrappers (one function each). Services contain business logic and circuit breaker orchestration. Swapping a provider = changing one file.
- **Circuit breaker as a class, not decorator**: Allows health endpoint to inspect state via `get_state()`. Makes testing straightforward.
- **Single `schemas.py`**: ~15 models total — one file is faster to navigate for a hackathon.
- **System prompt cached at module level**: Read once from file at import time. For Anthropic, also uses `cache_control` header for server-side caching (~90% cost reduction on repeated calls).
- **Azure Blob + SAS URLs for audio**: Team is already on Azure. SAS URLs are time-limited, no auth needed for playback, auto-expire.
- **`python-multipart` for voice endpoint**: Required by FastAPI for `UploadFile` handling.

---

## Verification
After all phases complete:
1. `uvicorn src.main:app --reload` from `backend/` directory
2. `GET /api/health` returns `{"status":"healthy", "tts_circuit":"closed", ...}`
3. `POST /api/stories/generate` with preferences returns story JSON
4. `POST /api/stories/audio` with story text returns audio SAS URL that plays in browser
5. `POST /api/voice/command` with audio file returns action JSON
6. `POST /api/feedback` records feedback
7. `pytest tests/` passes all tests