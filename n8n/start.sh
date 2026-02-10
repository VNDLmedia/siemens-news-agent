#!/bin/bash

# News AI Agent - Quick Start Script
# This script helps you set up and start the News AI Agent

echo "========================================"
echo "  News AI Agent - Quick Start"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo ""
    echo "Creating .env from env.example..."
    
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ Created .env file"
        echo ""
        echo "⚠️  IMPORTANT: Edit the .env file and add your credentials:"
        echo "   - OPENAI_API_KEY"
        echo "   - SMTP credentials"
        echo "   - RECIPIENT_EMAIL"
        echo ""
        
        read -p "Have you edited the .env file? (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Please edit .env first, then run this script again."
            exit 1
        fi
    else
        echo "❌ env.example not found!"
        exit 1
    fi
fi

echo "✅ .env file found"
echo ""

# Check if Docker is running
echo "🔍 Checking Docker..."
if ! docker version > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Start containers
echo "🚀 Starting containers..."
docker-compose up -d

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "  ✅ News AI Agent is running!"
    echo "========================================"
    echo ""
    echo "📊 n8n Dashboard: http://localhost:5678"
    echo "🗄️  PostgreSQL: localhost:5432"
    echo ""
    echo "Next steps:"
    echo "1. Open http://localhost:5678 in your browser"
    echo "2. Login with your N8N_USER and N8N_PASSWORD from .env"
    echo "3. Set up credentials (PostgreSQL, OpenAI, SMTP)"
    echo "4. Import the 3 workflow files from workflows/ folder"
    echo ""
    echo "📖 Full instructions: See README.md"
    echo ""
    echo "Useful commands:"
    echo "  - View logs:    docker-compose logs -f"
    echo "  - Stop:         docker-compose down"
    echo "  - Restart:      docker-compose restart"
    echo ""
else
    echo ""
    echo "❌ Failed to start containers"
    echo "Check the error messages above."
    echo ""
fi
