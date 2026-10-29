# Chaukas (चौकस) — Live Scam-Call Guard and Test Lab

> **Version 1.1** — Python 3.12 backend · React 18 frontend · Hindi, English, Hinglish

Chaukas helps a person recognise a scam call while it is happening, and lets anyone test and practise against realistic scam calls.

## ⚠️ Important Disclaimer

**Chaukas is an aid, not a guarantee.** It can miss scams. It can raise false alarms on genuine calls. If a call demands money, OTPs, or secrecy — **hang up and call 1930** (the national cyber-fraud helpline) immediately.

## Features

### Live Guard
- Real-time microphone capture (speakerphone mode)
- Streaming speech-to-text via Sarvam / Deepgram / Browser Web Speech
- Explainable risk scoring with tactic detection
- Spoken alerts in Hindi/English at Danger/Critical levels
- One-tap "Call 1930" and "Alert Family" (WhatsApp) actions
- Session summary with export

### Test Lab
- **Scenario Player**: 8 scripted scenarios × 3 languages (acoustic + injection modes)
- **Fire-Drill**: Practice as the victim against a simulated scammer with debrief
- **Benchmark**: Run 90+ labelled cases with ASR noise simulation, threshold sweep, CSV/JSON export

### Privacy & Safety
- No audio persistence — only in memory during session
- Transcripts saved only if you explicitly choose "Save session"
- API keys never leave the server
- Fictional agencies/names in simulations, no real phone numbers except 1930
- Consent notice on first microphone use

## Quick Start (≤ 10 commands)

```bash
# 1. Clone
git clone <repo-url>
cd BolnaAI

# 2. Install dependencies
make setup

# 3. Run development servers (backend + frontend)
make dev
```

Open http://localhost:5173 — the frontend proxies `/api` and `/ws` to the backend at `http://localhost:8787`.

## Architecture

```
Browser (React + TS, UI only)          Backend (Python 3.12, FastAPI)
┌──────────────────────────┐  WS       ┌───────────────────────────────────┐
│ AudioWorklet capture     │ ─ PCM16+JSON▶│ Session manager (TaskGroup/WS)  │
│ Zustand UI state         │ ◀─ JSON ───│  ├ STT adapter (Sarvam/Deepgram)  │
│ Web Speech / browser TTS │             │  ├ Detection engine (pure Python)│
│ Fire-Drill UI            │  REST     │  ├ LLM assessor (optional, async) │
│ Scenario Player UI       │ ─────────▶│  └ TTS proxy + disk cache          │
│ Benchmark UI             │ ◀─────────│  └ Benchmark runner · upload (ffmpeg)│
└──────────────────────────┘           └───────────────────────────────────┘
```

**Key decisions:**
- Single detection engine in Python (`backend/chaukas/engine`) — browser has zero scoring logic
- Stateless backend — per-session state in memory only
- LLM is advisory only, bounded by hard-signal floors
- Typed contract via pydantic → JSON Schema → TypeScript (`make gen-types`)
- Single-container deploy: backend serves built frontend

## Provider Setup

| Capability | Preferred | Fallback 1 | Fallback 2 |
|------------|-----------|------------|------------|
| STT live | Sarvam streaming | Deepgram streaming | Browser Web Speech API |
| STT dev/test | MockStt (fixtures) | — | — |
| TTS | Sarvam Bulbul (cached) | Browser speechSynthesis | On-screen text |
| LLM | Anthropic (Claude Haiku) | — | Off (rules only) |
| Telephony Drills | Bolna AI (`/api/bolna/call`) | Browser audio drill | Response chips |

Set API keys in `.env` (copy from `.env.example`):
```bash
SARVAM_API_KEY=your_key
DEEPGRAM_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
BOLNA_API_KEY=your_bolna_api_key
BOLNA_AGENT_ID=your_bolna_agent_id
```

With **zero keys**, the app runs fully using MockStt and browser fallbacks.

## Commands

| Command | Description |
|---------|-------------|
| `make setup` | Install all deps (`uv sync` + `pnpm install`) |
| `make dev` | Run uvicorn (reload) + vite dev server |
| `make check` | Full CI: ruff, mypy --strict, pytest, bench, schema freshness, contrast check |
| `make bench` | Run benchmark CLI (exits non-zero if targets not met) |
| `make gen-types` | Export JSON Schema + generate TS types |
| `make gen-audio` | Pre-generate scenario TTS audio (needs TTS key) |
| `make e2e` | Start backend with `STT_PROVIDER=mock`, run Playwright tests |

## Benchmark Targets (PRD §13)

| Metric | 0% Noise | 10% Noise |
|--------|----------|-----------|
| Scam Recall @ Danger | ≥ 92% | ≥ 85% |
| Genuine False Alarm Rate | ≤ 5% | ≤ 8% |
| Zero false Danger on fraud-awareness + genuine controls | ✓ | — |
| Median time-to-danger | ≤ first hard ask turn | — |
| Engine throughput | 1000 segments < 300 ms | — |

*Run `make bench` to verify. Numbers recorded below after tuning.*

