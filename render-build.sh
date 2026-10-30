#!/usr/bin/env bash
# Render build script for native Python environment
set -o errexit

echo "=== Installing pnpm and building frontend ==="
npm install -g pnpm@9.7.0
pnpm install --frozen-lockfile
pnpm --filter web build

echo "=== Installing uv and syncing backend ==="
pip install uv
cd backend
uv sync --frozen --no-dev

echo "=== Build succeeded! ==="

