# Atlas — AI Emergency Operations Copilot

Dispatch centers do not fail from a lack of information. They fail when too many reports arrive at once. Atlas uses ASU AIR to process emergency streams in parallel, turn unstructured 911 audio/text into structured incidents, collapse duplicate reports, and continuously recommend how limited units should move as the scene changes.

This repo is a hackathon demo for the Tempe / Phoenix area. It uses **synthetic 911-style data only**. Do not point it at real private live calls unless you have explicit authorized access.

## What it does

Atlas ingests streams such as:

- 911 call transcripts
- caller location
- incident type
- unit availability
- hospital capacity
- traffic / road closures
- weather
- prior nearby incidents

Then it classifies, prioritizes, clusters, and re-plans.

Example: 200 calls arrive across Phoenix. Instead of a dispatcher reading them one by one, Atlas processes them concurrently and produces a live incident map.

```
“There's smoke coming from an apartment.”
“My dad collapsed and isn't responding.”
“Three-car crash on Rural and Broadway.”
“Someone is yelling outside but I don't see a weapon.”
```

becomes structured incidents such as:

- **Incident #183**
- Type: Medical
- Severity: P1
- Signals: unconscious person, possible cardiac arrest
- Recommended response: nearest ALS ambulance
- Human dispatcher still approves the assignment

## Where AIR matters

1. **Concurrent call processing**  
   Qwen ASR (when configured) plus AIR LLM workers extract emergency type, severity, address, injuries, hazards, and people count from many transcripts at once.

2. **Duplicate detection**  
   During a major event, 500 callers can be describing 127 unique emergencies. Atlas embeds each report and clusters by geographic proximity, time proximity, and semantic similarity.

3. **Severity as decision support**  
   P1 immediate threat to life, P2 urgent, P3 moderate, P4 non-emergency. Atlas recommends. A dispatcher approves. It does not autonomously make final life-or-death dispatch decisions.

4. **Resource allocation**  
   15 ambulances, 8 fire trucks, 20 police units, and a surge of active incidents. Atlas scores severity, travel time, required equipment, nearby units, and hospital capacity.

5. **Continuous re-optimization**  
   Observe → analyze → plan → recommend → new information → re-plan. A new cardiac arrest, a highway closure, or a hospital hitting capacity triggers a fresh recommendation.

6. **Demand prediction**  
   Historical synthetic volume plus time-of-day patterns (Friday night on Mill Ave, evening commute on Rural / Broadway) recommend where to pre-position units.

```
911 / traffic / weather
        ↓
   AIR ASR + agents
        ↓
Call Understanding · Severity · Clustering
Resource Allocation · Routing · Prediction
        ↓
  Optimization engine
        ↓
 Live map + recommended responders
```

## Demo flow

The safest judge path is **Guided demo** in the console. It walks through a deterministic
scenario, recommendation evidence, human approval, a new P1 incident, live re-planning, the
operations timeline, and the after-action report.

Manual controls are also available:

1. Choose **ASU game night**, **Monsoon response**, or **Weekday commute**.
2. Click **Start scenario**. The same scenario replays the same validated synthetic inputs each time.
3. Open an incident and review the recommended unit, ETA, decision factors, policy, and alternatives.
4. Click **Approve & dispatch** for the human-in-the-loop step.
5. Click **Inject P1** to introduce a major collision and compare the previous plan with the re-route.
6. Open **Timeline** for the decision log, then **Report** for the after-action summary and JSON export.

Synthetic scenarios use repeatable, locally validated analysis so a model or VPN interruption cannot
derail the presentation. For non-scenario inputs, configured ASU AIR models remain the primary
analysis path with local fallback.

## Stack

| Layer | Choice |
| --- | --- |
| Frontend | React + Vite + Leaflet |
| Backend | Python / FastAPI, using the Python libraries in `backend/requirements.txt` |
| Database | SQLite via SQLAlchemy |
| Models | Local heuristics by default; ASU AIR when env keys are set |

## Project layout

```
atlas-demo/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── agents/
│   │   ├── models/
│   │   ├── database/
│   │   ├── simulator/
│   │   └── schemas/
│   ├── main.py
│   ├── requirements.txt
│   └── .env
├── frontend/
└── README.md
```

## Run with Docker

The fastest path, and the one to hand to anyone else. Requires only Docker Desktop.

```bash
docker compose up --build
```

Then open **[http://localhost:8080](http://localhost:8080)**. The frontend is built by Vite and
served by nginx, which proxies `/api` and `/ws` to the FastAPI container. SQLite lives in a named
volume so incidents survive a restart.

No API keys are required — Atlas falls back to local classifiers and free map tiles. To use the
real models, copy `.env.example` to `.env`, fill in the AIR and MapTiler values, and rebuild.
`WEB_PORT` and `BACKEND_PORT` in that same file move the published ports if 8080 or 8000 are
already taken.

```bash
docker compose down     # stop
docker compose down -v  # stop and wipe the database volume
```

See [QUICKSTART.md](QUICKSTART.md) for the demo script.

## Install for local development

You need Python 3.11+ and Node 18+.

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Fill in `backend/.env`. Variable names are already there; add values only where you have them.

| Variable | Purpose |
| --- | --- |
| `APP_NAME` | Service name |
| `APP_ENV` | `development` or `production` |
| `APP_HOST` | Bind host |
| `APP_PORT` | Bind port |
| `CORS_ORIGINS` | Comma-separated frontend origins |
| `DATABASE_URL` | SQLite path, default `sqlite:///./atlas.db` |
| `AIR_API_KEY` | ASU AIR key |
| `AIR_API_BASE_URL` | ASU AIR base URL |
| `AIR_LLM_MODEL` | Reasoning model name |
| `AIR_EMBEDDING_MODEL` | Embedding model name |
| `AIR_ASR_MODEL` | Qwen ASR model name |
| `SIMULATION_CALL_COUNT` | Calls per simulation |
| `SIMULATION_BATCH_SIZE` | Calls processed together |
| `SIMULATION_DELAY_SECONDS` | Pause between batches |
| `SIMULATION_ON_SCENE_TICKS` | Ticks a dispatched unit remains on scene before release |

AIR keys can stay empty. Atlas then uses local classifiers, hashed embeddings, and the synthetic transcripts already in the simulator.

Start the API from `backend/`:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend

```bash
cd frontend
npm install
```

Fill in `frontend/.env` if the defaults are wrong:

| Variable | Purpose |
| --- | --- |
| `VITE_API_URL` | Backend origin, default `http://localhost:8000` |
| `VITE_WS_URL` | WebSocket origin, default `ws://localhost:8000` |

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

- `/` — landing page for judges (pitch, problem, six capabilities)
- `/how-it-works` — AIR architecture and stack
- `/console` — live operations demo

## 20-second pitch

During emergencies, dispatch centers do not suffer from a lack of information — they suffer from too much information arriving too quickly. Atlas uses ASU AIR to process thousands of emergency reports in parallel, transcribe and understand calls, detect duplicate reports, identify critical incidents, and continuously recommend how limited emergency resources should be allocated as conditions change.

Instead of helping dispatchers handle one call, Atlas helps them understand the entire emergency landscape.
