// =============================================================================
// server.cjs — Express production server for Meal Planner SPA
// =============================================================================
// Why .cjs? The project's package.json sets "type": "module", which makes
// Node treat .js files as ES modules. This file uses require() (CommonJS),
// so it MUST use the .cjs extension to bypass the module type detection.
//
// This server:
//   1. Serves static files from ./dist (the Vite production build)
//   2. Exposes /api/config for runtime environment variables
//   3. Acts as a SPA catch-all — any unrecognized route returns index.html
//      (so React Router handles client-side routing)
//
// Deployed on Cloud Run (port comes from $PORT env var, default 8080).
// =============================================================================

const express = require('express');
const path = require('path');

const app = express();
const port = process.env.PORT || 8080;       // Cloud Run injects PORT=8080

// ---- Serve compiled static assets ----
// Vite outputs everything under dist/ (index.html, JS, CSS, images, fonts)
app.use(express.static(path.join(__dirname, 'dist')));

// ---- Runtime config endpoint ----
// Exposes a few env vars to the browser WITHOUT baking them into the JS bundle.
// This allows changing values (e.g., AGENT_RUNTIME_ID) without a rebuild.
app.get('/api/config', (req, res) => {
  res.json({
    GOOGLE_CLOUD_PROJECT: process.env.GOOGLE_CLOUD_PROJECT || '',
    AGENT_RUNTIME_ID: process.env.AGENT_RUNTIME_ID || ''
  });
});

// ---- SPA catch-all ----
// Any request that didn't match a static file or /api/config gets index.html.
// React Router takes over from there with client-side routing.
// NOTE: We use app.use() instead of app.get('*') because path-to-regexp v8
// (shipped with newer Express) removed support for bare '*' wildcards.
app.use((req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

// ---- Start ----
app.listen(port, () => {
  console.log(`Frontend server running on port ${port}`);
});
