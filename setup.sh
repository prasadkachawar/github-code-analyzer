#!/bin/bash

# Static Analysis MCP Server Setup Script
# This script sets up the MCP server for GitHub integration

set -e  # Exit on any error

echo "🚀 Setting up Static Analysis MCP Server..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose are installed${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example${NC}"
    cp .env.example .env
    echo -e "${YELLOW}� Please edit .env file with your actual credentials before proceeding${NC}"
    echo -e "${YELLOW}   Required variables:${NC}"
    echo "   - GITHUB_TOKEN (GitHub Personal Access Token)"
    echo "   - GITHUB_WEBHOOK_SECRET (Secret for webhook verification)"
    echo "   - ANTHROPIC_API_KEY or OPENAI_API_KEY (LLM API key)"
    echo "   - EMAIL_USER, EMAIL_PASSWORD, FROM_EMAIL (Email settings)"
    echo
    read -p "Press Enter after you've configured the .env file..."
fi

# Source environment variables
source .env

# Validate required environment variables
required_vars=("GITHUB_TOKEN" "GITHUB_WEBHOOK_SECRET")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo -e "${RED}❌ Missing required environment variables:${NC}"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    exit 1
fi

# Check if at least one LLM API key is provided
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ At least one LLM API key is required (ANTHROPIC_API_KEY or OPENAI_API_KEY)${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment variables validated${NC}"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p analysis_reports analysis_baselines temp_repos logs

# Build the Docker image
echo "🔨 Building Docker image..."
docker-compose build

# Start the services
echo "🚀 Starting MCP server..."
docker-compose up -d

# Wait for service to be healthy
echo "⏳ Waiting for service to be ready..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if docker-compose ps mcp-server | grep -q "healthy"; then
        echo -e "${GREEN}✅ MCP server is running and healthy!${NC}"
        break
    fi
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    echo -e "${RED}❌ Service failed to start within $timeout seconds${NC}"
    echo "Checking logs..."
    docker-compose logs mcp-server
    exit 1
fi

# Display status
echo
echo -e "${GREEN}🎉 Static Analysis MCP Server is now running!${NC}"
echo
echo "📊 Service Status:"
docker-compose ps

echo
echo "🔗 Service URLs:"
echo "   Webhook endpoint: http://localhost:5000/webhook"
echo "   Health check:    http://localhost:5000/health"

echo
echo "� Next Steps:"
echo "1. Configure your GitHub repository webhook:"
echo "   - URL: http://your-server-domain:5000/webhook"
echo "   - Content type: application/json"
echo "   - Secret: [your GITHUB_WEBHOOK_SECRET]"
echo "   - Events: Push, Pull requests"
echo
echo "2. Set up your LLM client to connect to this MCP server"
echo
echo "3. Monitor logs: docker-compose logs -f mcp-server"

# Offer to show logs
echo
read -p "Would you like to view the logs now? (y/N): " show_logs
if [[ $show_logs =~ ^[Yy]$ ]]; then
    docker-compose logs -f mcp-server
fi
