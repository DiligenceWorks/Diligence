# Fitness Rewards

Personal fitness web app with a points-based behavioral economy. Earn points through fitness activities, spend them on real-world rewards.

## Stack
- **Backend**: FastAPI + PostgreSQL + SQLAlchemy (async)
- **Frontend**: React + Vite
- **Deployment**: Docker Compose via Coolify

## Quick Start (Development)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Deploy (Production)

```bash
cp .env.example .env
# Edit .env with real secrets
docker compose up -d --build
```

## Features
- Science-based onboarding (PAR-Q+, TTM Stages of Change, BREQ-2)
- Points economy with configurable earning rules and rewards
- Daily gate: earn your daily minimum before unlocking rewards
- Weekly targets with reset
- Strava + Polar integration (OAuth 2.0)
- Open Food Facts barcode scanning for food logging
- Curated external fitness resources (Darebee, StrongLifts, YouTube)
- 90-day program commitment tracking
- Mobile-first PWA design
