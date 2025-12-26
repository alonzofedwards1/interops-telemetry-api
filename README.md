# InterOps Telemetry API (Node.js)

Minimal, production-safe telemetry ingestion API for InterOps. Accepts telemetry events over HTTP, stores them in memory, and exposes them for downstream dashboards. No database, no auth, non-blocking ingestion.

## Requirements
- Node.js 20+
- Docker (optional)

## Run locally
```bash
npm install
npm start
```
The service listens on port **8080** by default.

## Run with Docker
```bash
docker build -t interops-telemetry-api .
docker run --rm -p 8081:8080 interops-telemetry-api
```
The container listens on port 8080; map host port 8081 (or any other) as needed.

## Endpoints
- `POST /api/telemetry/events` – accepts telemetry events, logs the event ID when valid, always returns `202 Accepted`
- `GET /api/telemetry/events` – returns all stored telemetry events as JSON
- `GET /health` – basic health probe

## Telemetry payload shape
```json
{
  "eventId": "string",
  "eventType": "PD_EXECUTION",
  "timestamp": "ISO-8601 string",
  "source": {
    "system": "MIRTH | MANUAL | APP",
    "channelId": "string",
    "environment": "TEST | DEV | PROD"
  },
  "correlation": {
    "requestId": "string",
    "messageId": "string"
  },
  "execution": { "durationMs": 42 },
  "outcome": { "status": "SUCCESS | FAILURE", "resultCount": 1 },
  "protocol": { "standard": "HL7v3 | FHIR | X12", "interactionId": "string" }
}
```

Validation is minimal: `eventId` and `eventType` must be non-empty strings. Invalid payloads still return `202 Accepted` but emit a warning log.

## Example curl commands
Post telemetry (mirrors Mirth HTTP Sender):
```bash
curl -X POST http://localhost:8080/api/telemetry/events \
  -H "Content-Type: application/json" \
  -d '{
    "eventId": "123",
    "eventType": "PD_EXECUTION",
    "timestamp": "2024-01-01T12:00:00Z",
    "source": {"system": "MIRTH", "channelId": "channel-1", "environment": "TEST"},
    "correlation": {"requestId": "req-1", "messageId": "msg-1"},
    "execution": {"durationMs": 42},
    "outcome": {"status": "SUCCESS", "resultCount": 1},
    "protocol": {"standard": "HL7v3", "interactionId": "PRPA_IN201306UV02"}
  }'
```

Read stored telemetry:
```bash
curl http://localhost:8080/api/telemetry/events
```

## Notes
- CORS is enabled for all origins by default.
- Telemetry storage is an in-memory array; data clears on restart.
- Ingestion never blocks callers. Payload errors are logged but still return 202.
- Designed for use with Mirth HTTP Sender after PD responses are built.
