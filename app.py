from flask import Flask, render_template, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import threading
import time

load_dotenv()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Load servers configuration from external file
def load_servers_config():
    """Load server configuration from servers_config.json file"""
    try:
        with open('servers_config.json', 'r') as f:
            config = json.load(f)
            servers = {}
            for server_id, server_config in config['servers'].items():
                if server_config.get('enabled', True):  # Only load enabled servers
                    servers[server_id] = {
                        'name': server_config['name'],
                        'ip': server_config['ip'],
                        'port': server_config['port'],
                        'description': server_config['description']
                    }
            return servers
    except FileNotFoundError:
        print("⚠️ servers_config.json not found, using default configuration")
        return get_default_servers()
    except Exception as e:
        print(f"❌ Error loading servers_config.json: {e}")
        return get_default_servers()

def get_default_servers():
    """Default server configuration as fallback"""
    return {
        'server_180_35': {
            'name': 'Server 180.35',
            'ip': '10.40.180.35',
            'port': '19999',
            'description': 'Production Server 1'
        },
        'server_180_36': {
            'name': 'Server 180.36',
            'ip': '10.40.180.36',
            'port': '19999',
            'description': 'Production Server 2'
        },
        'server_180_6': {
            'name': 'Server 180.6',
            'ip': '10.40.180.6',
            'port': '19999',
            'description': 'Production Server 3'
        },
        'server_180_9': {
            'name': 'Server 180.9',
            'ip': '10.40.180.9',
            'port': '19999',
            'description': 'Production Server 4'
        },
        'server_180_37': {
            'name': 'Server 180.37',
            'ip': '10.40.180.37',
            'port': '19999',
            'description': 'Production Server 5'
        },
        'server_180_38': {
            'name': 'Server 180.38',
            'ip': '10.40.180.38',
            'port': '19999',
            'description': 'Production Server 6'
        }
    }

# Load servers configuration
NETDATA_SERVERS = load_servers_config()

# Google Chat Webhook
GCHAT_WEBHOOK_URL = "https://chat.googleapis.com/v1/spaces/AAQA-CHmNo8/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=muHJuBI-mncQJM7Z1fpnJSvLUYNACm8LSnv1V3vTqzs"

# Thresholds
THRESHOLDS = {
    'mysql_connections': 400,  # Adjusted for exact values (not multiplied by 1000)
    'system_load': 10.0,
    'cpu_usage': 80,
    'memory_usage': 85,
    'disk_usage': 90
}

# Alert state tracking
alert_states = {}

# Data storage for threshold crossings - organized by server
metric_history = {
    # Structure: {server_id: {metric_type: [data_entries]}}
}

# WebSocket data streaming
streaming_active = False
streaming_thread = None

