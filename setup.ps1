# Diligence — Windows Setup

Write-Host "`n`e[36m💪 Diligence — Setup`e[0m`n"

if (Test-Path .env) {
    Write-Host "`e[33m.env already exists. Delete it first to regenerate.`e[0m"
    exit 1
}

# Generate random SECRET_KEY (64 hex chars)
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
$secret = ($bytes | ForEach-Object { $_.ToString("x2") }) -join ""

# Generate random API_TOKEN (32 alphanumeric chars)
$apiToken = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# Create .env from template and replace both keys
Copy-Item .env.example .env
(Get-Content .env) -replace "^SECRET_KEY=.*", "SECRET_KEY=$secret" -replace "^API_TOKEN=.*", "API_TOKEN=$apiToken" | Set-Content .env

Write-Host "`e[32m✅ .env created with random SECRET_KEY and API_TOKEN`e[0m"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  docker compose up -d"
Write-Host "  Open http://localhost"
Write-Host "  Register your account"
Write-Host "  Configure integrations via Settings or your AI agent"
Write-Host ""
Write-Host "MCP agent connection:"
Write-Host "  URL: http://localhost:3001/sse"
Write-Host "  Header: Authorization: Bearer $apiToken"
