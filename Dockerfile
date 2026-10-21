# Chaukas — Single-container deployment
# Builds backend and frontend, serves both from FastAPI

# ---- Build Stage ----
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    ffmpeg \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Backend dependencies
COPY backend/pyproject.toml backend/uv.lock ./backend/
RUN cd backend && uv sync --frozen --no-dev

# Frontend dependencies
COPY package.json pnpm-workspace.yaml ./
COPY apps/web/package.json ./apps/web/
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# Copy source
COPY backend/chaukas ./backend/chaukas
COPY apps/web ./apps/web
COPY packages/protocol ./packages/protocol

# Build frontend
RUN cd apps/web && pnpm build

# ---- Runtime Stage ----
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy backend from builder
COPY --from=builder /app/backend /app/backend

# Copy built frontend
COPY --from=builder /app/apps/web/dist ./apps/web/dist

# Copy protocol types
COPY --from=builder /app/packages/protocol ./packages/protocol

# Environment
ENV PYTHONPATH=/app/backend
ENV PORT=8787

# Run
EXPOSE 8787
CMD ["uv", "run", "--directory", "/app/backend", "uvicorn", "chaukas.main:app", "--host", "0.0.0.0", "--port", "8787"]