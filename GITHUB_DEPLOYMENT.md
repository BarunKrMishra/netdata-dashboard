# 🚀 GitHub Repository Setup & Production Deployment

## 📋 **Step 1: Create GitHub Repository**

1. **Go to GitHub.com** and create a new repository:
   - Repository name: `netdata-dashboard`
   - Description: `Real-time Netdata monitoring dashboard with three-level threshold alerting`
   - Make it **Public** (or Private if preferred)
   - **Don't** initialize with README (we already have one)

2. **Copy the repository URL** (e.g., `https://github.com/yourusername/netdata-dashboard.git`)

## 📤 **Step 2: Push to GitHub**

Run these commands in your project directory:

```bash
# Initialize git repository
git init

# Add all files
git add .

# Commit files
git commit -m "Initial commit: Netdata Dashboard with Docker support"

# Add remote origin (replace with your GitHub URL)
git remote add origin https://github.com/yourusername/netdata-dashboard.git

# Push to GitHub
git push -u origin main
```

## 🖥️ **Step 3: Deploy to Production Server (10.0.0.153)**

### **Option A: Using Deployment Script (Recommended)**

1. **Make script executable**:
   ```bash
   chmod +x deploy.sh
   ```

2. **Run deployment**:
   ```bash
   ./deploy.sh
   ```

### **Option B: Manual Deployment**

SSH into your production server and run:

```bash
# SSH to production server
ssh root@10.0.0.153

# Clone repository
git clone https://github.com/yourusername/netdata-dashboard.git
cd netdata-dashboard

# Install Docker (if not installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Configure servers (edit servers_config.json)
nano servers_config.json

# Deploy with Docker Compose
docker-compose up -d --build

# Check status
docker-compose ps
```

## 🔧 **Step 4: Configure Production Servers**

Edit `servers_config.json` on the production server:

```json
{
  "servers": {
    "server_180_35": {
      "ip": "10.40.180.35",
      "name": "Server 180.35",
      "enabled": true
    },
    "server_180_36": {
      "ip": "10.40.180.36",
      "name": "Server 180.36",
      "enabled": true
    },
    "server_180_6": {
      "ip": "10.40.180.6",
      "name": "Server 180.6",
      "enabled": true
    },
    "server_180_9": {
      "ip": "10.40.180.9",
      "name": "Server 180.9",
      "enabled": true
    },
    "server_180_37": {
      "ip": "10.40.180.37",
      "name": "Server 180.37",
      "enabled": true
    },
    "server_180_38": {
      "ip": "10.40.180.38",
      "name": "Server 180.38",
      "enabled": true
    }
  }
}
```

## 🌐 **Step 5: Access Dashboard**

- **Dashboard URL**: `http://10.0.0.153:5001`
- **Health Check**: `http://10.0.0.153:5001/api/health`

## 📊 **Step 6: Verify Deployment**

1. **Check container status**:
   ```bash
   docker-compose ps
   ```

2. **View logs**:
   ```bash
   docker-compose logs -f
   ```

3. **Test health endpoint**:
   ```bash
   curl http://10.0.0.153:5001/api/health
   ```

4. **Open dashboard** in browser: `http://10.0.0.153:5001`

## 🔄 **Step 7: Updates & Maintenance**

### **Update Application**:
```bash
# On production server
cd /opt/netdata-dashboard
git pull
docker-compose up -d --build
```

### **View Logs**:
```bash
docker-compose logs -f
```

### **Restart Service**:
```bash
docker-compose restart
```

### **Stop Service**:
```bash
docker-compose down
```

## 🚨 **Troubleshooting**

### **Container Won't Start**:
```bash
# Check logs
docker-compose logs

# Check Docker status
systemctl status docker

# Restart Docker
systemctl restart docker
```

### **Port Already in Use**:
```bash
# Check what's using port 5001
netstat -tulpn | grep 5001

# Kill process if needed
kill -9 <PID>
```

### **No Data Showing**:
- Check server IPs in `servers_config.json`
- Verify Netdata servers are accessible from production server
- Check firewall rules

## 📝 **Production Commands Reference**

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# Update and rebuild
git pull && docker-compose up -d --build

# Check container status
docker-compose ps

# Health check
curl http://localhost:5001/api/health
```

---

**🎉 Your Netdata Dashboard is now deployed and ready for production monitoring!**
