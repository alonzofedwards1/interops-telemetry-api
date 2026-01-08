const express = require('express');
const cors = require('cors');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();

// Basic Express app setup
const app = express();
const port = process.env.PORT || 8000;

app.use(cors());
app.use(express.json({ limit: '1mb' }));

// SQLite setup
const dbPath = process.env.TELEMETRY_DB_PATH || path.join(process.cwd(), 'telemetry.db');
const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('[telemetry] failed to connect to sqlite database', err);
  } else {
    console.log(`[telemetry] connected to sqlite database at ${dbPath}`);
  }
});

db.serialize(() => {
  db.run(
    `CREATE TABLE IF NOT EXISTS telemetry_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      event_id TEXT,
      event_type TEXT,
      timestamp_utc TEXT,
      source_system TEXT,
      source_channel_id TEXT,
      source_environment TEXT,
      organization TEXT,
      qhin TEXT,
      environment TEXT,
      status TEXT,
      duration_ms INTEGER,
      result_count INTEGER,
      correlation_id TEXT,
      correlation_request_id TEXT,
      correlation_message_id TEXT,
      protocol_standard TEXT,
      protocol_interaction_id TEXT,
      raw_payload TEXT NOT NULL,
      received_at TEXT DEFAULT (datetime('now'))
    )`,
    (err) => {
      if (err) {
        console.error('[telemetry] failed to ensure telemetry_events table', err);
      } else {
        console.log('[telemetry] ensured telemetry_events table (auto-created if missing)');
      }
    },
  );
});

const telemetryEvents = [];

function isValidTelemetry(event) {
  if (!event || typeof event !== 'object') return false;
  const { eventId, eventType } = event;
  return typeof eventId === 'string' && eventId.length > 0 && typeof eventType === 'string' && eventType.length > 0;
}

function persistTelemetryEvent(payload) {
  const source = payload?.source || {};
  const correlation = payload?.correlation || {};
  const execution = payload?.execution || {};
  const outcome = payload?.outcome || {};
  const protocol = payload?.protocol || {};

  const eventId = typeof payload.eventId === 'string' ? payload.eventId : null;
  const eventType = typeof payload.eventType === 'string' ? payload.eventType : null;
  const timestampUtc =
    typeof payload.timestamp === 'string'
      ? payload.timestamp
      : typeof payload.timestampUtc === 'string'
        ? payload.timestampUtc
        : null;
  const sourceSystem = typeof source.system === 'string' ? source.system : null;
  const sourceChannelId = typeof source.channelId === 'string' ? source.channelId : null;
  const sourceEnvironment = typeof source.environment === 'string' ? source.environment : null;
  const status = typeof outcome.status === 'string' ? outcome.status : null;
  const durationMs = typeof execution.durationMs === 'number' ? execution.durationMs : null;
  const resultCount = typeof outcome.resultCount === 'number' ? outcome.resultCount : null;
  const correlationRequestId = typeof correlation.requestId === 'string' ? correlation.requestId : null;
  const correlationMessageId = typeof correlation.messageId === 'string' ? correlation.messageId : null;
  const protocolStandard = typeof protocol.standard === 'string' ? protocol.standard : null;
  const protocolInteractionId = typeof protocol.interactionId === 'string' ? protocol.interactionId : null;
  const rawPayload = JSON.stringify(payload ?? {});

  try {
    db.run(
      `INSERT INTO telemetry_events (
        event_id,
        event_type,
        timestamp_utc,
        source_system,
        source_channel_id,
        source_environment,
        status,
        duration_ms,
        result_count,
        correlation_request_id,
        correlation_message_id,
        protocol_standard,
        protocol_interaction_id,
        raw_payload
      ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
      [
        eventId,
        eventType,
        timestampUtc,
        sourceSystem,
        sourceChannelId,
        sourceEnvironment,
        status,
        durationMs,
        resultCount,
        correlationRequestId,
        correlationMessageId,
        protocolStandard,
        protocolInteractionId,
        rawPayload,
      ],
      (err) => {
        if (err) {
          console.error('[telemetry][db] insert failed', err);
        } else {
          console.info('[telemetry][db] event persisted', { eventId });
        }
      },
    );
  } catch (err) {
    console.error('[telemetry][db] insert failed', err);
  }
}

// Telemetry ingestion (non-blocking, always returns 202)
app.post('/api/telemetry/events', (req, res) => {
  try {
    const payload = req.body || {};
    const eventId = typeof payload.eventId === 'string' ? payload.eventId : null;
    const eventType = typeof payload.eventType === 'string' ? payload.eventType : null;
    const status = typeof payload?.outcome?.status === 'string' ? payload.outcome.status : null;

    console.info('[telemetry][ingest] event received', { eventId, eventType, status });

    if (isValidTelemetry(payload)) {
      telemetryEvents.push(payload);
      persistTelemetryEvent(payload);
    } else {
      console.warn('[telemetry][ingest] invalid telemetry payload received', { eventId, eventType });
    }
  } catch (err) {
    console.error('[telemetry][ingest] error handling telemetry payload', err);
  }

  res.sendStatus(202);
});

// Telemetry read endpoint
app.get('/api/telemetry/events', (_req, res) => {
  try {
    console.info('[telemetry][read] returning events', { count: telemetryEvents.length, source: 'memory' });
    res.json(telemetryEvents);
  } catch (err) {
    console.error('[telemetry][read] error reading telemetry store', err);
    res.json([]);
  }
});

// Simple health check
app.get('/health', (_req, res) => {
  res.json({ status: 'ok' });
});

// Fallback error handler to prevent uncaught exceptions from surfacing
app.use((err, _req, res, _next) => {
  console.error('[telemetry] unhandled error', err);
  res.sendStatus(202);
});

process.on('uncaughtException', (err) => {
  console.error('[telemetry] uncaught exception', err);
});

process.on('unhandledRejection', (reason) => {
  console.error('[telemetry] unhandled rejection', reason);
});

app.listen(port, () => {
  console.log(`Telemetry API listening on port ${port}`);
});
