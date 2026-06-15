# Diligence — Self-Hosted Fitness Rewards with AI Agent Support

Points-based fitness accountability app. Log workouts and food, earn points, unlock rewards. Connect any AI agent via MCP for logging, coaching, and meal planning. Self-hosted, open source, zero cloud dependencies.

Built by [DiligenceWorks](https://diligenceworks.online).

## Quick Start

```bash
git clone https://github.com/diligenceworks/diligence
cd diligence
./setup.sh
docker compose up -d
```

Open http://localhost and create your account.

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

Point your agent's MCP config to `http://localhost:3001/sse` (development) or `https://your-domain/mcp` (production behind reverse proxy).

Works with Claude Desktop, Cursor, Windsurf, and any MCP-compatible agent.

Copy the contents of [AGENT_GUIDE.md](AGENT_GUIDE.md) into your agent's system instructions for motivation-aware coaching.

## Configuring Integrations

All integrations are configured through the app UI (Settings → Integrations) or through your AI agent. No `.env` file editing or container restarts needed.

## Data Sovereignty

Diligence is self-hosted software. Your data never leaves your server. No cloud dependency, no vendor lock-in, no telemetry. MIT license — fork it, modify it, keep it forever.

Your fitness data — heart rate, body composition, food intake, GPS traces — is biometric data that deserves sovereignty.

## Stack

- Python 3.12, FastAPI, SQLAlchemy
- React 18, Vite
- PostgreSQL 16
- FastMCP (Streamable HTTP/SSE)
- Docker Compose

## Contributing

Contributions welcome. Open an issue to discuss before submitting a PR.

## License

MIT — see [LICENSE](LICENSE).
