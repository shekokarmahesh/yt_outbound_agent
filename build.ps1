# Ahoum Agent Docker Build Script for Windows

Write-Host "🐳 Building Ahoum Facilitator Onboarding Agent Docker Image..." -ForegroundColor Cyan

# Check if .env.local exists
if (-not (Test-Path ".env.local")) {
    Write-Host "❌ Error: .env.local file not found!" -ForegroundColor Red
    Write-Host "📝 Please copy .env.production.example to .env.local and fill in your credentials:" -ForegroundColor Yellow
    Write-Host "   Copy-Item .env.production.example .env.local" -ForegroundColor White
    Write-Host "   # Then edit .env.local with your actual values" -ForegroundColor Gray
    exit 1
}

# Check if outbound-trunk.json exists
if (-not (Test-Path "outbound-trunk.json")) {
    Write-Host "⚠️  Warning: outbound-trunk.json not found. Make sure you have configured your SIP trunk." -ForegroundColor Yellow
}

# Build the Docker image
Write-Host "🔨 Building Docker image..." -ForegroundColor Green
docker-compose build

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Build completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 To start the agent:" -ForegroundColor Cyan
    Write-Host "   docker-compose up -d" -ForegroundColor White
    Write-Host ""
    Write-Host "📊 To view logs:" -ForegroundColor Cyan
    Write-Host "   docker-compose logs -f" -ForegroundColor White
    Write-Host ""
    Write-Host "🛑 To stop the agent:" -ForegroundColor Cyan
    Write-Host "   docker-compose down" -ForegroundColor White
    Write-Host ""
    Write-Host "📞 To make a call (after starting):" -ForegroundColor Cyan
    Write-Host "   lk dispatch create --new-room --agent-name ahoum-facilitator-onboarding --metadata '+1234567890'" -ForegroundColor White
} else {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}
