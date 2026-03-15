FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hardcode DB connection - trust auth, no password
# This ensures correct connection regardless of Coolify env var handling
ENV DATABASE_URL=postgresql+asyncpg://fitness@db:5432/fitness_rewards
ENV SECRET_KEY=8915f64daf616b1b1ea5cdc8242ec924adf263c045bef378d9cb880787ba4386
ENV STRAVA_CLIENT_ID=211907
ENV STRAVA_CLIENT_SECRET=d1e48251327a3760acd6dcf4129ec59350dc6b71
ENV POLAR_CLIENT_ID=13c4d547-4056-4b55-8412-a1cce84e887e
ENV POLAR_CLIENT_SECRET=29890119-2267-4a72-8888-e67ab0c0bf60
ENV BASE_URL=https://fitness.littlefake.com

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
