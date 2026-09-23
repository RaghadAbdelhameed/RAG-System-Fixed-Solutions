# KnowledgeHub — Multi-Organization RAG Chatbot Platform

A from-scratch rebuild of the same concept as the reference project you shared:
multiple organizations, each with an isolated knowledge base, a role-based
admin hierarchy (Super Admin → Org Admin → Member), document upload with
automatic embedding, Arabic/cross-lingual RAG answers, feedback + stats,
persisted chat history, and voice input.

**What's different from the reference project** (so this isn't a copy):
- Backend is modularized into routers/services instead of one large `main.py`
- Auth uses **JWT bearer tokens** instead of passing `user_id` around
- Different embedding model (`paraphrase-multilingual-mpnet-base-v2`) and a
  configurable relevance-threshold fallback instead of a fixed rule
- Uses **Gemini** directly via the SDK (no LangChain wrapper)
- Different DB table/column names and project structure
- Different UI: teal/amber flat design instead of the purple glass gradient,
  different page layout and component structure

**What's the same on purpose** (because you asked for the same behavior):
org data isolation, RBAC, temp-password email flow forcing a password change,
multi-format document upload (PDF/DOCX/TXT/CSV), pgvector similarity search,
cross-lingual retrieval, fallback message when nothing relevant is found,
persistent chat history, 1–5 star feedback with admin review + stats, and
voice-to-text questions.

---

## 0. Project layout

```
knowledgehub_rag/
├── backend/
│   ├── app/
│   │   ├── config.py          settings from .env
│   │   ├── database.py        SQLAlchemy engine/session
│   │   ├── models.py          Organization, Account, KnowledgeFile,
│   │   │                      KnowledgeChunk, Conversation, ConversationTurn, Rating
│   │   ├── schemas.py         Pydantic request/response models
│   │   ├── security.py        bcrypt hashing + JWT
│   │   ├── deps.py            auth dependency / role guard
│   │   ├── mailer.py          temp-password emails (console fallback)
│   │   ├── ingestion.py       file parsing, chunking, embeddings
│   │   ├── rag_engine.py      pgvector retrieval + Gemini generation
│   │   ├── speech.py          faster-whisper transcription
│   │   ├── main.py            FastAPI app + router wiring
│   │   └── routers/
│   │       ├── auth_routes.py         login, change-password
│   │       ├── superadmin_routes.py   orgs, org admins
│   │       ├── admin_routes.py        members, document upload/list/delete
│   │       ├── chat_routes.py         ask, history, speech-to-text
│   │       └── feedback_routes.py     ratings, stats
│   ├── requirements.txt
│   ├── .env.example
│   └── seed_super_admin.py    creates the first Super Admin
├── frontend/                  plain HTML/CSS/JS, no build step
│   ├── login.html / change_password.html / chat.html
│   ├── admin_documents.html / admin_users.html / admin_feedback.html
│   ├── superadmin.html
│   ├── css/theme.css
│   └── js/{api,login,chat,admin}.js
├── sample_docs/                a test Arabic document
└── README.md                   this file
```

---

## 1. Install PostgreSQL + pgvector

You need a PostgreSQL server (14+) with the `pgvector` extension available.

```bash
# macOS (Homebrew)
brew install postgresql pgvector

# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
# then build/install pgvector: https://github.com/pgvector/pgvector#installation
```

Create the database and enable the extension:

```bash
psql -U postgres
CREATE DATABASE knowledgehub;
CREATE USER kb_user WITH PASSWORD 'kb_pass';
GRANT ALL PRIVILEGES ON DATABASE knowledgehub TO kb_user;
\c knowledgehub
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

---

## 2. Python environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:
- `DATABASE_URL` — match the user/password/db you created in step 1
- `GEMINI_API_KEY` — get one free at https://aistudio.google.com/app/apikey
- `JWT_SECRET` — any long random string
- Leave `SMTP_*` blank while testing — temp-password emails will just print
  to your terminal instead of actually sending

---

## 4. Create the first Super Admin

```bash
python seed_super_admin.py
```
Follow the prompts (name, email, password). This account can create
organizations and organization admins.

---

## 5. Run the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000`, and it also serves the frontend
at `http://localhost:8000/frontend/login.html` (tables/DB are auto-created
on first run).

---

## 6. Walk through the platform

1. Open `http://localhost:8000/frontend/login.html` and log in as the
   super admin you just created.
2. Create an **Organization** (e.g. "قسم خدمة العملاء").
3. Create an **Org Admin** for it — a temp password prints in the terminal
   running uvicorn (since SMTP isn't configured). Log out, log in as that
   admin using the printed password, and you'll be forced to set a real one.
4. As the org admin, go to **Documents** and upload `sample_docs/customer_data_update_guide.txt`
   (or your own PDFs/DOCX/CSV).
5. Go to **Users** and create a Member account the same way (temp password
   prints to terminal again).
6. Log in as that member and open **Chat** — ask, in Arabic:
   `ما هي خطوات تحديث بيانات العميل؟`
   You'll get an answer grounded only in that organization's documents,
   plus the source filename(s) and a 👍/👎 to rate it.
7. Back in the org admin's **Feedback** page, you'll see that rating and
   the running average.

---

## 7. Notes on scaling / production

- Swap the mocked email for real SMTP credentials in `.env` when ready.
- `RELEVANCE_THRESHOLD` in `.env` controls how strict the fallback is —
  lower it if the bot says "not enough information" too often; raise it
  if it's answering things it shouldn't.
- The embedding model downloads once (~450MB) the first time you upload a
  document or ask a question — this can take a minute or two on first run.
- Voice input requires the browser tab to be served over `localhost` or
  HTTPS (browser microphone permission requirement) — `localhost` is fine
  for local testing.
