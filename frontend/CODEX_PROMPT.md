# Codex prompt for the interoperability UI

You are generating a Create React App (CRA) frontend that talks to a FastAPI backend. Follow these constraints so the UI aligns with the existing backend:

## API base
- All backend routes are mounted under the `/api` prefix.
- Use the same origin as the frontend (CORS is configured) and prepend `/api` to every call.

## Token observability and manual fetch
- Manual token fetch: `POST /api/tokens/manual`
  - Body (application/json): `{ client_id, client_secret, username, password, scope? }`
  - Sends a password-grant request with `user_role=users` automatically; the response is JSON and **does not** wrap data (e.g., `{ "status": "ok", "expires_in": 3600, "scope": "..." }`).
  - Do not display or store the raw access token in the UI.
- Token status: `GET /api/tokens/status`
  - Returns `{ token_present, expires_in, expires_at, scope }` with no `data` wrapper.
- Forced refresh: `POST /api/tokens/refresh`
  - Returns `health()` JSON; surface errors as UI messages (HTTP 502 on failure).
- JWT decode: `GET /api/tokens/jwt`
  - Returns decoded header/claims for observability; never expose `access_token`.

## Patient discovery (PD)
- Search endpoint: `POST /api/pd/search`
  - Body example:
    ```json
    {
      "request_id": "optional-correlator",
      "demographics": {
        "firstName": "Jane",
        "lastName": "Doe",
        "dob": "1990-01-01"
      }
    }
    ```
  - Returns `{ "status": "submitted", "correlation_id": "..." }` if accepted; errors are JSON (HTTP 502/500) when token fetch or downstream submit fails.
  - Always call token status endpoints first or handle 502 errors gracefully.

## Telemetry and timeline
- Telemetry and timeline routers are already mounted under `/api`; reuse existing fetch helpers to render their JSON payloads without assuming axios-style `{ data }` responses.

## Fetch helper expectations
- Use `fetch` or a thin wrapper that resolves to parsed JSON directly. Do **not** destructure `{ data }` like Axios—responses are plain objects.
- Handle HTTP errors by reading the JSON `detail` when present and showing a friendly message.

## UI guidance
- Provide clear loading/error states for token calls and PD search.
- Do not cache secrets client-side; only keep minimal metadata needed for UX (status, expiry, scope, correlation IDs).

Use these rules verbatim when prompting Codex so generated frontend components call the backend correctly.
