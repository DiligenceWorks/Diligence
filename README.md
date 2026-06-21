# Diligence — Self-Hosted Fitness Rewards with AI Agent Support

Points-based fitness accountability app. Log workouts and food, earn points, unlock rewards. Connect any AI agent via MCP for logging, coaching, and meal planning. Self-hosted, open source, zero cloud dependencies.

Built by [DiligenceWorks](https://diligenceworks.online).

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — that's it. No Python, Node.js, or database install needed.
- Docker Desktop runs natively on **Windows 10/11**, **macOS**, and **Linux**.

---

### Windows 11 Setup

**1. Install Docker Desktop**

Download from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/).

During installation, the installer presents a checkbox: **"Use WSL 2 instead of Hyper-V (recommended)"**. This is checked by default.

- **WSL 2 backend (default):** Works on all Windows editions including Home. Lower resource usage, better performance. Requires WSL 2 to be installed first — open PowerShell as Administrator and run `wsl --install`, then reboot.
- **Hyper-V backend:** If WSL 2 causes issues (black screen on reboot, kernel errors, or containers won't start), uncheck the WSL 2 box during installation to use Hyper-V instead. Requires Windows Pro, Enterprise, or Education.

**Important:** Hardware virtualization must be enabled in your BIOS/UEFI settings (Intel VT-x or AMD-V). This is the most common cause of "Docker won't start" issues. Check your laptop/PC manufacturer's documentation for how to access BIOS settings (usually F2, F12, or Del during boot).

**2. Clone and run**

Open PowerShell:
```powershell
git clone https://github.com/diligenceworks/diligence
cd diligence
powershell -ExecutionPolicy Bypass -File setup.ps1
docker compose up -d
```

Or without the script:
```powershell
git clone https://github.com/diligenceworks/diligence
cd diligence
copy .env.example .env
# Edit .env and set SECRET_KEY to any random string
docker compose up -d
```

---

### macOS Setup

**1. Install Docker Desktop**

Download from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/). Make sure you pick the right installer for your chip:

- **Apple Silicon** (M1, M2, M3, M4) — download the Apple Silicon .dmg
- **Intel** — download the Intel .dmg

To check: Apple menu → About This Mac. Look for "Chip" (Apple Silicon) or "Processor" (Intel).

Drag Docker.app to Applications and launch it. Requires macOS 13 Ventura or later.

Alternatively, install via Homebrew: `brew install --cask docker`

**2. Clone and run**

Open Terminal:
```bash
git clone https://github.com/diligenceworks/diligence
cd diligence
./setup.sh
docker compose up -d
```

---

### Linux Setup

Install Docker Engine and Docker Compose via your distro's package manager, or install Docker Desktop for Linux. Then:

```bash
git clone https://github.com/diligenceworks/diligence
cd diligence
./setup.sh
docker compose up -d
```

---

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

## Built-in AI Coach

Diligence includes a built-in AI coaching chat. Configure any LLM provider in **Settings → Integrations**, then open the **Coach** tab.

Supported providers (one API key, that's it):

| Provider | Free tier | What you get |
|----------|-----------|-------------|
| **OpenRouter** | 26 free models | 300+ models from every major provider, one key |
| **Hugging Face** | Yes | Thousands of open-source models |
| **Groq** | Yes | Ultra-fast Llama inference |
| **Ollama** | Local, free | Run any model on your own machine |
| **OpenAI** | No | GPT-4o, GPT-4o-mini |
| **Claude** | No | Claude Sonnet 4.6, Opus 4.8 |
| **Gemini** | Yes | Gemini 2.0 Flash, 2.5 Pro |
| **Custom** | — | Any OpenAI-compatible endpoint (vLLM, TGI, LiteLLM) |

The AI coach has access to your profile, points, program schedule, and motivation type. It can log workouts, search food, and create meal plans through the chat.

### Connecting external AI agents (MCP)

The MCP connector at port 3001 works with any MCP-compatible agent. The built-in chat and external agents coexist — use whichever fits your workflow.

**Claude Desktop** — add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "diligence": { "url": "http://localhost:3001/sse" }
  }
}
```

**Claude Code** (CLI):
```bash
claude mcp add diligence --transport sse http://localhost:3001/sse
```

**Cursor** — add to `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "diligence": { "url": "http://localhost:3001/sse" }
  }
}
```

**Windsurf** — add to MCP settings, same format as Cursor.

**COROS watch owners** — add both Diligence and COROS MCP servers to your agent. The agent bridges your watch data with your fitness log:
```json
{
  "mcpServers": {
    "diligence": { "url": "http://localhost:3001/sse" },
    "coros": { "url": "https://your-coros-mcp-url/sse" }
  }
}
```

Copy the contents of [AGENT_GUIDE.md](AGENT_GUIDE.md) into your agent's system instructions for motivation-aware coaching.

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
