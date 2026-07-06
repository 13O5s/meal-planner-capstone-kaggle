# =============================================================================
# Dockerfile — Frontend Container (meal-planner-ui)
# =============================================================================
# Multi-stage build:
#   Stage 1 (build) : Installs dependencies, runs `tsc && vite build`
#   Stage 2 (run)   : Serves the compiled SPA via Express on port 8080
#
# Build arg:
#   VITE_API_URL — Backend URL that Vite bakes into the JS bundle at build time
#                  (e.g. https://meal-planner-api-XXXXXX.us-east1.run.app)
#
# Deployed to: Cloud Run (us-east1)
# =============================================================================

# ---- Stage 1: Build the React/Vite application ----
FROM node:20-slim AS build

WORKDIR /app

# Accept the backend API URL at build time, then bake it into the bundle
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

# Install dependencies first (leveraging Docker layer caching)
COPY package*.json ./
RUN npm install

# Copy source and build (tsc -b for type-check, vite build for bundling)
COPY . .
RUN npm run build

# ---- Stage 2: Production runtime ----
FROM node:20-slim

WORKDIR /app

# Install only production deps (express serves the static dist folder)
COPY package*.json ./
RUN npm install --only=production && npm install express

# Copy the built artifacts from Stage 1
COPY --from=build /app/dist ./dist

# Copy the Express server (uses .cjs extension to force CommonJS in an ESM project)
COPY server.cjs ./

# Cloud Run expects the container to listen on PORT=8080
EXPOSE 8080

# Start the Express server that serves index.html for all routes (SPA catch-all)
CMD ["node", "server.cjs"]
