# Makefile — Chaukas
# All targets must be invokable from a clean clone.

.PHONY: help setup dev check bench gen-types gen-audio e2e lint typecheck test test-web clean

# Default target
help:
	@echo "Chaukas — Live Scam-Call Guard and Test Lab"
	@echo ""
	@echo "Targets:"
	@echo "  make setup      - Install all dependencies (uv sync + pnpm install)"
	@echo "  make dev        - Run backend (uvicorn --reload) and frontend (vite) together"
	@echo "  make check      - Full CI pipeline (lint, typecheck, tests, bench, schema freshness, contrast)"
	@echo "  make bench      - Run benchmark CLI (gated by acceptance criteria)"
	@echo "  make gen-types  - Export JSON schema and generate TypeScript types"
	@echo "  make gen-audio  - Pre-generate scenario voices (requires TTS key)"
	@echo "  make e2e        - Start backend with STT_PROVIDER=mock and run Playwright"
	@echo "  make lint       - Run ruff on backend"
	@echo "  make typecheck  - Run mypy --strict on backend"
	@echo "  make test       - Run pytest on backend"
	@echo "  make test-web   - Run vitest + playwright on frontend"
	@echo "  make clean      - Remove build artifacts"

# ---------- Setup ----------
setup:
	cd backend && uv sync
	pnpm install

# ---------- Development ----------
dev:
	@echo "Starting backend and frontend..."
	@cd backend && uv run uvicorn chaukas.main:app --reload --port 8787 & \
	cd apps/web && pnpm dev

# ---------- Quality / CI ----------
check: lint typecheck test bench schema-fresh contrast-check test-web
	@echo "✓ All checks passed"

lint:
	cd backend && uv run ruff check .
	cd apps/web && pnpm lint

typecheck:
	cd backend && uv run mypy --strict chaukas
	cd apps/web && pnpm typecheck

test:
	cd backend && uv run pytest -v

test-web:
	cd apps/web && pnpm test
	cd apps/web && pnpm test:e2e

# ---------- Benchmark ----------
bench:
	cd backend && uv run chaukas-bench

# ---------- Code Generation ----------
gen-types:
	cd backend && uv run python -m chaukas.scripts.export_schema
	cd packages/protocol && pnpm gen:types

schema-fresh: gen-types
	@if ! git diff --quiet packages/protocol/ 2>/dev/null; then \
		echo "ERROR: Generated protocol types are stale. Run 'make gen-types' and commit."; \
		exit 1; \
	fi
	@echo "✓ Protocol types are up to date"

gen-audio:
	cd backend && uv run python -m chaukas.scripts.gen_scenario_audio

# ---------- E2E ----------
e2e:
	STT_PROVIDER=mock cd backend && uv run uvicorn chaukas.main:app --port 8787 & \
	sleep 3 && \
	cd apps/web && pnpm test:e2e

# ---------- Utilities ----------
clean:
	rm -rf backend/.venv
	rm -rf apps/web/node_modules
	rm -rf apps/web/dist
	rm -rf packages/protocol/node_modules
	rm -rf packages/protocol/dist
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache