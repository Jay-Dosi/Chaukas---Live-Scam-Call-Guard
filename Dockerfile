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

# Backend dependencies & build
COPY backend/pyproject.toml backend/uv.lock ./backend/
COPY backend/chaukas ./backend/chaukas
RUN cd backend && uv sync --frozen --no-dev

# Frontend dependencies & build
COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml ./
COPY packages/protocol ./packages/protocol
COPY apps/web ./apps/web
RUN npm install -g pnpm && pnpm install --frozen-lockfile
RUN cd apps/web && pnpm build

# ---- Runtime Stage ----
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy uv from builder
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

# Copy backend from builder
COPY --from=builder /app/backend /app/backend

# Copy built frontend
COPY --from=builder /app/apps/web/dist ./apps/web/dist

# Copy protocol types
COPY --from=builder /app/packages/protocol ./packages/protocol

# Environment
ENV PYTHONPATH=/app/backend
ENV PATH="/app/backend/.venv/bin:$PATH"
ENV PORT=8787

# Run
EXPOSE 8787
CMD ["uv", "run", "--no-dev", "--directory", "/app/backend", "uvicorn", "chaukas.main:app", "--host", "0.0.0.0", "--port", "8787"]
