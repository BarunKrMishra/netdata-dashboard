# 🚀 Production Deployment Guide

## 📦 **Clean Production Package**

The project has been cleaned and contains only the essential files:

```
NETdata project/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── servers_config.json       # Server configuration
├── static/
│   └── buzzer_sound.wav     # Buzzer sound file
└── templates/
    └── dashboard.html       # Main dashboard UI
```

## 🔧 **Production Setup**

### **1. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **2. Configure Servers**
Edit `servers_config.json` to add your production servers:
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

### **3. Run Production Server**
```bash
python app.py
```

The dashboard will be available at: `http://your-server-ip:5001`

## ⚙️ **Production Configuration**

### **Thresholds (Hardcoded in app.py)**
- **MySQL Active Connections:**
  - Alert: 400 (color change + Google Chat)
  - Storage: 800 (data storage)
  - Buzzer: 1000 (sound alert)

- **System Load:**
  - Alert: 10 (color change + Google Chat)
  - Storage: 20 (data storage)
  - Buzzer: 50 (sound alert)

- **MySQL Per Second:**
  - Alert: 1000 (color change + Google Chat)
  - Storage: 1000 (data storage)
  - Buzzer: 1000 (sound alert)

### **Google Chat Webhook**
Configured in `app.py`:
```python
GCHAT_WEBHOOK_URL = "https://chat.googleapis.com/v1/spaces/AAQA-CHmNo8/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=muHJuBI-mncQJM7Z1fpnJSv1V3vTqzs"
```

## 🌐 **Features**

✅ **Real-time WebSocket streaming**  
✅ **Three-level threshold system**  
✅ **Server-specific data storage**  
✅ **Google Chat notifications**  
✅ **Buzzer sound alerts**  
✅ **Historical data viewing**  
✅ **Server management UI**  

## 📊 **Monitoring**

- **Dashboard URL**: `http://your-server-ip:5001`
- **Health Check**: `http://your-server-ip:5001/api/health`
- **Metrics API**: `http://your-server-ip:5001/api/metrics`

## 🔒 **Security Notes**

- Ensure firewall allows port 5001
- Consider using HTTPS in production
- Validate server IPs in `servers_config.json`
- Monitor Google Chat webhook usage

## 📝 **Maintenance**

- **Add Servers**: Edit `servers_config.json` and restart app
- **View Logs**: Check console output for threshold crossings
- **Historical Data**: Click metric cards to view stored data
- **Server Management**: Use dashboard UI to add/remove servers

## 🚨 **Troubleshooting**

1. **No data showing**: Check server IPs and Netdata accessibility
2. **No notifications**: Verify Google Chat webhook URL
3. **No buzzer sound**: Check `static/buzzer_sound.wav` file
4. **WebSocket issues**: Check firewall and port 5001

---

**Ready for Production! 🎉**
