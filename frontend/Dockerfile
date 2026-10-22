# syntax=docker/dockerfile:1

# =============================================================================
# Stage 1: Builder — build frontend with Vite
# =============================================================================
FROM node:22.13-alpine AS builder

WORKDIR /build

# Copy dependency manifests
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build argument for API URL (empty for production, API through same origin)
ARG VITE_API_URL=""
ENV VITE_API_URL=${VITE_API_URL}

# Build the application
RUN npm run build

# =============================================================================
# Stage 2: Runtime — serve with Caddy
# =============================================================================
FROM caddy:2.9-alpine

# Copy built assets
COPY --from=builder /build/dist /srv

# Copy Caddyfile
COPY Caddyfile /etc/caddy/Caddyfile

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --spider --quiet http://localhost:80/ || exit 1

EXPOSE 80

CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
