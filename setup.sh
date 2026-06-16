#!/bin/bash
echo "💪 Diligence — Setup"

if [ -f .env ]; then
  echo ".env already exists. Delete it first to regenerate."
  exit 1
fi

SECRET=$(openssl rand -hex 32)
TOKEN=$(openssl rand -hex 32)
cp .env.example .env
sed -i.bak "s/^SECRET_KEY=.*/SECRET_KEY=${SECRET}/" .env
sed -i.bak "s/^API_TOKEN=.*/API_TOKEN=${TOKEN}/" .env
rm -f .env.bak

echo "✅ .env created with random SECRET_KEY and API_TOKEN"
echo ""
echo "Next steps:"
echo "  docker compose up -d"
echo "  Open http://localhost"
echo "  Register your account"
echo "  Configure integrations via Settings or your AI agent"
echo ""
echo "MCP agent connection:"
echo "  URL: http://localhost:3001/sse"
echo "  Header: Authorization: Bearer ${TOKEN}"
