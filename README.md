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