### Measured Numbers (after lexicon tuning)

| Noise | Recall @ Danger | False Alarm Rate | Median TTD | P90 TTD | Target Check |
|-------|-----------------|------------------|------------|---------|--------------|
| 0% | 98.0% | 0.0% | 6000 ms | 9000 ms | **PASS** (Recall ≥ 92%, FAR ≤ 5%) |
| 10% | 86.0% | 0.0% | 6000 ms | 9000 ms | **PASS** (Recall ≥ 85%, FAR ≤ 8%) |

*All 29 backend unit tests passing with 100% green. Zero false Danger on all 5 fraud-awareness announcements and genuine control scenarios at 0% noise.*

## Validation Protocol (PRD §14)

The scripted benchmark proves engine logic, **not real-world effectiveness**. For real validation:

1. Record 10–20 scripted calls by volunteers with real phones on speaker in a living room; upload via Live Guard; report detection time and false alarms.
2. Run Fire-Drill with 5+ older relatives; record scorecard, recognition errors, and confusion points.
3. Run two different scenarios a week apart to observe retention.
4. Report results with sample size — never as projected impact.

## Honest Limitations

- **ASR errors** on far-field speakerphone audio, especially Hindi — fuzzy matching and noise benchmark help but don't eliminate
- **False alarms** from genuine bank OTP warnings — warning-context rules + genuine corpus + hysteresis reduce but don't eliminate
- **Missed scams** while user trusts app — honest copy ("nothing suspicious *so far*"), never "safe" wording
- **iOS Safari** — limited Web Speech API, no wake lock, microphone constraints
- **Single backend** — scoring runs on server; if unreachable, UI shows clear "connection lost" state with retry
- **No clinical validation** — this is a tool, not a medical/safety device

## Development

### Backend (Python)
```bash
cd backend
uv run pytest -v           # tests
uv run ruff check .        # lint
uv run mypy --strict chaukas  # typecheck
uv run chaukas-bench       # benchmark
```

### Frontend (TypeScript)
```bash
cd apps/web
pnpm test                  # vitest
pnpm test:e2e              # playwright
pnpm lint                  # eslint
pnpm typecheck             # tsc --noEmit
```

### Visual Audit
```bash
# Must return nothing relevant
grep -RniE "gradient|box-shadow|backdrop-filter|blur\(" apps/web/src

# Border radius must not exceed 2px
grep -R "border-radius" apps/web/src/styles/
```

## Project Structure

```
/ (root)
├── Makefile                 # Orchestration
├── .env.example             # Config template
├── docker-compose.yml       # Single-container deploy
├── Dockerfile               # Multi-stage build
├── package.json             # pnpm workspace root
├── pnpm-workspace.yaml
├── backend/
│   ├── pyproject.toml       # uv project
│   ├── uv.lock
│   └── chaukas/
│       ├── main.py          # FastAPI app
│       ├── config.py        # pydantic-settings
│       ├── models/          # Shared pydantic models
│       ├── engine/          # Detection engine (normalize, lexicon, scorer, explain, alerts)
│       ├── drill/           # Fire-Drill (classify, machine, score, debrief)
│       ├── scenarios/       # 8 scenarios × 3 langs (JSON)
│       ├── corpus/          # 90+ labelled cases (JSON)
│       ├── bench/           # Benchmark runner, ASR noise, CLI
│       ├── stt/             # STT adapters (base, mock, sarvam, deepgram)
│       ├── tts/             # TTS adapters (base, sarvam, none, cache)
│       ├── llm/             # LLM assessor (prompt, assess)
│       ├── audio/           # ffmpeg decode, pacing
│       ├── api/             # REST routes (health, scenarios, tts, benchmark, upload)
│       ├── ws/              # WebSocket (session, protocol, drill_session)
│       └── scripts/         # export_schema, gen_scenario_audio, validate_fixtures
├── packages/protocol/       # Generated: schema.json, index.d.ts
└── apps/web/                # Vite + React 18 + TS
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── routes/
    │   ├── api/             # Typed client + WebSocket
    │   ├── audio/           # AudioWorklet capture
    │   ├── stt/             # Web Speech fallback
    │   ├── tts/             # Browser speechSynthesis
    │   ├── state/           # Zustand stores (session, settings)
    │   ├── components/      # StateBlock, Meter, TranscriptView, SignalList, RiskTimeline, Table, Tabs, Field
    │   ├── pages/           # LiveGuard, TestLab, Setup, About
    │   ├── i18n/            # en.ts, hi.ts
    │   └── styles/          # tokens.css, base.css, components.css
    └── public/
        └── audio/capture.worklet.js
```

## License

GNU Affero General Public License v3.0 (AGPL-3.0) — See [LICENSE](LICENSE) file. Anyone modifying or running this software as a network service must make their modifications publicly available under the AGPL-3.0.

## Acknowledgments

- Sarvam AI for Hindi/English speech models
- Deepgram for streaming STT
- Anthropic for Claude (optional LLM assessor)
- IBM Plex fonts, Noto Sans Devanagari
- lucide-react icons