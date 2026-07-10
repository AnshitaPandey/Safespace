# SafeSpace 

An AI emotional-support companion platform: chat with memory (RAG), mood tracking with
forecasting, an AI journal, analytics, goals/streaks, voice, and a safety layer that gates
the LLM entirely on high-risk messages. This is the complete build across the project
roadmap's 12 weeks. See `SafeSpace_Blueprint.md` for the original system design doc this was
built from.

## Honest status before you dig in

Everything below is real, wired-together code — not stubs — and the backend/frontend have
both been verified to import, type-check, and build cleanly (see "What was actually verified"
at the bottom). Two things are worth knowing going in:

1. **The emotion classifier, topic detector, and risk classifier use strong pretrained models
   as a pragmatic default**, not custom models fine-tuned on this app's data — because that
   requires a labeled dataset and a training run this environment can't do for you. The real
   training scripts are included (`backend/ml-service/training/`) and are meant to be run once
   you have data; swapping the checkpoint they produce into `ml-service/models/` is the whole
   upgrade path.
2. **The mood forecaster (GRU) has no trained checkpoint included** — there's no real
   longitudinal mood data to train it on yet. The training script runs against synthetic data
   out of the box (so you can see the full pipeline work and compare GRU/LSTM/Transformer), and
   the backend gracefully falls back to a naive moving-average forecast until a real checkpoint
   exists.

Neither of these is a placeholder pretending to be finished — they're the correct, honest state
of "the DL parts of an ML product before you have production data," which is itself a real
thing worth being able to talk about in an interview.

## Architecture at a glance

```
Frontend (React/Vite/Tailwind) ──HTTP/WS──> Backend (FastAPI)
                                                  │
                          ┌───────────────────────┼────────────────────────┐
                          │                        │                        │
                     Postgres                   Redis                  Qdrant (vectors)
                  (source of truth)     (short-term memory,          (long-term memory
                                          Celery broker)                embeddings)
                          │
                    Celery workers (memory extraction, journal summarization,
                    analytics rollups, message tagging, quality scoring)
                          │
                     ml-service (FastAPI, separate container)
                  emotion / sentiment / topic / risk / mood-forecast models
```

## What's implemented, by roadmap week

**Week 1 — Foundations**: JWT + Google OAuth auth, Postgres schema, React shell.

**Week 2 — Core chat**: chat/message persistence, WebSocket real-time loop, first LLM
integration (Anthropic), keyword-based safety gate (hard stop before the LLM on high risk).

**Week 3 — Memory + Mood + Journal**: Qdrant-backed RAG memory with hybrid ranking
(similarity + importance + recency — see `app/ai/memory_retrieval.py`), async memory
extraction via Celery, mood log CRUD + weekly/monthly trend charts, journal CRUD with
async LLM-generated summaries/themes/reflection questions.

**Week 4 — Personalities + Analytics + polish**: five personality prompt templates
(implemented since Week 2), AI-generated weekly/monthly narrative reports
(`app/workers/analytics_rollup.py`), emotional-pattern breakdown.

**Weeks 5-6 — DL: emotion, sentiment, topic**: `ml-service`, a separate FastAPI
microservice serving all three, called async via Celery after each message
(`app/workers/message_tagging.py`) so DL inference never blocks the chat response.

