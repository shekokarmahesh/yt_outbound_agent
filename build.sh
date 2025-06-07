#!/bin/bash

# Ahoum Agent Docker Build Script

set -e

echo "🐳 Building Ahoum Facilitator Onboarding Agent Docker Image..."

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo "❌ Error: .env.local file not found!"
    echo "📝 Please copy .env.production.example to .env.local and fill in your credentials:"
    echo "   cp .env.production.example .env.local"
    echo "   # Then edit .env.local with your actual values"
    exit 1
fi

# Check if outbound-trunk.json exists
if [ ! -f "outbound-trunk.json" ]; then
    echo "⚠️  Warning: outbound-trunk.json not found. Make sure you have configured your SIP trunk."
fi

# Build the Docker image
echo "🔨 Building Docker image..."
docker-compose build

echo "✅ Build completed successfully!"
echo ""
echo "🚀 To start the agent:"
echo "   docker-compose up -d"
echo ""
echo "📊 To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 To stop the agent:"
echo "   docker-compose down"
echo ""
echo "📞 To make a call (after starting):"
echo "   lk dispatch create --new-room --agent-name ahoum-facilitator-onboarding --metadata '+1234567890'"
