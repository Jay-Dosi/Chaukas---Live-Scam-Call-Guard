# DESIGN — Chaukas Frontend Redesign
## Incident console on paper

### Design direction
Calm, serious, civic. A well-made government form crossed with a flight-recorder log — not a startup landing page.
- **Surface**: warm off-white paper background, near-black ink text, hairline 1px rules instead of cards-with-shadows
- **Colour**: restrained neutral palette + exactly 3 signal colours mapped to risk levels (calm green, caution amber, danger vermilion). Colour is *never* the only carrier of meaning: always pair with a label and a shape or pattern
- **Type**: IBM Plex Sans for UI, IBM Plex Mono with tabular numerals for timestamps, scores, durations. A clear scale of 5 sizes defined as tokens. Strong hierarchy through weight and size, not through boxes
- **Layout**: left-aligned, grid-based, generous but consistent spacing from a 4/8px scale. No centred hero sections, no 3-column icon-card grids, no pill buttons
- **Motion**: only functional (state changes, alert entrance, meter updates), under 200ms, respects prefers-reduced-motion

### Colour tokens (tokens.css)
```
--paper:      #F7F6F2   /* page background, warm off-white */
--surface:    #FFFFFF   /* panels, cards */
--surface-sunk: #EFEDE6 /* wells, transcript bg */

--ink:        #14171C   /* primary text, near-black */
--ink-2:      #454B55   /* secondary text, 7.5:1 on paper */
--ink-3:      #6B717C   /* tertiary, only >=18px */

--line:       #CFCDC4   /* 1px borders, dividers */
--line-strong:#14171C   /* 2px structural rules */

--calm:       #1F6A3D   /* calm green */
--calm-bg:    #E3EFE7   /* calm background */

--caution:    #8A5A00   /* caution amber */
--caution-bg: #F6EBCF   /* caution background */

--danger:     #B3261E   /* danger vermilion */
--danger-bg:  #F7E0DD   /* danger background */

--critical:   #FFFFFF   /* inverted block */
--critical-bg:#8F1B15   /* critical background */

--action:     #1B3A5C   /* primary buttons, links */
--action-ink: #FFFFFF   /* primary button text */
```

### Type scale (tokens.css)
```
--t-xs: 0.8125rem   /* 14.6px */
--t-sm: 0.9375rem   /* 15px */
--t-md: 1.125rem    /* 18px — base */
--t-lg: 1.375rem    /* 22px */
--t-xl: 1.75rem     /* 28px */
--t-2xl: 2.5rem     /* 40px */
--t-hero: 4rem      /* 64px — state word */
```

### Spacing
```
--space: 4px   /* all spacing multiples of 4 */
--radius: 2px  /* max border radius — panels have 0 radius */
```

### Typography
- Body: 18px (set on html in base.css), line-height 1.6, color: var(--ink)
- Headings: scale via --t-xl to --t-hero, font-weight 600, line-height 1.3
- Devanagari: Noto Sans Devanagari, font-size calc(1em + 2px), line-height 1.55
- Monospace (timestamps, scores, durations): IBM Plex Mono, tabular numerals implicit via font

