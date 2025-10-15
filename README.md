# 📊 Netdata Dashboard

A real-time monitoring dashboard for Netdata servers with three-level threshold alerting system.

## 🚀 Features

- **Real-time WebSocket streaming** from multiple Netdata servers
- **Three-level threshold system** (Alert/Storage/Buzzer)
- **Server-specific data storage** and historical viewing
- **Google Chat notifications** for threshold crossings
- **Buzzer sound alerts** for critical thresholds
- **Modern responsive UI** with glassmorphism design
- **Server management** through web interface

## 📊 Thresholds

### MySQL Active Connections
- **Alert**: 400 (color change + Google Chat)
- **Storage**: 800 (data storage)
- **Buzzer**: 1000 (sound alert)

### System Load
- **Alert**: 10 (color change + Google Chat)
- **Storage**: 20 (data storage)
- **Buzzer**: 50 (sound alert)

### MySQL Per Second Connections
- **Alert**: 1000 (color change + Google Chat)
- **Storage**: 1000 (data storage)
- **Buzzer**: 1000 (sound alert)

## 🐳 Docker Deployment

### Quick Start
```bash
# Clone repository
git clone <your-repo-url>
cd netdata-dashboard

# Configure servers
nano servers_config.json

# Run with Docker Compose
docker-compose up -d

# Check status
docker-compose ps
```

### Manual Docker Build
```bash
# Build image
docker build -t netdata-dashboard .

# Run container
docker run -d \
  --name netdata-dashboard \
  -p 5001:5001 \
  -v $(pwd)/servers_config.json:/app/servers_config.json:ro \
  netdata-dashboard
```

## ⚙️ Configuration

### Server Configuration (`servers_config.json`)
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
    }
  }
}
```

### Google Chat Webhook
Configure in `app.py`:
```python
GCHAT_WEBHOOK_URL = "your-webhook-url"
```

## 🌐 Access

- **Dashboard**: `http://your-server:5001`
- **Health Check**: `http://your-server:5001/api/health`
- **Metrics API**: `http://your-server:5001/api/metrics`

## 📝 API Endpoints

- `GET /` - Main dashboard
- `GET /api/health` - Health check
- `GET /api/metrics` - Current metrics
- `GET /api/servers` - Server list
- `POST /api/servers` - Add server
- `DELETE /api/servers/<server_id>` - Remove server
- `GET /api/metric-history/<server_id>/<metric_type>` - Historical data

## 🔧 Development

### Local Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

### Requirements
- Python 3.11+
- Flask
- Flask-SocketIO
- Requests
- Eventlet

## 📊 Monitoring

The dashboard automatically:
- Streams real-time data from Netdata servers
- Stores data when thresholds are crossed
- Sends Google Chat notifications
- Plays buzzer sounds for critical alerts
- Maintains server-specific historical data

## 🔒 Security

- Non-root user in Docker container
- Health checks for container monitoring
- Input validation for server management
- CORS configuration for web security

## 📈 Production Deployment

1. **Clone repository** on production server
2. **Configure servers** in `servers_config.json`
3. **Deploy with Docker Compose**:
   ```bash
   docker-compose up -d
   ```
4. **Monitor logs**:
   ```bash
   docker-compose logs -f
   ```

## 🚨 Troubleshooting

- **No data**: Check server IPs and Netdata accessibility
- **No notifications**: Verify Google Chat webhook URL
- **Container issues**: Check Docker logs and health status
- **Port conflicts**: Ensure port 5001 is available

---

**Built with ❤️ for Netdata monitoring**
