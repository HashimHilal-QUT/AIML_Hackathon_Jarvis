# SMS AI Chatbot (Australia-ready)

A production-ready Flask backend that receives SMS via Twilio or PlaySMS, forwards to OpenAI (gpt-4o-mini by default), and replies via SMS. Stores short per-number conversation history in SQLite.

## Features
- Twilio webhook or PlaySMS webhook for inbound SMS
- OpenAI chat with concise, SMS-friendly replies
- SQLite history (~10 messages per number)
- Auto-split long replies into 320-char chunks
- Basic per-user rate limiting (0.5s)
- .env configuration

## Quick start (Local)

1. Python 3.11+
2. Install dependencies:
```
pip install -r requirements.txt
```
3. Configure environment:
```
cp env.example .env
# edit .env
```
4. Run the app:
```
python app.py
```
5. Expose locally (optional), e.g. using ngrok:
```
ngrok http 5000
```
Use the HTTPS forwarding URL for webhooks (e.g., https://xxxx.ngrok-free.app/sms).

## Docker & Compose

1. Build and run:
```
cp env.example .env
# Fill in OPENAI_API_KEY, Twilio creds, PORT (optional), NGROK_AUTHTOKEN (optional)
docker compose up --build
```
- The `app` service runs Gunicorn serving `app:app` on `${PORT:-5000}`
- The `ngrok` service exposes the app publicly and the ngrok inspector on `http://localhost:4040`

2. Get public URL:
```
curl -s http://127.0.0.1:4040/api/tunnels | jq -r '.tunnels[0].public_url'
```
Set your Twilio number webhook to `PUBLIC_URL/sms` (POST).

3. Data persistence:
- `conversations.db` is bind-mounted, so history persists across restarts.

## Webhook endpoint
- `POST /sms`
- Accepts both Twilio and PlaySMS webhook payloads.
- Response:
  - Twilio mode: returns TwiML with one or more `<Message>` nodes
  - PlaySMS mode: returns text and sends via PlaySMS HTTP API

## Environment variables
See `env.example`.

- **OPENAI_MODEL**: defaults to `gpt-4o-mini`
- **USE_TWILIO / USE_PLAYSMS**: set true/false
- **NGROK_AUTHTOKEN**: optional; improves stability of ngrok tunnels

## Twilio setup (Australia)
1. Create a Twilio account and verify billing for AU numbers.
2. Buy an Australian mobile number that supports SMS.
3. In Twilio Console > Phone Numbers > Manage > Active numbers > your AU number:
   - Messaging > A Message Comes In: set to Webhook
   - URL: `https://YOUR_DOMAIN/sms`
   - Method: POST
4. Set environment variables:
   - `USE_TWILIO=true`
   - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`
5. Testing:
   - Send an SMS to your Twilio AU number.
   - The app will respond via TwiML with concise replies. If you want to send using REST instead, adapt `send_via_twilio_rest` and call it in `/sms`.

Notes:
- Twilio AU numbers have local compliance. Ensure you’ve completed identity and address requirements in Twilio Console if required.
- On trial accounts, replies only deliver to verified caller IDs.

## PlaySMS setup (USB modem + SIM)
1. Install PlaySMS on a local server or VPS. Refer to PlaySMS docs for your OS.
2. Connect a USB GSM modem with an AU SIM card. Common stack: gammu-smsd or kannel + PlaySMS.
3. Configure the gateway in PlaySMS so outbound API works via your modem/SIM.
4. In PlaySMS:
   - Create an API key for the user or global (
     typically called `h` in the WS API).
   - Note your base URL, e.g., `http://YOUR_HOST/playsms`.
5. Set environment variables:
   - `USE_PLAYSMS=true` (and set `USE_TWILIO=false` or leave false)
   - `PLAYSMS_API_URL`, `PLAYSMS_API_KEY`, `PLAYSMS_SENDER_ID`
6. Configure inbound webhook to your Flask app:
   - Many PlaySMS installs can POST to a webhook on inbound. Configure to POST to `https://YOUR_DOMAIN/sms` with params like `from` and `text`.
   - If inbound webhook is not available, you can configure polling or custom connectors; adjust `/sms` to match your payload fields if needed.

## Conversation and limits
- Per-number history stored in SQLite. The last ~10 exchanges are sent to OpenAI.
- Replies trimmed to ~1000 chars and split into 320-char SMS segments.
- Basic rate limit: 0.5s between messages per sender.

## Deployment

### Replit
- Create a new Replit (Python template), upload files.
- Add secrets in the Secrets tab from `.env`.
- Set Run command: `python app.py`.
- Use Replit’s public URL for webhooks: `https://YOUR_REPL_NAME.YOUR_USER.repl.co/sms`.

### Railway
- Create a new Railway project, deploy from repo or upload.
- Add environment variables from `.env` in Variables.
- Expose a web service; default port is 5000.
- Use service domain for webhooks: `https://YOUR-APP.up.railway.app/sms`.

### Render
- Create a new Web Service.
- Build command: `pip install -r requirements.txt`
- Start command: `python app.py`
- Add environment variables in the dashboard.
- Use the service URL for webhooks.

## Security and reliability
- Keep API keys in environment variables only.
- Use HTTPS webhook URLs.
- Log only necessary info; avoid logging full message contents in production.

## Troubleshooting
- 400 Missing sender or message: verify payload fields names (`From`/`Body` for Twilio; `from`/`text` for PlaySMS).
- 429 Please wait: rate limit hit; wait >0.5s.
- OpenAI error: verify `OPENAI_API_KEY` and network egress.
- Twilio 11200/12200 errors: check your webhook’s response is valid XML and reachable over HTTPS.
- Twilio 21608 on trial: verify your handset number in Twilio or upgrade.

## License
MIT
