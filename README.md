# InterOps Telemetry API

Minimal, production-safe telemetry ingestion API for InterOps built with FastAPI. It accepts telemetry events over HTTP, stores them in SQLite for quick inspection, and never blocks callers on downstream work.

## Requirements
- Python 3.12+
- Docker (optional)

## Backend layout and imports
Open the repository root as your working directory—the `app/` package lives directly under it:

```
interops-telemetry-api/
├── app/
│   ├── api/
│   ├── auth/
│   ├── pd/
│   ├── telemetry/
│   └── timeline/
├── frontend/
└── requirements.txt
```

If you open or run code from the nested `app/` directory itself, Python will not see the repository root on `sys.path`, and imports like `from app.auth.openemr_auth import OpenEMRAuthManager` will fail. Running commands from the repository root keeps `app` resolvable without manual `PYTHONPATH` edits. From the root you can start the API with:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 9000
```

PyCharm users can right-click the repository root and choose **Mark Directory as → Sources Root** to make sure editor autocomplete resolves `app.*` imports consistently.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 9000
```
The service listens on port **8000** by default. Override with `PORT=<port>` if needed. Telemetry events persist to a local SQLite file at `./telemetry.db` (override with `TELEMETRY_DB_PATH=<path>`).

Starting the service automatically creates `telemetry.db` and the `telemetry_events` table if they do not already exist—no manual migration step is required.

## Run with Docker
```bash
docker build -t interops-telemetry-api .
docker run --rm -p 8000:8000 interops-telemetry-api
```

## Endpoints
- `POST /api/tokens/manual` – fetch an OpenEMR access token via password grant (never returns the token itself)
- `GET /api/tokens/status` – report whether a token is cached along with expiry metadata
- `POST /api/tokens/refresh` – force a refresh using the configured OpenEMR credentials
- `POST /api/pd/search` – submit a patient-discovery request to the configured Mirth endpoint
- `POST /api/telemetry/events` – accepts telemetry events and returns HTTP 202 immediately (non-blocking)
- `GET /api/telemetry/events` – returns all stored telemetry events as JSON from SQLite
- `GET /health` – basic health probe

If any of the `/api/tokens/*` or `/api/pd/search` routes return 404, your FastAPI app was started from the wrong working
directory or without importing `app.main`. Start from the repository root (where `requirements.txt` lives) and visit
`http://localhost:8000/docs` to confirm the routes are mounted.

## Telemetry payload shape
```json
{
  "eventId": "string",
  "eventType": "string",
  "timestampUtc": "2024-01-01T12:00:00Z",
  "source": "MIRTH",
  "protocol": "HL7v3",
  "interactionId": "PRPA_IN201306UV02",
  "organization": "VA",
  "qhin": "CommonWell",
  "environment": "TEST",
  "status": "SUCCESS",
  "durationMs": 42,
  "resultCount": 1,
  "correlationId": "REQ-123"
}
```

## Example curl commands
Post telemetry (mirrors Mirth HTTP Sender):
```bash
curl -i -X POST http://localhost:8000/api/telemetry/events \
  -H "Content-Type: application/json" \
  -d '{
    "eventId": "evt-001",
    "eventType": "PD_EXECUTION",
    "timestampUtc": "2025-12-26T22:15:00Z",
    "source": "MIRTH",
    "protocol": "HL7v3",
    "interactionId": "PRPA_IN201306UV02",
    "organization": "VA",
    "qhin": "CommonWell",
    "environment": "TEST",
    "status": "SUCCESS",
    "durationMs": 187,
    "resultCount": 1,
    "correlationId": "REQ-123"
  }'
```

Read stored telemetry:
```bash
curl http://localhost:8000/api/telemetry/events
```

## PD executions (materialized)
The API derives PD execution rows from telemetry events with `eventType = "pd.request.completed"`.
These rows are stored in `pd_executions` for dashboard rollups.

List PD executions:
```bash
curl http://localhost:8000/api/pd-executions
```

Summarize PD executions:
```bash
curl http://localhost:8000/api/pd-executions/summary
```

Materialize from telemetry:
```bash
curl -X POST http://localhost:8000/api/pd-executions/materialize
```

If you see an empty array when reading:

- Post your events to the **same host/port** you are reading from (for example, `curl` and browser both pointed at `http://localhost:8000`).
- The SQLite file defaults to `./telemetry.db`. If you override `TELEMETRY_DB_PATH`, ensure the Node process can read/write that location.
- Check the server logs for lines like `[telemetry] returning <n> event(s)` to confirm the backend received your payloads.

## Frontend configuration
If you are viewing the telemetry table in the frontend, ensure it is pointed at the backend you are posting to. The UI defaults to `http://100.27.251.103:8000/api`; when you post events to `localhost`, set `REACT_APP_API_BASE_URL=http://localhost:8000/api`, restart the frontend, and refresh the page so it fetches from your local service.

## Notes
- CORS is enabled for all origins by default.
- Telemetry storage is persisted in SQLite for quick, file-backed testing.
- Ingestion does not block callers; even invalid payloads receive HTTP 202 to avoid retries.
- See `TELEMETRY_DB.md` for the schema and EC2 setup steps.
