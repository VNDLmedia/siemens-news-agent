# News AI Agent - Quick Start Script
# This script helps you set up and start the News AI Agent

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  News AI Agent - Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Creating .env from env.example..." -ForegroundColor Yellow
    
    if (Test-Path "env.example") {
        Copy-Item "env.example" ".env"
        Write-Host "✅ Created .env file" -ForegroundColor Green
        Write-Host ""
        Write-Host "⚠️  IMPORTANT: Edit the .env file and add your credentials:" -ForegroundColor Yellow
        Write-Host "   - OPENAI_API_KEY" -ForegroundColor Yellow
        Write-Host "   - SMTP credentials" -ForegroundColor Yellow
        Write-Host "   - RECIPIENT_EMAIL" -ForegroundColor Yellow
        Write-Host ""
        
        $continue = Read-Host "Have you edited the .env file? (y/n)"
        if ($continue -ne "y") {
            Write-Host "Please edit .env first, then run this script again." -ForegroundColor Red
            exit
        }
    } else {
        Write-Host "❌ env.example not found!" -ForegroundColor Red
        exit
    }
}

Write-Host "✅ .env file found" -ForegroundColor Green
Write-Host ""

# Check if Docker is running
Write-Host "🔍 Checking Docker..." -ForegroundColor Cyan
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "🚀 Starting containers..." -ForegroundColor Cyan
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  ✅ News AI Agent is running!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 n8n Dashboard: http://localhost:5678" -ForegroundColor Cyan
    Write-Host "🗄️  PostgreSQL: localhost:5432" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Open http://localhost:5678 in your browser" -ForegroundColor White
    Write-Host "2. Login with your N8N_USER and N8N_PASSWORD from .env" -ForegroundColor White
    Write-Host "3. Set up credentials (PostgreSQL, OpenAI, SMTP)" -ForegroundColor White
    Write-Host "4. Import the 3 workflow files from workflows/ folder" -ForegroundColor White
    Write-Host ""
    Write-Host "📖 Full instructions: See README.md" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Useful commands:" -ForegroundColor Yellow
    Write-Host "  - View logs:    docker-compose logs -f" -ForegroundColor White
    Write-Host "  - Stop:         docker-compose down" -ForegroundColor White
    Write-Host "  - Restart:      docker-compose restart" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ Failed to start containers" -ForegroundColor Red
    Write-Host "Check the error messages above." -ForegroundColor Red
    Write-Host ""
}
