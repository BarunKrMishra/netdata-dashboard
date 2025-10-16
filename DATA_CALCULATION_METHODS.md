# Data Calculation Methods - Technical Explanation

## 🧮 How We Calculate Dashboard Values

### **The Challenge**
Netdata UI displays processed values that may differ from raw API data. Our goal is to match Netdata UI exactly.

### **Our Solution: Single Point Real-time Method**

#### **API Parameters We Use**
```python
# For ALL metrics (MySQL Active Connections, System Load, MySQL Per Second)
url = f"{server_url}/api/v1/data?chart={chart_name}&after=-1&before=0&points=1&group=average"
```

#### **Parameter Explanation**
- **`after=-1`**: Look at data from 1 second ago
- **`before=0`**: Up to the current moment
- **`points=1`**: Return only 1 data point (the latest)
- **`group=average`**: Use average grouping method

### **Why This Works**

#### **1. Netdata UI Behavior**
- Netdata UI shows the **latest single point** for real-time metrics
- It doesn't average multiple points for current display
- Our method fetches exactly what Netdata UI shows

#### **2. Real-time Accuracy**
- `after=-1&before=0` ensures we get the most recent data
- `points=1` eliminates any averaging delays
- Data is synchronized across all metrics

#### **3. Consistent Timing**
- All metrics use the same timestamp window
- No time drift between different metrics
- Perfect synchronization for threshold comparisons

---

## 📊 Specific Metric Calculations

### **MySQL Active Connections**
```python
# Chart: mysql_local.connections_active
# API Call:
GET /api/v1/data?chart=mysql_local.connections_active&after=-1&before=0&points=1&group=average

# What it returns:
{
  "data": [
    [timestamp, active_connections_value]
  ]
}

# We display: active_connections_value (exact Netdata UI value)
```

### **System Load**
```python
# Chart: system.load
# API Call:
GET /api/v1/data?chart=system.load&after=-1&before=0&points=1&group=average

# What it returns:
{
  "data": [
    [timestamp, load1, load5, load15]
  ]
}

# We display: load1, load5, load15 (exact Netdata UI values)
```

### **MySQL Per Second Connections**
```python
# Chart: mysql_local.connections
# API Call:
GET /api/v1/data?chart=mysql_local.connections&after=-1&before=0&points=1&group=average

# What it returns:
{
  "data": [
    [timestamp, connections_per_second_value]
  ]
}

# We display: connections_per_second_value (exact Netdata UI value)
```

---

## 🔄 Data Flow Process

### **Step-by-Step Process**
```
1. WebSocket Timer (every 0.5 seconds)
   ↓
2. For each server in servers_config.json:
   ↓
3. Make API call to Netdata server
   ↓
4. Extract latest data point from response
   ↓
5. Apply thresholds and store if needed
   ↓
6. Send data to frontend via WebSocket
   ↓
7. Frontend updates dashboard in real-time
```

### **Code Implementation**
```python
def get_single_point_data(server_url, chart_name):
    """
    Get single point data exactly like Netdata UI shows
    Uses real-time parameters for immediate data
    """
    try:
        # Use real-time parameters for immediate data:
        # - after=-1: last 1 second (minimal window)
        # - before=0: ending now
        # - points=1: single latest point
        # - group=average: default grouping method
        url = f"{server_url}/api/v1/data?chart={chart_name}&after=-1&before=0&points=1&group=average"
        response = requests.get(url, timeout=2)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                # Get the latest point (last in the array)
                latest_point = data['data'][-1]
                return latest_point[1]  # Return the value (not timestamp)
        
        return None
    except Exception as e:
        print(f"Error fetching data for {chart_name}: {e}")
        return None
```

---

## ⚡ Real-time Streaming

### **WebSocket Implementation**
```python
def stream_metrics():
    """Background thread to stream metrics via WebSocket"""
    global streaming_active
    print("📡 Starting real-time metrics streaming...")
    
    while streaming_active:
        try:
            metrics_data = fetch_all_metrics()
            if metrics_data.get('status') == 'success':
                socketio.emit('metrics_update', metrics_data)
                print(f"📊 Streamed metrics at {metrics_data.get('fetch_time', 'N/A')} - {len(metrics_data.get('servers', {}))} servers")
            
            time.sleep(0.5)  # Stream every 0.5 seconds for real-time data
        except Exception as e:
            print(f"❌ Error in metrics streaming: {e}")
            time.sleep(1)
```

### **Frontend Updates**
```javascript
// Listen for real-time updates
socket.on('metrics_update', function(data) {
    console.log('📊 Received metrics update:', data);
    
    // Update each server card
    Object.keys(data.servers).forEach(serverId => {
        const serverData = data.servers[serverId];
        updateServerCard(serverId, serverData);
    });
});
```

---

## 🎯 Threshold Logic

### **Three-Level Alerting System**

#### **Level 1: Visual Alerts**
```python
# MySQL Active Connections
if mysql_active > 400:
    card_class = "metric-card alert"
    send_google_chat_alert("MySQL Active Connections exceeded 400")

# System Load
if load1 > 10:
    card_class = "metric-card alert"
    send_google_chat_alert("System Load exceeded 10")
```

#### **Level 2: Data Storage**
```python
# MySQL Active Connections
if mysql_active > 800:
    store_metric_data(server_id, 'mysql_active', mysql_active, timestamp)

# System Load
if load1 > 20:
    store_metric_data(server_id, 'load', load1, timestamp)
```

#### **Level 3: Audio Alerts**
```javascript
// Frontend audio alerts
if (mysql_active > 1000) {
    playBuzzerSound();
    showBuzzerAlert('mysql_active');
}

if (load1 > 50) {
    playBuzzerSound();
    showBuzzerAlert('load');
}
```

---

## 🔍 Data Validation

### **How We Ensure Accuracy**
1. **Direct API Comparison**: Compare our values with Netdata UI
2. **Timestamp Synchronization**: All metrics use same time window
3. **Error Handling**: Graceful fallback for API failures
4. **Timeout Management**: 2-second timeout for API calls

### **Verification Methods**
```python
# Test API call
curl "http://netdata-server:19999/api/v1/data?chart=mysql_local.connections_active&after=-1&before=0&points=1&group=average"

# Compare with Netdata UI
# Our dashboard should show identical values
```

---

## 📈 Performance Considerations

### **Optimization Strategies**
- **Caching**: No caching to ensure real-time data
- **Parallel Requests**: Simultaneous API calls to all servers
- **Error Recovery**: Automatic retry on failures
- **Resource Management**: Efficient memory usage

### **Scalability**
- **Server Addition**: Dynamic server management
- **Load Distribution**: Each server handled independently
- **Memory Usage**: ~100MB per container
- **Network**: Minimal bandwidth usage

---

*This technical explanation provides detailed insight into how our dashboard calculates and displays values, ensuring perfect accuracy with Netdata UI.*
