# Diligence

Self-hosted fitness rewards platform with AI agent integration. Points-based behavioral economy: earn points through workouts and food logging, spend them on rewards you choose. Science-based onboarding. 14-tool MCP connector for AI agents. Your data stays on your machine.

**By [DiligenceWorks Pte. Ltd.](https://diligenceworks.online) — MIT License**

---

## Which install is right for you?

| | **pip install** | **Docker** |
|---|---|---|
| **Who it's for** | You want a fitness app on your laptop. No servers, no DevOps, no fuss. | You're self-hosting for a household, a team, or you want PostgreSQL and a production-grade setup. |
| **What you need** | Python 3.11+ | Docker and Docker Compose |
| **Database** | SQLite (zero config, file on disk) | PostgreSQL 16 (runs in a container) |
| **Runs as** | Single process on localhost | 4 containers behind nginx |
| **Setup time** | 2 minutes | 5 minutes |
| **Best for** | Personal use on a laptop or desktop | Always-on server, multiple users, backups |

---

## Install — Personal Laptop (pip)

**Prerequisites:** Python 3.11 or newer.

```bash
# Clone and install
git clone https://github.com/DiligenceWorks/Diligence.git
cd Diligence
pip install .

# Run
diligence
```

That's it. The app opens in your browser at `http://localhost:8000`. Your data lives in `~/.diligence/`.

On first run, Diligence generates a secret key and stores your config in `~/.diligence/.env`. The SQLite database is created automatically at `~/.diligence/data.db`.

### Options

```bash
diligence --port 9000          # Different port
diligence --no-browser         # Don't auto-open browser
diligence --data-dir /my/path  # Custom data directory
python -m diligence            # Alternative way to run
```

### Building the frontend from source

The pip package includes a pre-built frontend. If you want to modify the UI:

```bash
cd frontend
npm install
npm run build
cp -r dist/ ../diligence/frontend/
```

---

## Install — Server (Docker)

**Prerequisites:** Docker and Docker Compose.

```bash
git clone https://github.com/DiligenceWorks/Diligence.git
cd Diligence
./setup.sh                 # generates .env with secrets
docker compose up -d       # starts 4 containers
```

Open `http://localhost` (or your server's IP). Register your account — the first user gets admin.

### What's running

| Container | Role | Port |
|-----------|------|------|
| frontend | React app + nginx reverse proxy | 80 |
| backend | FastAPI application server | 8000 (internal) |
| mcp-connector | MCP SSE server for AI agents | 3001 |
| fitness-db | PostgreSQL 16 | 5432 (internal) |

### Environment variables

Copy `.env.example` to `.env` (or let `setup.sh` do it). Key variables:

| Variable | Docker default | Description |
|----------|---------------|-------------|
| `SECRET_KEY` | (generated) | JWT signing key |
| `API_TOKEN` | (generated) | MCP connector auth token |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Database connection |
| `BASE_URL` | `http://localhost` | Public URL for OAuth callbacks |

---

## AI Agent Integration (MCP)

Diligence exposes 14 tools via the [Model Context Protocol](https://modelcontextprotocol.io). Any MCP-compatible AI agent (Claude, custom agents) can log workouts, track food, manage meal plans, and check progress.

### Connect your agent

**pip install path:**
```
URL:    http://localhost:8000/mcp
Token:  (shown on first run, or check ~/.diligence/.env)
```

**Docker path:**
```
URL:    http://localhost:3001/sse
Token:  (in your .env file, API_TOKEN)
```

### Available tools

| Tool | What it does |
|------|-------------|
| `get_context()` | Full profile, motivation type, programs, rules, rewards |
| `get_today()` | Daily points, gate status, activities |
| `get_week()` | Weekly summary and target progress |
| `log_activity(...)` | Log a workout, earn points |
| `log_food(...)` | Log food with macros |
| `search_food(query)` | Search Open Food Facts + USDA (400K+ foods) |
| `get_program_schedule()` | Today's scheduled workout |
| `redeem_reward(name)` | Spend points on a reward |
| `load_meal_plan(...)` | Create a meal plan |
| `get_meal_plan()` | View today's meals |
| `update_meal_compliance(...)` | Mark meals as followed/skipped |
| `get_plan_progress()` | Compliance stats |
| `configure_integration(...)` | Store encrypted credentials |
| `get_integration_status()` | Check provider connections |

See `AGENT_GUIDE.md` for behavioral guidelines including BREQ-2 tone calibration.

---

## What's inside

### Science-based onboarding
- **PAR-Q+** physical activity readiness screening
- **TTM** (Transtheoretical Model) stage assessment
- **BREQ-2** motivation profiling — the app adapts its tone to your motivation type

### Points engine
- Earn points for workouts, food logging, fasting, meal compliance
- Daily gate (minimum to unlock rewards)
- Weekly targets with reset
- Configurable reward shop — you decide what points are worth

### Integrations
Strava and Polar sync are built in. The provider registry supports Garmin, Fitbit, Withings, WHOOP, and Oura (OAuth flows ready, need provider approval). USDA FoodData Central for nutrition lookup.

---

## Project structure

```
Diligence/
  pyproject.toml              # pip install config
  docker-compose.yml          # Docker config
  diligence/                  # Python package
    cli.py                    # Entry point for pip path
    main.py                   # FastAPI app
    config.py                 # Settings (auto-detects SQLite vs PostgreSQL)
    database.py               # Dialect-agnostic database layer
    models/                   # 15 SQLAlchemy models
    routers/                  # 12 API routers
    services/                 # Points engine, food lookup, sync, crypto
    utils/                    # Auth helpers
    mcp/                      # MCP connector (14 tools)
    frontend/                 # Pre-built React app (pip path serves this)
  frontend/                   # React source code
  backend/                    # Dockerfile + requirements.txt (Docker path)
  mcp-connector/              # MCP Dockerfile (Docker path)
```

---

## Development

```bash
# Clone
git clone https://github.com/DiligenceWorks/Diligence.git
cd Diligence

# Backend
pip install -e ".[dev]"
diligence --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Data and privacy

Your data never leaves your machine. There is no telemetry, no analytics, no cloud sync. The database is a single file (`~/.diligence/data.db` for pip, a Docker volume for Docker). Back it up however you back up your files.

Integration credentials (Strava, Polar, etc.) are encrypted at rest using Fernet with HKDF key derivation from your SECRET_KEY.

---

## License

MIT. See `LICENSE`.

Built by [DiligenceWorks Pte. Ltd.](https://diligenceworks.online)
