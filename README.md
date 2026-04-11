# 🤖 AIML Hackathon — Jarvis

Welcome to the Jarvis project repository! This README is your single source of truth for getting set up, understanding the project structure, and working effectively as a team.

![WhatsApp Image 2026-04-10 at 9 51 30 PM](https://github.com/user-attachments/assets/a7d546bb-7cb8-41b7-a20e-4f8d57dcb2cd)

---

## 📁 Project Structure

```
AIML_Hackathon_Jarvis/
├── .github/
│   └── workflows/
│       └── deploy.yml        # Auto-deploys to Azure VM on merge to main
├── frontend/                 # UI & client-side code
│   ├── src/
│   │   ├── components/
│   │   ├── assets/
│   │   ├── App.js
│   │   ├── index.html
│   │   └── styles.css
│   ├── public/
│   ├── package.json
│   └── .env.example
├── backend/                  # API & server-side logic
│   ├── src/
│   │   ├── routes/
│   │   ├── models/
│   │   └── utils/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── llmops/                   # LLM pipelines, prompts & evaluations
│   ├── models/
│   ├── pipelines/
│   ├── prompts/
│   └── evaluations/
├── wireframe/                # Design mockups & assets
│   ├── screens/
│   └── assets/
├── .gitignore
└── README.md
```

---

## 🌿 Branch Strategy

Each team member owns one branch. **Never push directly to `main`.**

| Branch | Owner | Purpose |
|---|---|---|
| `frontend` | Frontend Dev | UI components, pages, styling |
| `backend` | Backend Dev | API routes, database, server logic |
| `llmops` | LLM Engineer | Model pipelines, prompts, evaluations |
| `wireframe` | Designer | Mockups, screen designs, assets |
| `main` | Everyone (via PR) | Production — auto-deploys to Azure VM |

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone git@github.com:HashimHilal-QUT/AIML_Hackathon_Jarvis.git
cd AIML_Hackathon_Jarvis
```

### 2. Switch to your branch

```bash
git checkout frontend    # or backend / llmops / wireframe
```

### 3. Install dependencies

**Backend (Python):**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend (Node):**
```bash
cd frontend
npm install
```

### 4. Set up environment variables

```bash
# Copy the example file and fill in your values
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

> ⚠️ Never commit `.env` files. They are in `.gitignore` for a reason.

---

## 🔄 Daily Workflow

Follow these steps every day to avoid merge conflicts:

```bash
# 1. Pull the latest from main before starting work
git pull origin main

# 2. Do your work, then stage your changes
git add .

# 3. Commit with a clear message
git commit -m "feat: add login endpoint"

# 4. Push to YOUR branch only
git push origin your-branch-name
```

---

## 🔀 Merging Into Main (Pull Requests)

When your feature is ready:

1. Go to **GitHub → Pull Requests → New Pull Request**
2. Set **base:** `main` ← **compare:** `your-branch`
3. Write a clear description of what you changed
4. Request a review from at least one teammate
5. Once approved → click **Merge Pull Request**
6. 🚀 GitHub Actions will automatically deploy to the Azure VM

---

## ⚙️ CI/CD Pipeline

Every merge into `main` triggers an automated deployment:

```
Push to branch → Open PR → Review → Merge to main → GitHub Actions → Azure VM
```

You can monitor deployments in the **Actions** tab on GitHub.

---

## 📝 Commit Message Guidelines

Use clear, consistent commit messages so the team can follow the history:

| Prefix | Use for |
|---|---|
| `feat:` | A new feature |
| `fix:` | A bug fix |
| `docs:` | Documentation changes |
| `style:` | Formatting, no logic change |
| `refactor:` | Code restructure, no feature change |
| `test:` | Adding or updating tests |
| `chore:` | Dependency updates, config changes |

**Examples:**
```
feat: add user authentication endpoint
fix: resolve CORS error on /api/predict
docs: update README with setup instructions
```

---

## 🔐 Secrets & Environment Variables

- **Never** commit `.env` files or API keys to GitHub
- Store secrets in your local `.env` file (already gitignored)
- For production secrets, they are managed via **GitHub Secrets** (ask the repo owner)
- Use `.env.example` as a template — list variable names but leave values blank

---

## ✅ Golden Rules

1. 🚫 Never push directly to `main`
2. 🔄 Always pull from `main` before starting work
3. 🔐 Never commit `.env` files or API keys
4. 💬 Write meaningful commit messages
5. 👀 Review teammates' PRs — everyone is responsible for code quality
6. 🧪 Test your code before opening a PR

---

## 🆘 Common Issues

**SSH permission denied when pushing?**
```bash
# Check your SSH key is added to the agent
ssh-add ~/.ssh/id_ed25519
ssh -T git@github.com
```

**Merge conflict?**
```bash
git pull origin main
# Resolve conflicts in the flagged files
git add .
git commit -m "fix: resolve merge conflict"
git push origin your-branch
```

**Wrong branch?**
```bash
# Stash your work, switch branch, then pop
git stash
git checkout correct-branch
git stash pop
```

---

## 👥 Team

| Role | Branch |
|---|---|
| Frontend Developer | `frontend` |
| Backend Developer | `backend` |
| LLM / MLOps Engineer | `llmops` |
| Designer | `wireframe` |

---

*Last updated by repo owner. For questions, raise a GitHub Issue or message the team.*



# Bedtime Stories - Requirements Definition

## Product Name
**One Thousand and One Night**

---

## 1. Overview
This system is an application that generates, displays, and narrates personalized bedtime stories to help users relax before sleep.  
Users can select a genre, mood, story length, voice gender, and voice speed to enjoy a bedtime story tailored to their preferences.

---

## 2. Purpose
- To provide a calming experience before sleep
- To generate stories based on user preferences
- To allow users to enjoy stories through both reading and voice playback
- To deliver a simple and soothing interface suitable for bedtime use

---

## 3. Target Users
- People who want to relax before sleep
- People who enjoy personalized short stories
- Users who want bedtime storytelling as part of stress relief or sleep preparation
- Students and other users who want to unwind at night

---

## 4. Functional Requirements

### 4.1 Genre Selection
The user can select a story genre from a dropdown menu.

**Purpose**
- To allow users to choose the type of story they want

**Example Options**
- Heartwarming
- Horror
- Study
- Fantasy
- Others

**Input Method**
- Dropdown menu

**Effect on Output**
- Influences the story setting
- Influences the narrative tone
- Influences the overall theme

---

### 4.2 Mood Selection
The user can choose the emotional atmosphere of the story.

**Purpose**
- To control the tone and feeling of the generated story

**Example Options**
- Cozy
- Calm
- Adventurous
- Fun
- Mysterious

**Input Method**
- Single selection using buttons

**Effect on Output**
- Influences emotional expression
- Influences pacing and atmosphere
- Changes the overall feeling of the story

---

### 4.3 Length Selection
The user can choose the story length using a slider.

**Purpose**
- To adjust the story duration according to user preference and available bedtime time

**Example Options**
- Short (3 min)
- Medium (5 min)
- Long (10 min)

**Input Method**
- Slider

**Effect on Output**
- Influences story length
- Influences reading time
- Influences narration duration

---

### 4.4 Story Generation
The system generates a story based on the selected conditions when the user clicks the create button.

**Purpose**
- To create a personalized bedtime story for the user

**Input**
- Genre
- Mood
- Length

**Output**
- Story title
- Story body

**Trigger**
- Clicking the **Create Story** button

---

### 4.5 Story Display
The generated story is shown in a dedicated display area.

**Purpose**
- To let the user read the generated story clearly and comfortably

**Display Content**
- Story title
- Story body
- Readable paragraph structure

---

### 4.6 Voice Playback
The generated story can be played as narration audio.

**Purpose**
- To allow the user to enjoy the story hands-free and create a more bedtime-friendly experience

**Main Actions**
- Play
- Pause
- Resume
- Stop

**Output**
- Narrated audio version of the generated story

---

### 4.7 Voice Gender Selection
The user can select the gender of the narration voice.

**Purpose**
- To provide a narration voice that matches user preference

**Example Options**
- Male
- Female

**Input Method**
- Dropdown or toggle

**Effect on Output**
- Changes the voice used during narration playback

---

### 4.8 Voice Speed Selection
The user can select the narration speed.

**Purpose**
- To provide a comfortable listening pace for bedtime use

**Example Options**
- Slow
- Normal
- Fast

Or:
- 0.75x
- 1.0x
- 1.25x

**Input Method**
- Dropdown or slider

**Effect on Output**
- Changes narration playback speed

---

### 4.9 Feedback
The user can provide simple feedback on the generated story.

**Purpose**
- To collect user satisfaction data and support future improvements or personalization

**Example Options**
- Like
- Dislike

---

### 4.10 Story Regeneration
The user can generate another story.

**Purpose**
- To allow the user to try a different variation of the story

**Trigger**
- Clicking the **Create Another** button

---

## 5. Screen Requirements

### 5.1 Layout
The screen uses a two-column layout.

#### Left Column: Settings Area
- Genre selection
- Mood selection
- Length selection
- Voice gender selection
- Voice speed selection
- Story generation button

#### Right Column: Story Display Area
- Story title
- Story body
- Voice playback controls
- Feedback buttons
- Regenerate button

---

### 5.2 UI / Design Requirements
- The visual style should feel calm and bedtime-oriented
- The main palette should use deep navy, purple, and soft gold accents
- UI elements should have soft rounded shapes to create comfort
- The layout should provide enough spacing and contrast for long-form reading
- The visuals should communicate warmth, safety, and relaxation

---

## 6. Non-Functional Requirements

### 6.1 Usability
- The interface should be intuitive even for first-time users
- Required settings should be clearly organized
- The process from setting selection to story generation should be simple

### 6.2 Readability
- The story text should use readable font size and line spacing
- Titles and control elements should be easy to identify

### 6.3 Responsiveness
- The system should ideally show a loading state during story generation
- The generated story should appear smoothly after completion
- Voice playback controls should respond clearly to user interaction

### 6.4 Consistency
- The whole experience should remain aligned with the concept of safe, bedtime-friendly use
- The relationship between selected inputs and generated results should be understandable

### 6.5 Accessibility
- Buttons and selectable controls should be large enough to use comfortably
- Text and background should maintain sufficient contrast
- The system should support both reading and listening experiences

### 6.6 Maintainability and Extensibility
- The structure should make it easy to add more genres and voice options later
- The system should support future expansion such as personalization and saved story features

---

## 7. Input / Output Requirements

### 7.1 Input
Items selected by the user:
- Genre
- Mood
- Length
- Voice gender
- Voice speed

### 7.2 Output
Items produced by the system:
- Generated story title
- Generated story body
- Narrated audio playback
- User feedback result, assumed to be stored internally

---

## 8. Possible Future Enhancements (Optional, we could try if we have time)
- Auto-play narration
- Save favorites
- Story history
- Personalization based on user preference
- Background music or ambient sounds
- Child / adult mode
- Multilingual support
- Sleep timer

## 9. UI image
![Bedtime Stories UI](./wireframe/screens/UIImage.png)