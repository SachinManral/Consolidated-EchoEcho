# Echo Echo

A songwriting inspiration tool that generates short instrumental sketches, writes matching lyrics, and checks copyright safety — all from a mood, genre, and theme.

📖 **[Full Documentation →](https://consolidated-echoecho.onrender.com/docs)**

## What It Does

- **Generate music** via the Kie.AI API (30-second instrumental sketches powered by Suno)
- **Write lyrics** using a CrewAI + Groq agent (Llama 3.1) tuned to the mood and style
- **Check copyright** with an AI agent that flags similarity to known songs
- **Song library** — browse, replay, download, and trim your generated tracks
- **Auth** — invite-only sign-up with email/password login

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Uvicorn |
| Music generation | Kie.AI API (Suno v4) |
| Lyrics & copyright | CrewAI + Groq (Llama 3.1) |
| Frontend | Vanilla HTML/CSS/JS |
| 3D background | Three.js |

## Project Structure

```
├── backend/
│   ├── main.py                  # FastAPI app, all routes
│   ├── api_generator.py         # Kie.AI music generation + polling
│   ├── music_generator.py       # Local MusicGen (optional, heavy)
│   ├── composer.py              # Prompt builder
│   ├── auth.py                  # Login / signup
│   ├── transcriber.py           # Audio transcription
│   └── agents/
│       ├── lyrics_agent.py      # CrewAI lyrics writer
│       └── copyright_agent/     # Copyright risk checker
├── frontend/
│   ├── index.html               # Landing page
│   ├── login.html               # Auth
│   ├── dashboard.html           # Main generator UI
│   ├── generate.html            # Generation flow
│   ├── output.html              # Song result + download
│   └── echo.html                # Song library
├── render.yaml                  # Render deployment config
├── requirements-deploy.txt      # Lean deps for cloud deploy
└── requirements.txt             # Full local deps
```

## Local Setup

**Prerequisites:** Python 3.12+

```bash
# Clone and enter the project
git clone https://github.com/simplysandeepp/Consolidated-EchoEcho.git
cd Consolidated-EchoEcho

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env   # or create manually (see Environment Variables below)

# Run the server
uvicorn backend.main:app --reload --port 8000
```

Open `http://localhost:8000` in your browser.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Groq API key for lyrics and copyright agents |
| `KIE_API_KEY` | Yes | Kie.AI key for music generation |
| `KIE_CALLBACK_URL` | Yes | Public URL Kie.AI will call back (e.g. your Render URL + `/api/kieai/callback`) |
| `ECHO_SIGNUPS_OPEN` | No | Set to `1` to open public sign-ups (default: invite-only) |

Get keys:
- Groq: **console.groq.com**
- Kie.AI: **kie.ai**

## Deploy to Render

The repo includes a `render.yaml` for one-click deploy.

1. Push this repo to GitHub
2. Go to **render.com** → New → Web Service → Connect GitHub repo
3. Render auto-detects the config — just add your environment variables in the dashboard
4. Click **Deploy**

Build command: `pip install -r requirements-deploy.txt`  
Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

> **Note:** The free Render tier has an ephemeral filesystem — generated audio files are lost on redeploy. For persistence, attach a Render Disk or use external storage.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/generate` | Generate a song (API mode) |
| `POST` | `/api/compose` | Build a song prompt |
| `POST` | `/api/copyright/check` | Check lyrics for copyright risk |
| `POST` | `/api/auth/login` | Login |
| `POST` | `/api/auth/signup` | Sign up (requires `ECHO_SIGNUPS_OPEN=1`) |
| `GET` | `/history` | All generated songs |
| `GET` | `/song/{id}` | Single song record |
| `GET` | `/download/{id}/original` | Download original audio |
| `GET` | `/download/{id}/trimmed` | Download trimmed audio |
| `POST` | `/api/library/{id}/trim` | Trim a song to 30s |
| `GET` | `/generation-status` | Live generation progress |
| `GET` | `/health` | Service health check |

## Documentation

Full documentation is available at **[consolidated-echoecho.onrender.com/docs](https://consolidated-echoecho.onrender.com/docs)**

| Section | URL |
|---|---|
| Overview | `/docs` |
| How It Works | `/docs/how-it-works` |
| Tech Stack | `/docs/tech-stack` |
| Getting Started | `/docs/getting-started` |
| Environment Variables | `/docs/environment` |
| Generate Music API | `/docs/api/generate` |
| Compose Prompt API | `/docs/api/compose` |
| Lyrics & Copyright API | `/docs/api/lyrics` |
| Authentication API | `/docs/api/auth` |
| Library API | `/docs/api/library` |
| Download & Trim API | `/docs/api/download` |
| Health & Status API | `/docs/api/health` |
| Render Deployment | `/docs/deployment` |
| Troubleshooting | `/docs/troubleshooting` |

## License

MIT
