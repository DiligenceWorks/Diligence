# Contributing to Diligence

Thanks for your interest in contributing!

## How to contribute

1. **Open an issue** to discuss the change before starting work
2. **Fork the repo** and create a branch from `main`
3. **Test locally**: `docker compose up -d` and verify all 4 containers start healthy
4. **Submit a PR** with a clear description of what changed and why

## Development setup

```bash
git clone https://github.com/DiligenceWorks/Diligence.git
cd Diligence
./setup.sh          # Mac/Linux
docker compose up -d
```

Open http://localhost and register. First user gets admin automatically.

## Code style

- Backend: Python 3.11+, FastAPI, async/await, type hints
- Frontend: React with hooks, no class components
- CSS: use CSS variables from `index.css`, never hardcode colors

## Questions?

Open a GitHub Discussion or reach out at hello@diligenceworks.online.
