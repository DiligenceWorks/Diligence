# Diligence — Self-Hosted Fitness Rewards with AI Agent Support

Points-based fitness accountability app. Log workouts and food, earn points, unlock rewards. Connect any AI agent via MCP for logging, coaching, and meal planning. Self-hosted, open source, zero cloud dependencies.

Built by [DiligenceWorks](https://diligenceworks.online).

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows, macOS, or Linux)
- That's it. No Python, Node.js, or database install needed.

### Install

**macOS / Linux:**
```bash
git clone https://github.com/diligenceworks/diligence
cd diligence
./setup.sh
docker compose up -d
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/diligenceworks/diligence
cd diligence
powershell -ExecutionPolicy Bypass -File setup.ps1
docker compose up -d
```

**Windows (no script — manual):**
```powershell
git clone https://github.com/diligenceworks/diligence
cd diligence
copy .env.example .env
# Edit .env and set SECRET_KEY to any random string (e.g. mash the keyboard)
docker compose up -d
```

Open http://localhost and create your account. First user gets admin.

### Verify

```bash
docker compose ps
```

You should see 4 containers, all healthy: `frontend`, `backend`, `mcp-connector`, `fitness-db`.

## Features

- **Points economy** — earn from workouts, food logging, step goals. Daily gate locks rewards until you earn enough. Weekly reset.
- **Science-based onboarding** — PAR-Q+ safety screening, TTM stages of change, BREQ-2 motivation profiling.
- **AI agent integration** — 14 MCP tools for logging, coaching, meal planning, and device configuration.
- **Meal plans** — AI-generated plans with compliance tracking and points integration.
- **Activity sync** — Strava, Polar (OAuth 2.0). Garmin, Fitbit, Withings, WHOOP, Oura configurable in-app.
- **Food search** — Open Food Facts (4M+ products) + USDA FoodData Central (400K+ research-grade).
- **Program tracking** — 90-day structured programs (StrongLifts, Darebee, etc.) with day-by-day progression.
- **Configurable rewards** — you define what's worth earning. Gaming time, screen time, treats — your rules.

## Connecting an AI Agent

Point your agent's MCP config at:

| Environment | URL |
|-------------|-----|
| Local (development) | `http://localhost:3001/sse` |
| Behind reverse proxy | `https://your-domain/mcp` |

Works with Claude Desktop, Cursor, Windsurf, and any MCP-compatible agent.

Copy the contents of [AGENT_GUIDE.md](AGENT_GUIDE.md) into your agent's system instructions for motivation-aware coaching.

### Claude Desktop example

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "diligence": {
      "url": "http://localhost:3001/sse"
    }
  }
}
```

Then paste the contents of `AGENT_GUIDE.md` into your Claude Desktop project instructions.

## Configuring Integrations

All integrations are configured through the app UI (**Settings → Integrations**) or through your AI agent. No `.env` file editing or container restarts needed.

Tell your agent: *"I want to connect my Strava"* — it will walk you through getting API credentials and store them encrypted.

## Data Sovereignty

Diligence is self-hosted software. Your data never leaves your server. No cloud dependency, no vendor lock-in, no telemetry. MIT license — fork it, modify it, keep it forever.

Your fitness data — heart rate, body composition, food intake, GPS traces — is biometric data that deserves sovereignty.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                    nginx                         │
│         (frontend, /api proxy, /mcp proxy)       │
├──────────┬─────────────────┬────────────────────┤
│ React    │   FastAPI        │   MCP Connector    │
│ SPA      │   Backend        │   (14 tools)       │
│          │                  │   port 3001        │
│          ├──────────────────┤                    │
│          │  PostgreSQL 16   │                    │
│          │  (internal only) │                    │
└──────────┴──────────────────┴────────────────────┘
```

## Stack

- Python 3.12, FastAPI, SQLAlchemy (async)
- React 18, Vite
- PostgreSQL 16
- FastMCP (Streamable HTTP/SSE)
- Docker Compose

## Updating

```bash
git pull
docker compose build
docker compose up -d
```

Database migrations run automatically on startup. Your data is preserved.

## Backing Up

Your data lives in the `fitness_db_data` Docker volume:

```bash
docker compose exec fitness-db pg_dump -U fitness fitness_rewards > backup.sql
```

To restore:

```bash
docker compose exec -i fitness-db psql -U fitness fitness_rewards < backup.sql
```

## Contributing

Contributions welcome. Please open an issue to discuss before submitting a PR.

## License

MIT — see [LICENSE](LICENSE).