### Component rules
- **Buttons**: one system only — primary (action), secondary (ghost), danger (vermilion), text (link-style). Min 48px height, min 56px primary. `btn`, `btn-primary`, `btn-secondary`, `btn-danger`, `btn-ghost` classes. Hover: `filter: brightness(0.95)`. Focus: `outline: 3px solid var(--focus)`.
- **Inputs**: `field` class, min-height 48px, padding 12px 16px, border 2px solid var(--line), border-radius 2px, transition 120ms. Focus: border-color var(--ink), outline none.
- **StateBlock**: panels have 0 radius, border 1px var(--line). Calm: border-color var(--calm). Caution: bg var(--caution-bg) + border var(--caution). Danger: bg var(--danger-bg) + border var(--danger). Critical: bg var(--critical-bg) + border var(--critical-bg) + color var(--critical). Meter: 8-segment flat bar, gap 2px, height 16px, segments var(--line) filled with respective colour. No box-shadow.
- **Transcript**: ledger format, timestamp gutter left, speaker label, text. Flagged phrases: inline underline (2px thickness, text-underline-offset 2px) in signal colour + small badge token with context label. No emoji bullets. No gradient badges.
- **SignalList**: compact table with tactic, weight (mono), context (label + colour), matched phrase. No unnecessary spacing.
- **RiskTimeline**: simple stepped line with hairline gridlines (1px var(--line)). Threshold lines 1px dashed. Points as circles r=3. Labels 10px font. No background fills, no gradients.
- **Tabs**: horizontal tablist, pills with padding var(--space)*3 horizontal, var(--space)*6 vertical. Active item: color var(--action), border-bottom var(--action) 3px. Hover: color var(--ink). Focus: outline 3px var(--focus).
- **Table**: border-collapse collapse, 1px var(--line) cells, tabular numerals for numbers. Compact variant with reduced padding.
- **Layout**: left-aligned, max-width 1200px, margin 0 auto, padding var(--space)*6. Grid: 12-col desktop, 6-col tablet, 4-col mobile, gap 4/8px. No centred content.
- **Bottom bar (mobile)**: fixed, bottom 0, left 0, right 0, surface bg, border-top 1px var(--line), z-index 50, padding env(safe-area-inset-bottom).

### Required states for every screen
- Loading
- Empty (with a useful next action)
- Error
- Offline/"connection lost" with retry
- Microphone-permission denied
- STT fallback active
- First-use consent notice

### Honest copy rules (never break)
- Never use "safe" or "protected" wording. Use "nothing suspicious so far".
- Keep the disclaimer prominent: "Chaukas is an aid, not a guarantee. It can miss scams. If a call demands money, OTPs, or secrecy, hang up and call 1930."
- 1930 call-to-action prominent (large control at Danger/Critical)
- No exclamation marks in UI copy
- No "Welcome to", no "Powered by AI"
- Short, concrete labels. Tool-like, not marketing.

### i18n
- Hindi + English must both work everywhere
- Devanagari text must not be clipped, mis-sized, or line-height-broken
- Test with long Hindi strings (e.g. the full Hindi scenario texts)
- All UI strings in both en.ts and hi.ts — identical key sets, natural Hindi not literal translation

### Screen-specific plans
- **Live Guard (hero screen)**: risk state dominant, first viewport on mobile. Segmented risk bar (not gauge/donut). Transcript as ledger: timestamp gutter left, speaker label, text, flagged phrases marked inline (underline + small tactic tag). Signals as compact table: tactic, evidence phrase, weight. Risk timeline: simple stepped line with hairline gridlines. At Danger/Critical: whole screen shifts to unmistakable alert state with Call 1930 as largest control, Alert Family second.
- **Test Lab**: three clear modes (Scenario Player, Fire-Drill, Benchmark) as tabs. Benchmark results: proper tables with tabular numerals, pass/fail targets beside measured values, CSV/JSON export buttons. Fire-Drill debrief: scorecard format.
- **Setup**: form with clearly labelled fields, no fake features.
- **About**: static information page, honest limitations copy.

### Visual-audit rules (must return NOTHING relevant)
```
grep -RniE "gradient|box-shadow|backdrop-filter|blur\(" apps/web/src
```
- Must return nothing
- Border-radius never above 2px

### Checklist before shipping
- All existing tests pass: `pnpm test`, `pnpm test:e2e`
- `pnpm lint`, `pnpm typecheck`
- `make check` (full CI)
- Visual-audit greps return nothing
- Playwright screenshots of Live Guard in calm/caution/danger, English/Hindi, 360/768/1280px
- Both languages look intentional, not translated-in-afterwards

### What I deliberately left alone (backend contract)
- No backend changes. Store shapes, API calls, WebSocket/REST contract unchanged.
- No changes to packages/protocol/, schema.json, index.d.ts.
- Backend engine logic, detection, benchmark — untouched.