def get_netdata_ui_calculation(server_url, chart_name, timestamp):
    """
    Get Netdata UI-style calculation using the most accurate method
    Based on investigation findings - Netdata UI uses weighted averaging
    """
    
    # Method 1: Try Netdata's internal aggregation first
    try:
        agg_url = f"{server_url}/api/v1/data?chart={chart_name}&format=json&points=10&options=avg&_t={timestamp}"
        response = requests.get(agg_url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                return data['data'][-1][1]  # Last aggregated value
    except:
        pass
    
    # Method 2: Use weighted average (more recent values have more weight) - Netdata UI method
    try:
        raw_url = f"{server_url}/api/v1/data?chart={chart_name}&format=json&points=10&_t={timestamp}"
        response = requests.get(raw_url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                values = [point[1] for point in data['data'] if point[1] is not None]
                if values:
                    # Weighted average: more recent values have higher weight
                    weights = list(range(1, len(values) + 1))  # [1, 2, 3, ..., n]
                    weighted_sum = sum(values[i] * weights[i] for i in range(len(values)))
                    weight_sum = sum(weights)
                    return weighted_sum / weight_sum
    except:
        pass
    
    # Method 3: Fallback to simple average
    try:
        raw_url = f"{server_url}/api/v1/data?chart={chart_name}&format=json&points=10&_t={timestamp}"
        response = requests.get(raw_url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                values = [point[1] for point in data['data'] if point[1] is not None]
                if values:
                    return sum(values) / len(values)
    except:
        pass
    
    # Method 4: Single point fallback
    try:
        single_url = f"{server_url}/api/v1/data?chart={chart_name}&format=json&points=1&_t={timestamp}"
        response = requests.get(single_url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                return data['data'][0][1]
    except:
        pass
    
    return 0

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
                timestamp = latest_point[0] if len(latest_point) > 0 else int(time.time())
                value = latest_point[1] if len(latest_point) > 1 and latest_point[1] is not None else 0
                return value, timestamp
    except Exception as e:
        print(f"Error getting single point data for {chart_name}: {e}")
    
    return 0, int(time.time())

def get_detailed_load_data(server_url):
    """
    Get detailed load data (load1, load5, load15) exactly like Netdata UI
    Uses real-time parameters for immediate data
    """
    try:
        # Use real-time parameters for immediate data:
        # - after=-1: last 1 second (minimal window)
        # - before=0: ending now
        # - points=1: single latest point
        # - group=average: default grouping method
        load_url = f"{server_url}/api/v1/data?chart=system.load&after=-1&before=0&points=1&group=average"
        response = requests.get(load_url, timeout=2)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                # Get the latest point (last in the array)
                latest_point = data['data'][-1]
                if len(latest_point) >= 4:  # [timestamp, load1, load5, load15]
                    load1_value = latest_point[1] if latest_point[1] is not None else 0
                    load5_value = latest_point[2] if latest_point[2] is not None else 0
                    load15_value = latest_point[3] if latest_point[3] is not None else 0
                    
                    return {
                        'chart': 'system.load',
                        'load1': load1_value,
                        'load5': load5_value,
                        'load15': load15_value,
                        'data': [latest_point]
                    }
    except Exception as e:
        print(f"Error getting detailed load data: {e}")
    
    # Fallback
    return {
        'chart': 'system.load',
        'load1': 0,
        'load5': 0,
        'load15': 0,
        'data': [[0, 0, 0, 0]]
    }

def store_metric_data(server_id, server_name, metric_type, value, timestamp):
    """
    Store metric data when threshold is crossed - organized by server
    """
    try:
        data_entry = {
            'server_id': server_id,
            'server_name': server_name,
            'value': value,
            'timestamp': timestamp,
            'datetime': datetime.now().isoformat(),
            'formatted_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Initialize server data structure if it doesn't exist
        if server_id not in metric_history:
            metric_history[server_id] = {
                'mysql_active': [],
                'system_load': [],
                'mysql_per_sec': []
            }
        
        # Store data for this specific server and metric type
        if metric_type in metric_history[server_id]:
            metric_history[server_id][metric_type].append(data_entry)
            
            # Keep only last 50 entries per server per metric to prevent memory issues
            if len(metric_history[server_id][metric_type]) > 50:
                metric_history[server_id][metric_type] = metric_history[server_id][metric_type][-50:]
                
        print(f"📊 Stored {metric_type} data for {server_name} ({server_id}): {value} at {data_entry['formatted_time']}")
        
    except Exception as e:
        print(f"Error storing metric data: {e}")

def send_gchat_alert(server_name, metric_name, value, threshold, alert_type="HIGH"):
    """Send alert to Google Chat"""
    try:
        color = "#FF0000" if alert_type == "HIGH" else "#00FF00"
        status = "🚨 ALERT" if alert_type == "HIGH" else "✅ RECOVERED"
        
        message = {
            "cards": [{
                "header": {
                    "title": f"{status} - {server_name}",
                    "subtitle": f"{metric_name} threshold exceeded"
                },
                "sections": [{
                    "widgets": [{
                        "keyValue": {
                            "topLabel": "Metric",
                            "content": metric_name
                        }
                    }, {
                        "keyValue": {
                            "topLabel": "Current Value",
                            "content": str(value)
                        }
                    }, {
                        "keyValue": {
                            "topLabel": "Threshold",
                            "content": str(threshold)
                        }
                    }]
                }]
            }]
        }
        
        # Use verify=False to bypass SSL issues in development
        response = requests.post(GCHAT_WEBHOOK_URL, json=message, timeout=10, verify=False)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send Google Chat alert: {e}")
        return False

def check_thresholds(server_id, server_name, metrics_data):
    """Check thresholds and send alerts"""
    global alert_states
    
    if server_id not in alert_states:
        alert_states[server_id] = {}
    
    # Check MySQL active connections
    if metrics_data.get('mysql_active') and metrics_data['mysql_active'].get('data'):
        mysql_value = metrics_data['mysql_active']['data'][0][1] if metrics_data['mysql_active']['data'] else 0  # Use exact value
        mysql_timestamp = metrics_data['mysql_active']['data'][0][0] if metrics_data['mysql_active']['data'] else int(time.time())
        
        # Three threshold levels for MySQL Active Connections
        alert_threshold = 400      # Color change + Google Chat message
        storage_threshold = 800    # Store data when crossed
        buzzer_threshold = 1000    # Play buzzer sound
        
        # Check storage threshold (store data every time it's crossed)
        if mysql_value > storage_threshold:
            store_metric_data(server_id, server_name, 'mysql_active', mysql_value, mysql_timestamp)
        
        # Check alert threshold (color change + Google Chat message)
        if mysql_value > alert_threshold:
            if alert_states[server_id].get('mysql_connections') != 'HIGH':
                send_gchat_alert(server_name, "MySQL Active Connections", mysql_value, alert_threshold, "HIGH")
                alert_states[server_id]['mysql_connections'] = 'HIGH'
        else:
            if alert_states[server_id].get('mysql_connections') == 'HIGH':
                send_gchat_alert(server_name, "MySQL Active Connections", mysql_value, alert_threshold, "NORMAL")
                alert_states[server_id]['mysql_connections'] = 'NORMAL'
    
    # Check system load (using load1 as primary metric, like Netdata UI)
    if metrics_data.get('load') and metrics_data['load'].get('load1') is not None:
        load1_value = metrics_data['load']['load1']
        load5_value = metrics_data['load'].get('load5', 0)
        load15_value = metrics_data['load'].get('load15', 0)
        load_timestamp = metrics_data['load']['data'][0][0] if metrics_data['load'].get('data') else int(time.time())
        
        # Three threshold levels for System Load
        alert_threshold = 10       # Color change + Google Chat message
        storage_threshold = 20     # Store data when crossed
        buzzer_threshold = 50      # Play buzzer sound
        
        # Check storage threshold (store data every time it's crossed)
        if load1_value > storage_threshold:
            store_metric_data(server_id, server_name, 'system_load', load1_value, load_timestamp)
        
        # Check alert threshold (color change + Google Chat message)
        if load1_value > alert_threshold:
            if alert_states[server_id].get('system_load') != 'HIGH':
                send_gchat_alert(server_name, f"System Load (load1: {load1_value:.2f}, load5: {load5_value:.2f}, load15: {load15_value:.2f})", load1_value, alert_threshold, "HIGH")
                alert_states[server_id]['system_load'] = 'HIGH'
        else:
            if alert_states[server_id].get('system_load') == 'HIGH':
                send_gchat_alert(server_name, f"System Load (load1: {load1_value:.2f}, load5: {load5_value:.2f}, load15: {load15_value:.2f})", load1_value, alert_threshold, "NORMAL")
                alert_states[server_id]['system_load'] = 'NORMAL'
    
    # Check MySQL per second connections
    if metrics_data.get('mysql_per_sec') and metrics_data['mysql_per_sec'].get('data'):
        mysql_per_sec_value = metrics_data['mysql_per_sec']['data'][0][1] if metrics_data['mysql_per_sec']['data'] else 0
        mysql_per_sec_timestamp = metrics_data['mysql_per_sec']['data'][0][0] if metrics_data['mysql_per_sec']['data'] else int(time.time())
        
        # Three threshold levels for MySQL Per Second Connections
        alert_threshold = 1000     # Color change + Google Chat message
        storage_threshold = 1000   # Store data when crossed (same as alert for now)
        buzzer_threshold = 1000    # Play buzzer sound (same as alert for now)
        
        # Check storage threshold (store data every time it's crossed)
        if mysql_per_sec_value > storage_threshold:
            store_metric_data(server_id, server_name, 'mysql_per_sec', mysql_per_sec_value, mysql_per_sec_timestamp)
        
        # Check alert threshold (color change + Google Chat message)
        if mysql_per_sec_value > alert_threshold:
            if alert_states[server_id].get('mysql_per_sec') != 'HIGH':
                send_gchat_alert(server_name, "MySQL Per Second Connections", mysql_per_sec_value, alert_threshold, "HIGH")
                alert_states[server_id]['mysql_per_sec'] = 'HIGH'
        else:
            if alert_states[server_id].get('mysql_per_sec') == 'HIGH':
                send_gchat_alert(server_name, "MySQL Per Second Connections", mysql_per_sec_value, alert_threshold, "NORMAL")
                alert_states[server_id]['mysql_per_sec'] = 'NORMAL'

def fetch_all_metrics():
    """Fetch metrics from all servers - used for WebSocket streaming"""
    try:
        all_servers_data = {}
        
        for server_id, server_config in NETDATA_SERVERS.items():
            server_data = {}
            server_url = f"http://{server_config['ip']}:{server_config['port']}"
            
            try:
                # Get system overview
                system_url = f"{server_url}/api/v1/info"
                system_response = requests.get(system_url, timeout=2)
                system_data = system_response.json() if system_response.status_code == 200 else {}
                
                # Get MySQL active connections - single point like Netdata UI
                mysql_value, mysql_timestamp = get_single_point_data(server_url, 'mysql_local.connections_active')
                mysql_data = {
                    'chart': 'mysql_local.connections_active',
                    'data': [[mysql_timestamp, mysql_value]]  # Use Netdata's timestamp
                }
                
                # Get system load - individual load1, load5, load15 like Netdata UI
                load_data = get_detailed_load_data(server_url)
                
                # Get MySQL per second connections - single point like Netdata UI
                mysql_per_sec_value, mysql_per_sec_timestamp = get_single_point_data(server_url, 'mysql_local.connections')
                mysql_per_sec_data = {
                    'chart': 'mysql_local.connections',
                    'data': [[mysql_per_sec_timestamp, mysql_per_sec_value]]  # Use Netdata's timestamp
                }
                
                server_data = {
                    'name': server_config['name'],
                    'ip': server_config['ip'],
                    'description': server_config['description'],
                    'status': 'online',
                    'system': system_data,
                    'mysql_active': mysql_data,
                    'load': load_data,
                    'mysql_per_sec': mysql_per_sec_data
                }
                
                # Check thresholds for this server
                check_thresholds(server_id, server_config['name'], server_data)
                
            except Exception as e:
                server_data = {
                    'name': server_config['name'],
                    'ip': server_config['ip'],
                    'description': server_config['description'],
                    'status': 'offline',
                    'error': str(e)
                }
            
            all_servers_data[server_id] = server_data
        
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'fetch_time': time.strftime('%H:%M:%S'),
            'servers': all_servers_data
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }

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
            else:
                print(f"❌ Error in metrics data: {metrics_data.get('message', 'Unknown error')}")
            
            time.sleep(0.5)  # Stream every 0.5 seconds for real-time data
        except Exception as e:
            print(f"❌ Error in metrics streaming: {e}")
            time.sleep(1)
    
    print("🛑 Real-time streaming stopped")

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print(f"Client connected: {request.sid}")
    emit('connection_status', {'status': 'connected', 'message': 'WebSocket connected successfully'})
    
    # Automatically start streaming when client connects
    global streaming_active, streaming_thread
    if not streaming_active:
        streaming_active = True
        streaming_thread = threading.Thread(target=stream_metrics, daemon=True)
        streaming_thread.start()
        print("🚀 Real-time streaming started automatically")
        emit('streaming_status', {'status': 'started', 'message': 'Real-time streaming started automatically'})
    else:
        emit('streaming_status', {'status': 'already_running', 'message': 'Streaming already active'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print(f"Client disconnected: {request.sid}")

@socketio.on('start_streaming')
def handle_start_streaming():
    """Start metrics streaming (manual trigger)"""
    global streaming_active, streaming_thread
    if not streaming_active:
        streaming_active = True
        streaming_thread = threading.Thread(target=stream_metrics, daemon=True)
        streaming_thread.start()
        emit('streaming_status', {'status': 'started', 'message': 'Metrics streaming started'})
    else:
        emit('streaming_status', {'status': 'already_running', 'message': 'Streaming already active'})

@socketio.on('stop_streaming')
def handle_stop_streaming():
    """Stop metrics streaming"""
    global streaming_active
    streaming_active = False
    emit('streaming_status', {'status': 'stopped', 'message': 'Metrics streaming stopped'})

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/server-test')
def server_test():
    """Server management test page"""
    return render_template('server_test.html')

@app.route('/debug-server-management')
def debug_server_management():
    """Debug server management functionality"""
    return render_template('debug_server_management.html')

@app.route('/simple-test')
def simple_test():
    """Simple server management test"""
    return render_template('simple_test.html')

@app.route('/ultra-simple-test')
def ultra_simple_test():
    """Ultra simple server management test"""
    return render_template('ultra_simple_test.html')

@app.route('/test-buzzer')
def test_buzzer():
    """Test buzzer sound functionality"""
    return send_file('test_buzzer.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/api/metric-history/<server_id>/<metric_type>')
def get_server_metric_history(server_id, metric_type):
    """Get stored metric history for a specific server and metric type"""
    try:
        if server_id in metric_history and metric_type in metric_history[server_id]:
            return jsonify({
                'status': 'success',
                'server_id': server_id,
                'metric_type': metric_type,
                'data': metric_history[server_id][metric_type],
                'count': len(metric_history[server_id][metric_type])
            })
        else:
            return jsonify({
                'status': 'success',
                'server_id': server_id,
                'metric_type': metric_type,
                'data': [],
                'count': 0,
                'message': 'No data found for this server and metric type'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/metric-history/<metric_type>')
def get_metric_history(metric_type):
    """Get stored metric history for a specific metric type across all servers"""
    try:
        all_data = []
        total_count = 0
        
        for server_id, server_data in metric_history.items():
            if metric_type in server_data:
                all_data.extend(server_data[metric_type])
                total_count += len(server_data[metric_type])
        
        # Sort by timestamp (newest first)
        all_data.sort(key=lambda x: x['datetime'], reverse=True)
        
        return jsonify({
            'status': 'success',
            'metric_type': metric_type,
            'data': all_data,
            'count': total_count
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/metric-history')
def get_all_metric_history():
    """Get all stored metric history"""
    try:
        summary = {}
        for server_id, server_data in metric_history.items():
            summary[server_id] = {
                'mysql_active': len(server_data.get('mysql_active', [])),
                'system_load': len(server_data.get('system_load', [])),
                'mysql_per_sec': len(server_data.get('mysql_per_sec', []))
            }
        
        return jsonify({
            'status': 'success',
            'data': metric_history,
            'summary': summary
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/metrics')
def get_metrics():
    """Get all metrics from all Netdata servers (fallback for non-WebSocket clients)"""
    try:
        metrics_data = fetch_all_metrics()
        return jsonify(metrics_data)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/chart/<chart_name>')
def get_chart_data(chart_name):
    """Get specific chart data from Netdata"""
    try:
        points = request.args.get('points', '60')
        # Use the first server as default for chart data
        default_server = list(NETDATA_SERVERS.values())[0]
        chart_url = f"http://{default_server['ip']}:{default_server['port']}/api/v1/data?chart={chart_name}&format=json&points={points}"
        response = requests.get(chart_url, timeout=10)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Chart not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts')
def get_available_charts():
    """Get list of available charts from Netdata"""
    try:
        # Use the first server as default for charts list
        default_server = list(NETDATA_SERVERS.values())[0]
        charts_url = f"http://{default_server['ip']}:{default_server['port']}/api/v1/charts"
        response = requests.get(charts_url, timeout=10)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch charts'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint for all servers"""
    try:
        health_status = {}
        
        for server_id, server_config in NETDATA_SERVERS.items():
            try:
                health_url = f"http://{server_config['ip']}:{server_config['port']}/api/v1/info"
                response = requests.get(health_url, timeout=2)
                
                health_status[server_id] = {
                    'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                    'netdata_server': server_config['ip'],
                    'response_time': response.elapsed.total_seconds() if response.status_code == 200 else None,
                    'name': server_config['name']
                }
                
            except Exception as e:
                health_status[server_id] = {
                    'status': 'error',
                    'message': str(e),
                    'netdata_server': server_config['ip'],
                    'name': server_config['name']
                }
        
        return jsonify(health_status)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Server Management API Endpoints
@app.route('/api/servers', methods=['GET'])
def get_servers():
    """Get all configured servers"""
    try:
        return jsonify({
            'status': 'success',
            'servers': NETDATA_SERVERS
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers', methods=['POST'])
def add_server():
    """Add a new server"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['server_id', 'name', 'ip', 'port']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        server_id = data['server_id']
        
        # Check if server already exists
        if server_id in NETDATA_SERVERS:
            return jsonify({'error': f'Server with ID "{server_id}" already exists'}), 400
        
        # Test connection to the server
        test_url = f"http://{data['ip']}:{data['port']}/api/v1/info"
        try:
            test_response = requests.get(test_url, timeout=5)
            if test_response.status_code != 200:
                return jsonify({'error': f'Cannot connect to server {data["ip"]}:{data["port"]}'}), 400
        except Exception as e:
            return jsonify({'error': f'Cannot connect to server {data["ip"]}:{data["port"]}: {str(e)}'}), 400
        
        # Add server to configuration
        NETDATA_SERVERS[server_id] = {
            'name': data['name'],
            'ip': data['ip'],
            'port': data['port'],
            'description': data.get('description', '')
        }
        
        # Save to servers_config.json
        save_servers_config()
        
        return jsonify({
            'status': 'success',
            'message': f'Server "{data["name"]}" added successfully',
            'server_id': server_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<server_id>', methods=['DELETE'])
def remove_server(server_id):
    """Remove a server"""
    try:
        if server_id not in NETDATA_SERVERS:
            return jsonify({'error': f'Server "{server_id}" not found'}), 404
        
        server_name = NETDATA_SERVERS[server_id]['name']
        del NETDATA_SERVERS[server_id]
        
        # Save to servers_config.json
        save_servers_config()
        
        return jsonify({
            'status': 'success',
            'message': f'Server "{server_name}" removed successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<server_id>', methods=['PUT'])
def update_server(server_id):
    """Update server configuration"""
    try:
        if server_id not in NETDATA_SERVERS:
            return jsonify({'error': f'Server "{server_id}" not found'}), 404
        
        data = request.get_json()
        
        # Update server configuration
        if 'name' in data:
            NETDATA_SERVERS[server_id]['name'] = data['name']
        if 'ip' in data:
            NETDATA_SERVERS[server_id]['ip'] = data['ip']
        if 'port' in data:
            NETDATA_SERVERS[server_id]['port'] = data['port']
        if 'description' in data:
            NETDATA_SERVERS[server_id]['description'] = data['description']
        
        # Save to servers_config.json
        save_servers_config()
        
        return jsonify({
            'status': 'success',
            'message': f'Server "{server_id}" updated successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def save_servers_config():
    """Save current server configuration to servers_config.json"""
    try:
        config = {
            "servers": {}
        }
        
        for server_id, server_config in NETDATA_SERVERS.items():
            config["servers"][server_id] = {
                "name": server_config['name'],
                "ip": server_config['ip'],
                "port": server_config['port'],
                "description": server_config.get('description', ''),
                "enabled": True
            }
        
        with open('servers_config.json', 'w') as f:
            json.dump(config, f, indent=4)
            
        print(f"✅ Server configuration saved to servers_config.json")
        
    except Exception as e:
        print(f"❌ Error saving server configuration: {e}")

if __name__ == '__main__':
    print("🚀 Starting Netdata Dashboard with WebSocket support...")
    print("📡 WebSocket URL: ws://0.0.0.0:5001")
    print("🌐 Dashboard URL: http://0.0.0.0:5001")
    print("⚡ Real-time streaming: Enabled")
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)
