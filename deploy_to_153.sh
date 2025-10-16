#!/bin/bash

# Netdata Dashboard Deployment Script for 10.0.0.153
# This script deploys the dashboard using Docker on the production server

set -e  # Exit on any error

# Configuration
PRODUCTION_SERVER="10.0.0.153"
PRODUCTION_USER="root"  # Change as needed
PRODUCTION_DIR="/opt/netdata-dashboard"
GITHUB_REPO_URL="https://github.com/BarunKrMishra/netdata-dashboard.git"
DOCKER_COMPOSE_FILE="docker-compose.yml"
CONTAINER_NAME="netdata-dashboard"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Netdata Dashboard Deployment to ${PRODUCTION_SERVER}${NC}"
echo "=================================================="

# Function to run commands on remote server
run_remote() {
    ssh ${PRODUCTION_USER}@${PRODUCTION_SERVER} "$@"
}

# Function to check if command exists on remote server
check_remote_command() {
    run_remote "command -v $1 >/dev/null 2>&1"
}

echo -e "${YELLOW}📋 Checking prerequisites on ${PRODUCTION_SERVER}...${NC}"

# Check if Docker is installed
if ! check_remote_command docker; then
    echo -e "${RED}❌ Docker is not installed on ${PRODUCTION_SERVER}${NC}"
    echo -e "${YELLOW}Installing Docker...${NC}"
    run_remote "yum update -y && yum install -y docker"
    run_remote "systemctl start docker && systemctl enable docker"
    echo -e "${GREEN}✅ Docker installed successfully${NC}"
else
    echo -e "${GREEN}✅ Docker is already installed${NC}"
fi

# Check if Docker Compose is installed
if ! check_remote_command docker-compose; then
    echo -e "${RED}❌ Docker Compose is not installed on ${PRODUCTION_SERVER}${NC}"
    echo -e "${YELLOW}Installing Docker Compose...${NC}"
    run_remote "curl -L \"https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
    run_remote "chmod +x /usr/local/bin/docker-compose"
    echo -e "${GREEN}✅ Docker Compose installed successfully${NC}"
else
    echo -e "${GREEN}✅ Docker Compose is already installed${NC}"
fi

# Check if Git is installed
if ! check_remote_command git; then
    echo -e "${RED}❌ Git is not installed on ${PRODUCTION_SERVER}${NC}"
    echo -e "${YELLOW}Installing Git...${NC}"
    run_remote "yum install -y git"
    echo -e "${GREEN}✅ Git installed successfully${NC}"
else
    echo -e "${GREEN}✅ Git is already installed${NC}"
fi

echo -e "${YELLOW}📁 Setting up project directory...${NC}"

# Create project directory
run_remote "mkdir -p ${PRODUCTION_DIR}"

# Stop existing container if running
echo -e "${YELLOW}🛑 Stopping existing container...${NC}"
run_remote "cd ${PRODUCTION_DIR} && docker-compose down || true"

# Clone or update repository
echo -e "${YELLOW}📥 Cloning/updating repository...${NC}"
if run_remote "test -d ${PRODUCTION_DIR}/.git"; then
    echo -e "${BLUE}Updating existing repository...${NC}"
    run_remote "cd ${PRODUCTION_DIR} && git pull origin main"
else
    echo -e "${BLUE}Cloning repository...${NC}"
    run_remote "cd ${PRODUCTION_DIR} && git clone ${GITHUB_REPO_URL} ."
fi

# Build and start the application
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
run_remote "cd ${PRODUCTION_DIR} && docker-compose build --no-cache"

echo -e "${YELLOW}🚀 Starting the application...${NC}"
run_remote "cd ${PRODUCTION_DIR} && docker-compose up -d"

# Wait for the application to start
echo -e "${YELLOW}⏳ Waiting for application to start...${NC}"
sleep 10

# Check if the application is running
echo -e "${YELLOW}🔍 Checking application status...${NC}"
if run_remote "curl -f http://localhost:5001/api/health >/dev/null 2>&1"; then
    echo -e "${GREEN}✅ Application is running successfully!${NC}"
else
    echo -e "${RED}❌ Application failed to start${NC}"
    echo -e "${YELLOW}Checking logs...${NC}"
    run_remote "cd ${PRODUCTION_DIR} && docker-compose logs"
    exit 1
fi

# Display deployment information
echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo "=================================================="
echo -e "${BLUE}📊 Dashboard URL:${NC} http://${PRODUCTION_SERVER}:5001"
echo -e "${BLUE}🏥 Health Check:${NC} http://${PRODUCTION_SERVER}:5001/api/health"
echo -e "${BLUE}📈 Metrics API:${NC} http://${PRODUCTION_SERVER}:5001/api/metrics"
echo ""
echo -e "${YELLOW}📋 Useful Commands:${NC}"
echo -e "  View logs:     ssh ${PRODUCTION_USER}@${PRODUCTION_SERVER} 'cd ${PRODUCTION_DIR} && docker-compose logs -f'"
echo -e "  Stop app:      ssh ${PRODUCTION_USER}@${PRODUCTION_SERVER} 'cd ${PRODUCTION_DIR} && docker-compose down'"
echo -e "  Restart app:   ssh ${PRODUCTION_USER}@${PRODUCTION_SERVER} 'cd ${PRODUCTION_DIR} && docker-compose restart'"
echo -e "  Update app:    ssh ${PRODUCTION_USER}@${PRODUCTION_SERVER} 'cd ${PRODUCTION_DIR} && git pull && docker-compose up -d --build'"
echo ""
echo -e "${GREEN}🚀 Your Netdata Dashboard is now live!${NC}"
