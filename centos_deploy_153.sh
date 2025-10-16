#!/bin/bash

# CentOS-Specific Deployment Script for 10.0.0.153
# Optimized for CentOS Linux release 7.9.2009 (Core)

set -e

# Configuration
PRODUCTION_DIR="/opt/netdata-dashboard"
GITHUB_REPO_URL="https://github.com/BarunKrMishra/netdata-dashboard.git"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Deploying Netdata Dashboard on CentOS 7.9${NC}"
echo "=============================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run as root (use sudo)${NC}"
    exit 1
fi

# Update system packages
echo -e "${YELLOW}📦 Updating CentOS packages...${NC}"
yum update -y

# Install EPEL repository (for additional packages)
echo -e "${YELLOW}📦 Installing EPEL repository...${NC}"
yum install -y epel-release

# Install Docker if not installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}🐳 Installing Docker CE on CentOS...${NC}"
    
    # Install required packages
    yum install -y yum-utils device-mapper-persistent-data lvm2
    
    # Add Docker CE repository
    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    
    # Install Docker CE
    yum install -y docker-ce docker-ce-cli containerd.io
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    echo -e "${GREEN}✅ Docker CE installed successfully${NC}"
else
    echo -e "${GREEN}✅ Docker is already installed${NC}"
fi

# Install Docker Compose if not installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}🐳 Installing Docker Compose...${NC}"
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Create symlink for easier access
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    echo -e "${GREEN}✅ Docker Compose installed successfully${NC}"
else
    echo -e "${GREEN}✅ Docker Compose is already installed${NC}"
fi

# Install Git if not installed
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}📥 Installing Git...${NC}"
    yum install -y git
    echo -e "${GREEN}✅ Git installed successfully${NC}"
else
    echo -e "${GREEN}✅ Git is already installed${NC}"
fi

# Install curl if not installed (for health checks)
if ! command -v curl &> /dev/null; then
    echo -e "${YELLOW}📥 Installing curl...${NC}"
    yum install -y curl
    echo -e "${GREEN}✅ curl installed successfully${NC}"
else
    echo -e "${GREEN}✅ curl is already installed${NC}"
fi

# Create project directory
echo -e "${YELLOW}📁 Setting up project directory...${NC}"
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

# Clean up old images (optional)
echo -e "${YELLOW}🧹 Cleaning up old Docker images...${NC}"
docker system prune -f || true

# Build and start
echo -e "${YELLOW}🔨 Building and starting application...${NC}"
docker-compose up -d --build

# Wait for startup
echo -e "${YELLOW}⏳ Waiting for application to start...${NC}"
sleep 20

# Check health
echo -e "${YELLOW}🔍 Checking application health...${NC}"
if curl -f http://localhost:5001/api/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo ""
    echo -e "${BLUE}📊 Dashboard: http://$(hostname -I | awk '{print $1}'):5001${NC}"
    echo -e "${BLUE}🏥 Health: http://$(hostname -I | awk '{print $1}'):5001/api/health${NC}"
    echo -e "${BLUE}📈 Metrics: http://$(hostname -I | awk '{print $1}'):5001/api/metrics${NC}"
    echo ""
    echo -e "${YELLOW}📋 Management Commands:${NC}"
    echo -e "  View logs:     docker-compose logs -f"
    echo -e "  Stop app:      docker-compose down"
    echo -e "  Restart app:   docker-compose restart"
    echo -e "  Update app:    git pull && docker-compose up -d --build"
else
    echo -e "${RED}❌ Deployment failed. Checking logs...${NC}"
    docker-compose logs --tail=50
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Netdata Dashboard is now running on CentOS!${NC}"
