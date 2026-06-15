# Diligence — Agent Skill Definition

## What Is Diligence?

Diligence is a self-hosted fitness rewards platform. Users earn points through fitness activities (workouts, food logging, step goals) and spend them on configurable rewards (gaming time, screen time, etc.). A daily gate keeps rewards locked until enough points are earned. Points reset weekly.

## Architecture

- **Backend:** FastAPI (Python 3.12) + PostgreSQL 16
- **Frontend:** React 18 + Vite, served by nginx
- **MCP Connector:** FastMCP (Streamable HTTP/SSE) on port 3001, proxied via nginx at `/mcp`
- **Deployment:** Docker Compose (4 services: frontend, backend, mcp-connector, fitness-db)

## Connecting

Point your MCP client to:
- **Development:** `http://localhost:3001/sse`
- **Production:** `https://your-domain/mcp`

## Available Tools (14)

| Tool | Category | Description |
|------|----------|-------------|
| `get_context()` | Status | Full profile, motivation, program, rules, rewards |
| `get_today(date?)` | Status | Daily points, gate status, activities |
| `get_week(start_date?)` | Status | Weekly summary, active days |
| `log_activity(category, title, duration_minutes, ...)` | Activity | Log workout, earn points |
| `log_food(meal_type, food_name, ...)` | Food | Log food with macros |
| `search_food(query)` | Food | Search Open Food Facts + USDA |
| `get_program_schedule(date?)` | Programs | Today's workout from active program |
| `redeem_reward(reward_name)` | Rewards | Spend points on a reward |
| `load_meal_plan(name, duration_days, meals, ...)` | Meal Plans | Create a full meal plan |
| `get_meal_plan(date?)` | Meal Plans | View today's planned meals |
| `update_meal_compliance(plan_item_id, status, ...)` | Meal Plans | Mark meal followed/skipped |
| `get_plan_progress(plan_id?)` | Meal Plans | Compliance statistics |
| `configure_integration(provider, credentials)` | Integrations | Store encrypted credentials (write-only) |
| `get_integration_status()` | Integrations | Check provider connection status |

## Key Design Decisions

- The **agent generates meal plans** — the app only stores and tracks them. Zero AI API cost.
- Integration credentials are **write-only through MCP** — agents can set but never read them back.
- The app collects **BREQ-2 motivation data** during onboarding. Use `get_context()` to read the user's motivation profile and calibrate tone accordingly.
- Points reset weekly. Each week is a fresh start. No guilt carry-over.

## Source

- **Repository:** https://github.com/diligenceworks/diligence
- **License:** MIT
- **Built by:** DiligenceWorks Pte. Ltd. (https://diligenceworks.online)
