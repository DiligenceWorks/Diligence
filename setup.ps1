# Diligence — Windows Setup
# Generate API_TOKEN for MCP connector auth
$apiToken = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
(Get-Content .env) -replace '^API_TOKEN=.*', "API_TOKEN=$apiToken" | Set-Content .env

Write-Host "`n`e[36m💪 Diligence — Setup`e[0m`n"

if (Test-Path .env) {
    Write-Host "`e[33m.env already exists. Delete it first to regenerate.`e[0m"
    exit 1
}

# Generate random SECRET_KEY (64 hex chars)
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
$secret = ($bytes | ForEach-Object { $_.ToString("x2") }) -join ""

# Create .env from template
Copy-Item .env.example .env
(Get-Content .env) -replace "^SECRET_KEY=.*", "SECRET_KEY=$secret" | Set-Content .env

Write-Host "`e[32m✅ .env created with random SECRET_KEY`e[0m"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  docker compose up -d"
Write-Host "  Open http://localhost"
Write-Host "  Register your account"
Write-Host "  Configure integrations via Settings or your AI agent"
Write-Host ""
