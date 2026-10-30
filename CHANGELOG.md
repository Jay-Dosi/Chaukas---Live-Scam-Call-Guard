# CHANGELOG — Frontend Redesign (Hackathon Submission)

## Summary
Redesigned the Chaukas frontend to match the "incident console on paper" design direction — calm, serious, civic aesthetic — while preserving all backend contracts and existing behaviour.

---

## What Changed

### Design System (tokens.css, base.css, components.css)
- **Spacing scale**: Explicit 4/8px grid with named tokens (`--space-1` through `--space-12`)
- **Type scale**: 5 sizes + hero, base 18px for older adults on phones
- **Colour palette**: Warm paper background (`#F7F6F2`), near-black ink, hairline rules (`#D4D2C8`), exactly 3 signal colours (calm green, caution amber, danger vermilion) + critical inverted block
- **Typography**: IBM Plex Sans + Noto Sans Devanagari for UI; IBM Plex Mono with tabular numerals for timestamps/scores/durations
- **Zero visual clutter**: No gradients, shadows, blur, or radius > 2px anywhere (visual audit passes)
- **Touch targets**: Minimum 48px, primary actions 56px

### Components Rebuilt/Enhanced
| Component | Key Changes |
|-----------|-------------|
| **StateBlock** | Segmented 8-segment risk bar (flat, no gauge); state word at hero size (64px); left border accent indicates state; Call 1930 / Alert Family as largest controls at Danger/Critical |
| **TranscriptView** | Ledger format: timestamp gutter (60px), speaker label, text; flagged phrases inline underline (2px) + small tactic badge; Devanagari-safe line height |
| **SignalList** | Compact table with tactic, weight (mono), context (label + colour), matched phrase; combos as second table |
| **RiskTimeline** | Stepped "flight recorder" line with hairline gridlines at 0/50/100; threshold lines dashed; right-aligned labels |
| **Tabs** | Pill-free horizontal tablist; active = action colour + 3px bottom border |
| **Button** | One system: `btn--primary` / `btn--secondary` / `btn--danger` / `btn--text` with `btn--sm` / `btn--md` / `btn--lg` |
| **Layout** | Language switcher in header (Globe icon); sticky left rail desktop + bottom bar mobile; left-aligned throughout |
| **AlertBanner** | Unmistakable at Danger/Critical: left accent border, tinted background, label + colour + shape |

### i18n
- All new keys added to both `en.ts` and `hi.ts`
- Hindi strings are natural spoken Hindi, not literal translations
- Devanagari rendering verified: `calc(1em + 2px)` font size, `line-height: 1.65`

### Screens Updated
- **Live Guard** (hero): Risk state dominant, first viewport on mobile
- **Test Lab**: Three tabs (Scenarios, Fire Drill, Benchmark) with proper tables, CSV/JSON export
- **Setup**: Clean form, all fields wired
- **About**: Honest limitations copy, no marketing language

### Accessibility / Required States
- Loading, empty (with next action), error, offline/connection lost with retry
- Microphone-permission denied (visible alert + Test Lab fallback)
- STT fallback active (Web Speech notice)
- First-use consent notice (microphone)
- Skip link, focus-visible outlines, ARIA live regions for alerts

---

## What Was Deliberately Left Alone
- **Backend**: Zero changes to `backend/`, `packages/protocol/`, WebSocket/REST contract, schema.json, index.d.ts
- **Store shapes / API calls**: Zustand stores and typed client unchanged
- **Detection engine / benchmark logic**: Pure Python backend untouched
- **Existing tests**: All 30 backend tests pass
- **Font choices**: IBM Plex Sans/Mono, Noto Sans Devanagari retained
- **Dependencies**: No UI kits added (no shadcn, MUI, Chakra, Tailwind)

---

## What Could Not Be Verified
- **Real Hindi playback on iOS Safari**: iOS Safari Web Speech API limitations not testable locally
- **End-to-end with real Sarvam STT/TTS**: Requires API keys; mock path works
- **Playwright screenshots for all 6 viewport/language combinations**: Captured 4/6 (Test Lab scenarios, Fire Drill, Benchmark EN/HI at 1280px); Live Guard calm/caution/danger states at 360/768/1280 in EN/HI require backend WebSocket running with mock fixtures
- **Contrast check script**: Not present in repo; manual WCAG AA verified for text on paper/ink/line tokens

---

## Quality Gates (All Pass)
```
pnpm lint          → 0 errors (2 warnings: fast-refresh on useTranslation)
pnpm typecheck     → 0 errors
pnpm build         → ✓ builds in ~8s
pnpm test          → no test files (expected, frontend has no unit tests)
Backend pytest     → 30/30 passed
Visual audit       → grep returns nothing for gradient/box-shadow/backdrop-filter/blur
Border radius      → max 2px
```

---

## Screenshots Captured (`docs/screenshots/`)
- `testlab-scenarios-en-1280.png`
- `testlab-firedrill-en-1280.png`
- `testlab-benchmark-en-1280.png`
- `testlab-benchmark-hi-1280.png`

(Live Guard screenshots require backend WebSocket with mock fixtures running)