# Diligence Setup — Windows
Write-Host ""
Write-Host "  Diligence Setup"
Write-Host ""

function New-RandomHex { -join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Max 256) }) }

$Secret = New-RandomHex
$Token = New-RandomHex

# Detect mode — Docker if docker compose is available and docker-compose.yml exists
$DockerAvailable = $false
try { docker compose version 2>$null | Out-Null; $DockerAvailable = $true } catch {}

if ($DockerAvailable -and (Test-Path "docker-compose.yml")) {
    Write-Host "  Mode: Docker (PostgreSQL)"
    Write-Host ""

    if (Test-Path ".env") {
        Write-Host "  .env already exists. Delete it first to regenerate."
        exit 1
    }

    Copy-Item ".env.example" ".env"
    (Get-Content ".env") -replace '^SECRET_KEY=.*', "SECRET_KEY=$Secret" `
                         -replace '^API_TOKEN=.*', "API_TOKEN=$Token" `
                         -replace '^DATABASE_URL=.*', 'DATABASE_URL=postgresql+asyncpg://fitness@fitness-db:5432/fitness_rewards' `
                         -replace '^BASE_URL=.*', 'BASE_URL=http://localhost' |
        Set-Content ".env"

    Write-Host "  .env created"
    Write-Host ""
    Write-Host "  Next steps:"
    Write-Host "    docker compose up -d"
    Write-Host "    Open http://localhost"

} else {
    Write-Host "  Mode: Local (SQLite)"
    Write-Host ""

    $DataDir = Join-Path $env:USERPROFILE ".diligence"
    if (-not (Test-Path $DataDir)) { New-Item -ItemType Directory -Path $DataDir | Out-Null }
    $EnvFile = Join-Path $DataDir ".env"

    if (Test-Path $EnvFile) {
        Write-Host "  Config already exists at $EnvFile"
        Write-Host "  Delete it to regenerate."
        exit 1
    }

    @"
SECRET_KEY=$Secret
API_TOKEN=$Token
BASE_URL=http://localhost:8000
DATA_DIR=$DataDir
"@ | Set-Content $EnvFile

    Write-Host "  Config created at $EnvFile"
    Write-Host ""
    Write-Host "  Next steps:"
    Write-Host "    pip install ."
    Write-Host "    diligence"
    Write-Host ""
    Write-Host "  Data stored in: $DataDir"
}

Write-Host ""
Write-Host "  MCP agent connection:"
Write-Host "    URL: http://localhost:3001/sse"
Write-Host "    Header: Authorization: Bearer $Token"
Write-Host ""
