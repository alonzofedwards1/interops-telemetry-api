const express = require('express');
const cors = require('cors');

// Basic Express app setup
const app = express();
const port = process.env.PORT || 8081;

app.use(cors());
app.use(express.json({ limit: '1mb' }));

// In-memory telemetry store (process lifetime only)
const telemetryStore = (() => {
  const events = [];
  return {
    add(event) {
      events.push(event);
    },
    all() {
      return [...events];
    },
  };
})();

function isValidTelemetry(event) {
  if (!event || typeof event !== 'object') return false;
  const { eventId, eventType } = event;
  return typeof eventId === 'string' && eventId.length > 0 && typeof eventType === 'string' && eventType.length > 0;
}

// Telemetry ingestion (non-blocking, always returns 202)
app.post('/api/telemetry/events', (req, res) => {
  try {
    const payload = req.body || {};
    const eventId = typeof payload.eventId === 'string' ? payload.eventId : 'unknown-id';

    if (isValidTelemetry(payload)) {
      telemetryStore.add(payload);
      console.log(`[telemetry] received event ${eventId}`);
    } else {
      console.warn(`[telemetry] invalid telemetry payload received (eventId=${eventId})`);
    }
  } catch (err) {
    console.error('[telemetry] error handling telemetry payload', err);
  }

  res.sendStatus(202);
});

// Telemetry read endpoint
app.get('/api/telemetry/events', (_req, res) => {
  try {
    const events = telemetryStore.all();
    console.log(`[telemetry] returning ${events.length} event(s)`);
    res.json(events);
  } catch (err) {
    console.error('[telemetry] error reading telemetry store', err);
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
