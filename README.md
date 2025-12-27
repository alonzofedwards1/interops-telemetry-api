# InterOps Telemetry API (FastAPI)

Minimal, production-safe telemetry ingestion API for InterOps. Accepts telemetry events over HTTP, validates them with Pydantic, stores them in memory, and exposes them for downstream dashboards. No database, no auth, non-blocking ingestion.

## Requirements
- Python 3.12+
- Docker (optional)

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 9000
```
The service listens on port **9000** by default and exposes Swagger UI at `/docs`.

> Note: The application ignores any ambient `PORT` variable so it remains bound to
> port 9000. To intentionally change the port, set `TELEMETRY_PORT=<port>` before
> running.

## Run with Docker
```bash
docker build -t interops-telemetry-api .
docker run --rm -p 9000:9000 interops-telemetry-api
```
The container listens on port 9000; map the host port as needed.

## Endpoints
- `POST /api/telemetry/events` – accepts telemetry events, validates payloads, logs details, and returns `{ "status": "ok" }`
- `GET /api/telemetry/events` – returns all stored telemetry events as JSON
- `GET /health` – basic health probe

## Telemetry payload shape
```json
{
  "eventId": "string",
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
curl -i -X POST http://localhost:9000/api/telemetry/events \
  -H "Content-Type: application/json" \
  -d '{
    "eventId": "evt-001",
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
curl http://localhost:9000/api/telemetry/events
```

## Notes
- CORS is enabled for all origins by default.
- Telemetry storage is an in-memory array; data clears on restart.
- Ingestion does not block callers. Invalid payloads return HTTP 400 with validation details and are logged with structured context.
- Designed for use with Mirth HTTP Sender after PD responses are built.
