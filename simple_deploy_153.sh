#!/bin/bash

# Simple Deployment Script for 10.0.0.153 Server
# Run this script directly on the production server

set -e

# Configuration
PRODUCTION_DIR="/opt/netdata-dashboard"
GITHUB_REPO_URL="https://github.com/BarunKrMishra/netdata-dashboard.git"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Deploying Netdata Dashboard${NC}"
echo "================================"

# Update system packages
echo -e "${YELLOW}📦 Updating system packages...${NC}"
yum update -y

# Install Docker if not installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}🐳 Installing Docker...${NC}"
    yum install -y docker
    systemctl start docker
    systemctl enable docker
fi

# Install Docker Compose if not installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}🐳 Installing Docker Compose...${NC}"
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Install Git if not installed
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}📥 Installing Git...${NC}"
    yum install -y git
fi

# Create project directory
mkdir -p ${PRODUCTION_DIR}
cd ${PRODUCTION_DIR}

# Clone or update repository
if [ -d ".git" ]; then
    echo -e "${YELLOW}📥 Updating repository...${NC}"
    git pull origin main
else
    echo -e "${YELLOW}📥 Cloning repository...${NC}"
    git clone ${GITHUB_REPO_URL} .
fi

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose down || true

# Build and start
echo -e "${YELLOW}🔨 Building and starting application...${NC}"
docker-compose up -d --build

# Wait for startup
echo -e "${YELLOW}⏳ Waiting for application to start...${NC}"
sleep 15

# Check health
if curl -f http://localhost:5001/api/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo ""
    echo -e "${BLUE}📊 Dashboard: http://$(hostname -I | awk '{print $1}'):5001${NC}"
    echo -e "${BLUE}🏥 Health: http://$(hostname -I | awk '{print $1}'):5001/api/health${NC}"
else
    echo -e "${RED}❌ Deployment failed. Check logs:${NC}"
    docker-compose logs
fi
