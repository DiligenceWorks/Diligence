#!/bin/bash
echo "💪 Diligence — Setup"

if [ -f .env ]; then
  echo ".env already exists. Delete it first to regenerate."
  exit 1
fi

SECRET=$(openssl rand -hex 32)
cp .env.example .env
sed -i "s/^SECRET_KEY=.*/SECRET_KEY=${SECRET}/" .env

echo "✅ .env created with random SECRET_KEY"
echo ""
echo "Next steps:"
echo "  docker compose up -d"
echo "  Open http://localhost"
echo "  Register your account"
echo "  Configure integrations via Settings or your AI agent"
