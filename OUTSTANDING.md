# Diligence v4 — Outstanding Work

**Last updated:** June 22, 2026
**Session summary:** 5 commits, 35 files changed, +1,358/-329 lines

## What Was Delivered (June 22, 2026)

### Stream A — DW Branding ✅ COMPLETE
- Full palette swap from "Solar Momentum" (orange/green/blue) to DiligenceWorks brand (deep blue #2952CC, teal, IBM Plex Mono)
- Light and dark mode via `prefers-color-scheme` media query + manual `data-theme` override
- Typography: Outfit → Instrument Sans, Plus Jakarta Sans → IBM Plex Mono for data elements
- 30+ hardcoded hex color values replaced across 16 JSX files
- Border radii tightened from 14/10/20px to 8/6/12px

### Stream D — Security Hardening ✅ COMPLETE
- SEC-05: Fail-fast if SECRET_KEY is the default value
- SEC-06: CORS `allow_credentials=False`
- SEC-08: Input validation on auth schemas (username length/pattern, password min 8 chars)
- SEC-10: `.dockerignore` files for root, backend, mcp-connector
- SEC-11: JWT algorithm hardcoded as constant
- CQ-01: Crawl scheduler gated on `CRAWL_ENABLED` env var
- OS-02: `CONTRIBUTING.md`
- OS-03: `CHANGELOG.md` (v1.0.0)
- `setup.ps1`: API_TOKEN generation (Windows parity)

### Stream C — AI Agent Setup ✅ BACKEND + FRONTEND COMPLETE
- `ai_provider.py`: Multi-provider LLM routing with 2 code paths (OpenAI-compatible + Anthropic)
- Streaming SSE responses for all providers
- `ai_chat.py`: POST `/api/ai/chat` (SSE) + GET `/api/ai/status`
- Provider registry expanded from 11 to 20 providers across 4 categories
- `ChatCoach.jsx`: In-app chat UI with streaming, provider indicator, suggestion chips
- Nav updated: Home | Log | Keto | Programs | **Coach**
- README updated with 8-provider table + Claude Desktop/Code/Cursor/Windsurf configs
- AGENT_GUIDE updated with multi-MCP, Strava warning, provider-agnostic statement

### Stream B — Hardware Integrations ✅ FOUNDATION COMPLETE
- `device_sync_base.py`: Abstract base class with OAuth management, deduplication, webhook interface
- Provider registry includes Garmin, WHOOP, Oura, COROS, Fitbit, Withings, Suunto with accurate API URLs

---

## What Still Needs Doing

### Priority 1 — Blocked on API Credentials (Scot action items)

| Task | Blocker | Effort once unblocked |
|------|---------|----------------------|
| `garmin_sync.py` — Garmin Connect sync service | Apply at developer.garmin.com using DiligenceWorks Pte. Ltd. ~2 business days approval | 2-3 hours |
| `whoop_sync.py` — WHOOP sync service | Register at developer.whoop.com. Requires WHOOP device ownership | 2-3 hours |
| `oura_sync.py` — Oura Ring sync service | Register at cloud.ouraring.com. Self-serve, immediate | 2-3 hours |
| COROS partner API application | Apply at support.coros.com. Timeline unclear | MCP bridge already designed, no backend code needed |

Each sync service follows the pattern in `device_sync_base.py` and mirrors the existing `strava_sync.py`. The work is: OAuth flow, activity type mapping, API data fetching, and point awarding via `import_activity()`.

### Priority 2 — Code Work (no blockers)

| Task | Effort | Notes |
|------|--------|-------|
| Generic webhook receiver endpoint (`POST /api/integrations/webhook/{provider}`) | 1-2 hours | Dispatches to sync services when devices push data |
| Theme toggle UI in Settings page | 30 min | Light/dark/system toggle, stored in localStorage |
| SEC-07: Auth rate limiting (`slowapi` on login/register) | 30 min | Add `slowapi` to requirements.txt |
| SEC-09: UUID parameter validation in meal_plans/support routers | 20 min | Change `str` → `uuid.UUID` type hints |
| SEC-15: Enum validation for compliance status and meal_type | 20 min | Add `Literal[...]` types |
| UI-03: Fix React Hooks violation in HelpButton (App.jsx) | 10 min | Move `useEffect` above conditional return |
| UI-04: Load existing compliance data in MealPlan.jsx on mount | 30 min | Fetch from API and pre-populate state |
| UI-05: Error state handling in SettingsIntegrations + MealPlan | 30 min | Add error banners on API failures |
| Settings page accessibility after nav change | 20 min | Add gear icon in header or link from Coach page |
| Function calling for AI chat (tool use) | 2-3 hours | Let AI coach log workouts, search food via internal tools |

### Priority 3 — Polish (nice to have)

| Task | Effort |
|------|--------|
| Push updated code to GitHub (DiligenceWorks/Diligence) — clean-history push | 30 min |
| Deploy v4 to Coolify (fitness.littlefake.com) | 20 min |
| Update DW KB CONTEXT.md for fitness-rewards project | 20 min |
| OS-06: GitHub Actions CI pipeline (docker compose build) | 30 min |
| OS-07: Test suite (auth, points engine, meal plans) | 4-6 hours |
| OS-08: System requirements in README (RAM, disk, Docker version) | 10 min |
| OS-09: Backup/restore documentation in README | 10 min |
| UI-08: Default timezone from UTC instead of Asia/Bangkok | 5 min |

---

## Architecture Summary for Reviewers

**Container count:** 4 (unchanged — frontend, backend, mcp-connector, fitness-db)

**AI coaching flow:**
User types in Coach tab → POST `/api/ai/chat` → `ai_provider.py` reads configured provider from DB → routes to OpenAI-compatible endpoint OR Anthropic API → streams SSE response back to `ChatCoach.jsx`

**Device sync flow:**
User connects device via OAuth in Settings → credentials encrypted in `integration_configs` table → sync triggered by webhook (push) or manual sync (pull) → `device_sync_base.py` deduplicates and awards points via `points_engine.py`

**Provider registry:** 20 providers organized by category:
- **Device** (9): Strava✅, Polar✅, Garmin⏳, WHOOP⏳, Oura⏳, COROS (MCP), Fitbit, Withings, Suunto
- **AI** (8): OpenAI, OpenRouter, HuggingFace, Groq, Ollama, Claude, Gemini, Custom
- **Nutrition** (2): USDA✅, Nutritionix
- **Notifications** (1): Telegram✅

✅ = working sync service, ⏳ = sync service pending API credentials
