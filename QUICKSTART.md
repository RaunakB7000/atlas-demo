# Atlas — run it in one command

**Atlas is an AI emergency operations copilot.** It processes a surge of synthetic 911 calls in
parallel, collapses duplicate reports into unique incidents, and continuously recommends how
limited ambulances, engines, and police units should move. A human dispatcher always approves.

You only need [Docker Desktop](https://www.docker.com/products/docker-desktop/).

## 1. Start

From this folder:

```bash
docker compose up --build
```

First build takes a couple of minutes. When you see `atlas-backend` and `atlas-frontend` running,
open:

**[http://localhost:8080](http://localhost:8080)**

## 2. Walk the demo

1. Landing page explains the product. Click **Launch live console**.
2. Click **Guided demo**, then follow the four on-screen steps.
3. Start the selected deterministic scenario and point out that *incoming reports* climbs faster
   than *unique incidents* — that gap is duplicate detection working.
4. Review the selected incident's ETA, capability match, severity, alternatives, and policy before
   approving the recommendation.
5. Approve the lower-priority dispatch and inject the P1 collision. Use the animated **Before /
   Re-route / Recommended now** card to explain why the operational plan changed.
6. Open **Timeline** to show the auditable decision sequence, then open **Report** for the metrics,
   debrief notes, and downloadable JSON.

If presenting manually, choose a scenario, use **Start scenario**, select an incident, approve it,
then use **Inject P1**, **Timeline**, and **Report** in that order.

Pages: `/` landing · `/how-it-works` architecture · `/console` live demo

API docs: [http://localhost:8080/docs](http://localhost:8080/docs)

## 3. Stop

```bash
docker compose down
```

Add `-v` to also wipe the SQLite volume.

## Optional keys

Everything above works with **no API keys**. Atlas falls back to local classifiers, local
embeddings, and free map tiles.

To use the real models, copy `.env.example` to `.env` and fill in what you have:

| Variable | Effect |
| --- | --- |
| `AIR_API_KEY`, `AIR_API_BASE_URL` | Enables ASU AIR calls |
| `AIR_LLM_MODEL` | Call understanding + severity reasoning |
| `AIR_EMBEDDING_MODEL` | Embedding-based duplicate clustering |
| `AIR_ASR_MODEL` | Speech-to-text on call audio |
| `VITE_MAPTILER_KEY` | MapTiler dark basemap instead of free tiles |

Then rebuild:

```bash
docker compose up --build
```

## Notes

- Synthetic data only. No real 911 audio or private call data is used.
- Atlas recommends; it never autonomously makes a final dispatch decision.
- Ports: `8080` web, `8000` API. If either is taken, set `WEB_PORT` and
  `BACKEND_PORT` in `.env` and run `docker compose up --build` again.