**Weeks 7-8 — Memory + Safety v2**: hybrid memory ranking (done in Week 3, matches this
week's spec), async Celery-based extraction (not request-blocking), and a second safety
layer — a learned risk classifier served by ml-service, combined with the keyword gate by
taking the higher risk level (`app/ai/safety_layer.py::check_message_safety_combined`). The
keyword gate remains the deterministic backstop regardless of what the classifier says.

**Weeks 9-10 — Mood forecasting, quality scoring, voice**: GRU mood forecaster (architecture
+ training/comparison script — see honesty note above on the missing trained checkpoint),
LLM-as-judge conversation quality scoring (`app/workers/quality_scoring.py`), voice STT/TTS
via a provider-agnostic adapter (OpenAI Whisper/TTS by default).

**Weeks 11-12 — Advanced features + hardening**: goals, streaks (mood-log/journal
activity), in-app notifications, GitHub Actions CI/CD (lint, test, build, image push),
production Nginx config, a real pytest suite (7 tests, all passing).

## Running it locally

```bash
cp backend/.env.example backend/.env
# fill in at minimum: JWT_SECRET_KEY, ANTHROPIC_API_KEY
# optional: OPENAI_API_KEY (voice), GOOGLE_CLIENT_ID/SECRET (Google login)

docker compose up --build
```

This brings up: Postgres, Redis, Qdrant, the backend API, a Celery worker, Celery Beat
(scheduled weekly reports), `ml-service`, and the frontend dev server.

- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs
- ml-service health check: http://localhost:8100/health

**First boot will be slow** — `ml-service` downloads a few hundred MB of pretrained
Hugging Face models on first start (emotion/sentiment/topic/risk models). Subsequent
starts are fast since they're cached in the `ml-service` container's layer/volume.

## Training the real models (optional, once you have data)

```bash
cd backend/ml-service/training

# Emotion classifier — needs the GoEmotions dataset (auto-downloaded via `datasets`)
pip install datasets scikit-learn
python train_emotion_classifier.py --epochs 4 --output_dir ./emotion_model
# then point ml-service/models/emotion_classifier.py at ./emotion_model

# Mood forecaster — runs against synthetic data by default; swap to real Postgres data
# once you have 60+ days of history across a meaningful number of users
python train_mood_forecaster.py --data_source synthetic --epochs 30
# copy the resulting mood_forecaster_gru.pt into ml-service/checkpoints/
```

## Project layout

```
safespace/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/            # config, JWT/bcrypt, redis client
│   │   ├── db/               # async session (FastAPI) + sync session (Celery)
│   │   ├── models/            # 13 SQLAlchemy models
│   │   ├── schemas/            # Pydantic request/response models
│   │   ├── api/v1/              # auth, chat, memory, mood, journal, analytics,
│   │   │                          personality, goals, notifications, voice
│   │   ├── ai/                   # safety_layer, prompt_builder, memory_retrieval,
│   │   │                          llm_adapter, voice_adapter, vector_store, embeddings,
│   │   │                          short_term_memory, streaks, orchestrator
│   │   ├── ws/chat_socket.py       # WebSocket chat handler
│   │   └── workers/                 # Celery: memory_extraction, journal_summarization,
│   │                                   analytics_rollup, message_tagging, quality_scoring
│   ├── ml-service/                    # separate FastAPI microservice
│   │   ├── main.py
│   │   ├── models/                      # emotion, sentiment, topic, risk, mood_forecaster
│   │   └── training/                      # train_emotion_classifier.py, train_mood_forecaster.py
│   ├── migrations/                          # Alembic, 3 migrations
│   └── tests/                                 # pytest — 7 tests, all passing
├── frontend/src/
│   ├── pages/                    # Landing, Login, Register, AppLayout, ChatPage, MoodPage,
│   │                                JournalPage, AnalyticsPage, SettingsPage
│   ├── hooks/useChatSocket.ts
│   ├── lib/                       # api.ts, chatApi.ts, moodApi.ts, journalApi.ts,
│   │                                 analyticsApi.ts, settingsApi.ts
│   └── components/                  # MessageBubble, PersonalitySelector
├── nginx/nginx.conf                    # production reverse proxy config
├── .github/workflows/ci-cd.yml           # lint/test/build/push pipeline
└── docker-compose.yml                      # all 8 services
```

## What was actually verified in this environment

- Backend: full `ast.parse` syntax check across every `.py` file, then `from app.main import
  app` actually imports successfully with every Week 1-12 module wired in (auth, chat, RAG
  memory, mood, journal, analytics, goals, notifications, voice, Celery tasks all loading
  without error). All 7 Celery tasks confirmed registered. `pytest` run: 7/7 passing.
- Frontend: `npx tsc -b` — zero type errors across the full app. `npx vite build` — succeeds,
  146KB main bundle after chunk-splitting recharts out.
- Docker Compose and GitHub Actions YAML: both parsed and validated with `yaml.safe_load`.
- **Not verified**: an actual `docker compose up` end-to-end run (no Docker daemon in this
  sandbox), a live LLM round-trip (no real Anthropic API key available here), and the
  ml-service models actually downloading/running (torch/transformers were installed and the
  code syntax-checked, but the models weren't downloaded and run in this session — that
  happens on first `docker compose up`). Run these yourself first, and if anything's off,
  come back and I'll fix it.

## A few design decisions worth knowing about before you extend this

- **The safety layer is a hard gate, not a prompt instruction.** High-risk messages never
  reach the LLM for that turn, full stop. The Week 7-8 classifier only ever *adds* risk
  sensitivity on top of the keyword gate — it can escalate a risk level, never de-escalate one
  the keyword matcher already caught.
- **Celery tasks use a separate sync DB session**, not the async one FastAPI uses — mixing
  asyncpg into worker processes outside the event loop is more trouble than it's worth here.
- **Personalities are prompt templates, not database rows.** A `personality_profiles` table
  from the original blueprint was deliberately skipped — it would only earn its place once
  personalities need per-user customization beyond picking one of five presets.
- **ml-service is a separate container/deploy unit from the main API** on purpose — DL
  inference is compute-bound and benefits from independent scaling/GPU placement; chat traffic
  is bursty and I/O-bound. Keeping them separate is what makes that tradeoff possible later.
