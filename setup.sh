#!/bin/bash
set -e
echo ""
echo "  Diligence Setup"
echo ""

# Detect install mode
if command -v docker compose &> /dev/null && [ -f docker-compose.yml ]; then
    MODE="docker"
else
    MODE="local"
fi

# Generate secrets
SECRET=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
TOKEN=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")

if [ "$MODE" = "docker" ]; then
    echo "  Mode: Docker (PostgreSQL)"
    echo ""

    if [ -f .env ]; then
        echo "  .env already exists. Delete it first to regenerate."
        exit 1
    fi

    cp .env.example .env
    sed -i.bak "s/^SECRET_KEY=.*/SECRET_KEY=${SECRET}/" .env
    sed -i.bak "s/^API_TOKEN=.*/API_TOKEN=${TOKEN}/" .env
    sed -i.bak "s|^DATABASE_URL=.*|DATABASE_URL=postgresql+asyncpg://fitness@fitness-db:5432/fitness_rewards|" .env
    sed -i.bak "s|^BASE_URL=.*|BASE_URL=http://localhost|" .env
    rm -f .env.bak

    echo "  .env created"
    echo ""
    echo "  Next steps:"
    echo "    docker compose up -d"
    echo "    Open http://localhost"
    echo ""
    echo "  MCP agent connection:"
    echo "    URL: http://localhost:3001/sse"
    echo "    Header: Authorization: Bearer ${TOKEN}"

else
    echo "  Mode: Local (SQLite)"
    echo ""

    DATA_DIR="${HOME}/.diligence"
    mkdir -p "$DATA_DIR"
    ENV_FILE="${DATA_DIR}/.env"

    if [ -f "$ENV_FILE" ]; then
        echo "  Config already exists at ${ENV_FILE}"
        echo "  Delete it to regenerate."
        exit 1
    fi

    cat > "$ENV_FILE" << EOF
SECRET_KEY=${SECRET}
API_TOKEN=${TOKEN}
BASE_URL=http://localhost:8000
DATA_DIR=${DATA_DIR}
EOF

    echo "  Config created at ${ENV_FILE}"
    echo ""
    echo "  Next steps:"
    echo "    pip install ."
    echo "    diligence"
    echo ""
    echo "  Or run directly:"
    echo "    python -m diligence"
    echo ""
    echo "  Data stored in: ${DATA_DIR}"
    echo ""
    echo "  MCP agent connection:"
    echo "    URL: http://localhost:3001/sse"
    echo "    Header: Authorization: Bearer ${TOKEN}"
fi

echo ""
