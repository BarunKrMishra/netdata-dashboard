# Netdata Dashboard - Complete Project Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Data Calculation Methods](#data-calculation-methods)
3. [Architecture & Technology Stack](#architecture--technology-stack)
4. [Deployment Guide](#deployment-guide)
5. [API Endpoints](#api-endpoints)
6. [Monitoring Features](#monitoring-features)
7. [Demo Presentation Guide](#demo-presentation-guide)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

### **What is this Dashboard?**
A real-time monitoring dashboard that fetches metrics from multiple Netdata servers and displays them in a unified, responsive interface with:
- **Real-time data streaming** via WebSockets
- **Threshold-based alerting** with color changes and notifications
- **Server management** (add/remove servers dynamically)
- **Historical data storage** for threshold violations
- **Audio alerts** for critical thresholds

### **Key Features**
- ✅ **Real-time Monitoring**: Live data updates every 0.5 seconds
- ✅ **Multi-Server Support**: Monitor multiple Netdata servers simultaneously
- ✅ **Three-Level Alerting**: Color changes, data storage, and audio alerts
- ✅ **Responsive Design**: Works on mobile, tablet, laptop, TV, projector
- ✅ **Server Management**: Add/remove servers via UI
- ✅ **Historical Data**: Click metrics to view stored threshold violations
- ✅ **Google Chat Integration**: Automated notifications
- ✅ **Docker Deployment**: Containerized for easy deployment

---

## 📊 Data Calculation Methods

### **How We Calculate Values (Matching Netdata UI Exactly)**

#### **1. MySQL Active Connections**
```python
# API Call Parameters
url = f"{server_url}/api/v1/data?chart=mysql_local.connections_active&after=-1&before=0&points=1&group=average"

# Calculation Method
- after=-1: Last 1 second window
- before=0: Ending now
- points=1: Single latest data point
- group=average: Average grouping method
- Result: Latest single point value (exactly as Netdata UI shows)
```

#### **2. System Load**
```python
# API Call Parameters
url = f"{server_url}/api/v1/data?chart=system.load&after=-1&before=0&points=1&group=average"

# Calculation Method
- Fetches load1, load5, load15 values
- Uses latest single point (not averaged)
- Matches Netdata UI display exactly
- Shows current system load state
```

#### **3. MySQL Per Second Connections**
```python
# API Call Parameters
url = f"{server_url}/api/v1/data?chart=mysql_local.connections&after=-1&before=0&points=1&group=average"

# Calculation Method
- Rate of new connections per second
- Latest single point value
- Real-time connection rate monitoring
```

### **Why This Method Works**
1. **Exact Netdata UI Match**: We use the same API parameters that Netdata UI uses
2. **Real-time Data**: `after=-1&before=0&points=1` ensures latest data
3. **No Averaging**: Single point gives immediate current state
4. **Consistent Timing**: All metrics use synchronized timestamps

---

## 🏗️ Architecture & Technology Stack

### **Backend (Python Flask)**
```
app.py
├── Flask Web Framework
├── Flask-SocketIO (WebSocket support)
├── Requests (API calls to Netdata)
├── Threading (Background data streaming)
└── JSON handling (Data processing)
```

### **Frontend (HTML/CSS/JavaScript)**
```
templates/dashboard.html
├── Responsive CSS Grid Layout
├── WebSocket Client (socket.io.js)
├── Real-time Data Updates
├── Server Management UI
├── Historical Data Modal
└── Audio Alert System
```

### **Data Flow**
```
Netdata Servers → Flask API → WebSocket → Frontend Dashboard
     ↓              ↓           ↓            ↓
  Raw Metrics → Processing → Streaming → Real-time Display
```

### **Deployment Stack**
```
Docker Container
├── Python 3.11-slim base image
├── Flask + Dependencies
├── Nginx (if needed)
└── Docker Compose orchestration
```

---

## 🚀 Deployment Guide

### **Prerequisites**
- CentOS 7.9+ server
- Docker & Docker Compose
- Git
- Network access to Netdata servers

### **Quick Deployment**
```bash
# 1. Clone repository
git clone https://github.com/BarunKrMishra/netdata-dashboard.git
cd netdata-dashboard

# 2. Deploy with Docker
docker-compose up -d --build

# 3. Access dashboard
http://YOUR_SERVER_IP:5001
```

### **Production Deployment**
```bash
# Use the CentOS-specific deployment script
chmod +x centos_deploy_153.sh
./centos_deploy_153.sh
```

---

## 🔌 API Endpoints

### **Main Endpoints**
- `GET /` - Dashboard UI
- `GET /api/health` - Health check
- `GET /api/metrics` - All server metrics
- `GET /api/servers` - Server list
- `POST /api/servers/add` - Add server
- `DELETE /api/servers/remove/<server_id>` - Remove server

### **WebSocket Events**
- `connect` - Client connection
- `metrics_update` - Real-time data stream
- `disconnect` - Client disconnection

### **Historical Data**
- `GET /api/metric-history/<server_id>/<metric_type>` - Server-specific history
- `GET /api/metric-history/<metric_type>` - All servers history
- `GET /api/metric-history` - Complete history

---

## 📈 Monitoring Features

### **Three-Level Alerting System**

#### **Level 1: Visual Alerts (Color Changes)**
- **MySQL Active Connections**: > 400 → Red background
- **System Load**: > 10 → Red background
- **MySQL Per Second**: > 1000 → Red background

#### **Level 2: Data Storage**
- **MySQL Active Connections**: > 800 → Store data with timestamp
- **System Load**: > 20 → Store data with timestamp
- **MySQL Per Second**: > 1000 → Store data with timestamp

#### **Level 3: Audio Alerts**
- **MySQL Active Connections**: > 1000 → Buzzer sound
- **System Load**: > 50 → Buzzer sound

### **Google Chat Integration**
```python
# Webhook URL configured
webhook_url = "https://chat.googleapis.com/v1/spaces/AAQA-CHmNo8/messages?key=..."

# Sends alerts when thresholds crossed
# Sends recovery messages when back to normal
```

---

## 🎤 Demo Presentation Guide

### **Opening (2 minutes)**
"Today I'll demonstrate our Netdata Dashboard - a real-time monitoring solution that provides unified visibility across multiple servers with intelligent alerting."

### **Key Demo Points**

#### **1. Real-time Data (1 minute)**
- Show live updating metrics
- Explain WebSocket streaming (0.5-second updates)
- Demonstrate data matches Netdata UI exactly

#### **2. Multi-Server Monitoring (1 minute)**
- Show multiple server cards
- Explain unified dashboard concept
- Demonstrate server management (add/remove)

#### **3. Intelligent Alerting (2 minutes)**
- **Visual**: Show color changes when thresholds crossed
- **Storage**: Click metric to show historical violations
- **Audio**: Demonstrate buzzer alerts
- **Notifications**: Show Google Chat integration

#### **4. Responsive Design (1 minute)**
- Show mobile/tablet compatibility
- Demonstrate touch-friendly interface
- Show TV/projector display capability

#### **5. Technical Architecture (2 minutes)**
- Explain data calculation methods
- Show API endpoints
- Demonstrate Docker deployment
- Explain WebSocket real-time streaming

### **Demo Script**
```
"Let me show you how this works:

1. We fetch data from Netdata servers using their API
2. Our calculation method matches Netdata UI exactly
3. Data streams in real-time via WebSockets
4. When thresholds are crossed, we get:
   - Visual alerts (red boxes)
   - Data storage for analysis
   - Audio alerts for critical issues
   - Google Chat notifications

The dashboard is fully responsive and can be deployed anywhere with Docker."
```

---

## 🔧 Troubleshooting

### **Common Issues**

#### **Container Won't Start**
```bash
# Check logs
docker-compose logs -f

# Common fixes
docker-compose down
docker system prune -f
docker-compose up -d --build
```

#### **No Data Showing**
```bash
# Check server connectivity
curl http://NETDATA_SERVER:19999/api/v1/info

# Check API endpoints
curl http://localhost:5001/api/health
curl http://localhost:5001/api/metrics
```

#### **WebSocket Issues**
```bash
# Check browser console for errors
# Verify port 5001 is accessible
# Check firewall settings
```

### **Performance Optimization**
- **Data Refresh**: 0.5 seconds (configurable)
- **Memory Usage**: ~100MB per container
- **CPU Usage**: ~5-10% per server monitored
- **Network**: Minimal bandwidth usage

---

## 📞 Support & Maintenance

### **Regular Maintenance**
- Monitor container health
- Check disk space for historical data
- Update server configurations as needed
- Review threshold settings

### **Scaling Considerations**
- Add more servers via UI
- Adjust refresh rates if needed
- Monitor resource usage
- Consider load balancing for high traffic

### **Security Notes**
- Dashboard runs on internal network
- No external dependencies required
- Docker container isolation
- Non-root user in container

---

## 🎯 Business Value

### **Benefits**
1. **Unified Monitoring**: Single dashboard for multiple servers
2. **Real-time Alerts**: Immediate notification of issues
3. **Historical Analysis**: Track patterns and trends
4. **Cost Effective**: Open-source solution
5. **Easy Deployment**: Docker-based deployment
6. **Scalable**: Add servers without code changes

### **ROI**
- **Reduced Downtime**: Faster issue detection
- **Improved Efficiency**: Centralized monitoring
- **Better Planning**: Historical data analysis
- **Lower Costs**: No licensing fees

---

*This documentation provides complete information for demo presentations and technical discussions about the Netdata Dashboard project.*
