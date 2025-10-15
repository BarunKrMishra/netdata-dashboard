#!/bin/bash

# Netdata Dashboard Production Deployment Script
# For server: 10.0.0.153

echo "🚀 Deploying Netdata Dashboard to Production Server..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PRODUCTION_SERVER="10.0.0.153"
PRODUCTION_USER="root"  # Change as needed
PRODUCTION_DIR="/opt/netdata-dashboard"
DOCKER_COMPOSE_FILE="docker-compose.yml"
GITHUB_REPO_URL="https://github.com/BarunKrMishra/netdata-dashboard.git"

echo -e "${BLUE}📋 Deployment Configuration:${NC}"
echo "  Server: $PRODUCTION_SERVER"
echo "  User: $PRODUCTION_USER"
echo "  Directory: $PRODUCTION_DIR"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run command on production server
run_on_production() {
    ssh $PRODUCTION_USER@$PRODUCTION_SERVER "$1"
}

echo -e "${YELLOW}🔍 Checking production server prerequisites...${NC}"

# Check if Docker is installed
if ! run_on_production "command_exists docker"; then
    echo -e "${RED}❌ Docker not found on production server${NC}"
    echo -e "${YELLOW}Installing Docker...${NC}"
    run_on_production "curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
fi

# Check if Docker Compose is installed
if ! run_on_production "command_exists docker-compose"; then
    echo -e "${RED}❌ Docker Compose not found on production server${NC}"
    echo -e "${YELLOW}Installing Docker Compose...${NC}"
    run_on_production "curl -L \"https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose"
fi

echo -e "${GREEN}✅ Prerequisites check completed${NC}"

echo -e "${YELLOW}📦 Preparing deployment package...${NC}"

# Create deployment directory
mkdir -p deployment
cp -r app.py requirements.txt servers_config.json templates static Dockerfile docker-compose.yml README.md deployment/

echo -e "${GREEN}✅ Deployment package prepared${NC}"

echo -e "${YELLOW}🚀 Deploying to production server...${NC}"

# Create directory on production server
run_on_production "mkdir -p $PRODUCTION_DIR"

# Copy files to production server
echo -e "${BLUE}📤 Copying files to production server...${NC}"
scp -r deployment/* $PRODUCTION_USER@$PRODUCTION_SERVER:$PRODUCTION_DIR/

# Deploy on production server
echo -e "${BLUE}🐳 Building and starting Docker containers...${NC}"
run_on_production "cd $PRODUCTION_DIR && docker-compose down && docker-compose up -d --build"

# Wait for container to start
echo -e "${YELLOW}⏳ Waiting for container to start...${NC}"
sleep 10

# Check container status
echo -e "${BLUE}📊 Checking container status...${NC}"
run_on_production "cd $PRODUCTION_DIR && docker-compose ps"

# Health check
echo -e "${BLUE}🏥 Performing health check...${NC}"
if run_on_production "curl -f http://localhost:5001/api/health"; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo -e "${YELLOW}Checking container logs...${NC}"
    run_on_production "cd $PRODUCTION_DIR && docker-compose logs"
fi

# Cleanup
rm -rf deployment

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${BLUE}📊 Dashboard available at: http://$PRODUCTION_SERVER:5001${NC}"
echo -e "${BLUE}🏥 Health check: http://$PRODUCTION_SERVER:5001/api/health${NC}"

echo -e "${YELLOW}📝 Useful commands for production server:${NC}"
echo "  View logs: docker-compose logs -f"
echo "  Restart: docker-compose restart"
echo "  Stop: docker-compose down"
echo "  Update: git pull && docker-compose up -d --build"
