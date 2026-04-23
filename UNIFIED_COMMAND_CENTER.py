#!/usr/bin/env python3
"""
🎯 UNIFIED COMMAND CENTER - Single Monitor Dashboard
A desktop application providing:
- Real-time service health monitoring with controls
- AI agent chat interface (Ollama-style) with DB storage
- Server metrics and logs
- Trading system status
- Service management (start/stop/open folders)
- All components visible on one screen
"""

import os
import sys
import json
import time
import threading
import webbrowser
import sqlite3
import socket
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
import psutil
import subprocess

# Import cross-platform utilities
try:
    from platform_utils import get_platform
    platform_manager = get_platform()
except Exception as e:
    print(f"WARNING: Could not import platform_utils: {e}")
    platform_manager = None

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# Initialize database with cross-platform path
DB_PATH = PROJECT_ROOT / "command_center.db"

def init_database():
    """Initialize SQLite database for chat history"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                header TEXT,
                summary TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                type TEXT,
                message TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"ERROR initializing database: {e}")

init_database()

try:
    from path_resolver import get_paths, get_config
    paths = get_paths()
    config = get_config()
except Exception as e:
    print(f"Warning: Could not load path_resolver: {e}")
    paths = None
    config = {}

# Flask app
app = Flask(__name__)
CORS(app)

# Global state
service_status = {}
agent_messages = []
system_metrics = {}
trading_stats = {}
current_conversation_id = None

# Project roots for opening folders (cross-platform)
PROJECT_ROOTS = {
    "trading": str(PROJECT_ROOT),
    "ai_agent": str(PROJECT_ROOT),
    "mcp": str(PROJECT_ROOT),
}

# Add secondary drive info if available
SECONDARY_DRIVE = platform_manager.get_secondary_drive() if platform_manager else None
if SECONDARY_DRIVE:
    PROJECT_ROOTS["secondary"] = str(SECONDARY_DRIVE)

# Action commands for quick access buttons
ACTIONS = {
    "start_ollama": {
        "name": "Start Ollama",
        "command": "ollama serve",
        "type": "background",
        "icon": "🤖"
    },
    "start_telegram": {
        "name": "Start Telegram Bot",
        "script": "telegram_bot.py",
        "folder": "trading",
        "icon": "📱"
    },
    "start_agent_v2": {
        "name": "Start Agent V2",
        "script": "ai_agentic_agent.py",
        "folder": "ai_agent",
        "icon": "🧠"
    },
    "start_ea_servers": {
        "name": "Start EA AI Servers",
        "scripts": ["fxjefe_main_server.py", "ai_server.py", "fxjefe_sentiment_server.py"],
        "folder": "trading",
        "icon": "🎯"
    },
    "test_ai_servers": {
        "name": "Test AI Trading",
        "script": "test_model_live.py",
        "folder": "trading",
        "icon": "🧪"
    },
    "network_scan_bat": {
        "name": "Network Scan (BAT)",
        "command": "cmd /c ipconfig /all && netstat -ano",
        "icon": "🔍"
    },
    "network_scan_ps": {
        "name": "Network Scan (PS)",
        "command": "powershell -Command Get-NetTCPConnection | Format-Table -AutoSize",
        "icon": "🔎"
    },
    "network_scan_py": {
        "name": "Network Scan (Python)",
        "script": "network_scan.py",
        "folder": "trading",
        "icon": "🕵️"
    },
    "mcp_github": {
        "name": "GitHub MCP Tools",
        "folder": "mcp",
        "icon": "⚙️"
    },
    "mcp_filesystem": {
        "name": "Filesystem MCP",
        "folder": "mcp",
        "icon": "📁"
    }
}

# ============================================================================
# SERVICE MONITORING
# ============================================================================

SERVICES = {
    "trading_main": {
        "name": "Main Prediction Server",
        "port": 8080,
        "url": "http://127.0.0.1:8080/health",
        "category": "Trading",
        "script": "fxjefe_main_server.py",
        "folder": "trading"
    },
    "trading_ensemble": {
        "name": "AI Ensemble Server",
        "port": 5560,
        "url": "http://127.0.0.1:5560/health",
        "category": "Trading",
        "script": "ai_server.py",
        "folder": "trading"
    },
    "sentiment": {
        "name": "Sentiment Server",
        "port": 8081,
        "url": "http://127.0.0.1:8081/health",
        "category": "Trading",
        "script": "fxjefe_sentiment_server.py",
        "folder": "trading"
    },
    "wol_server": {
        "name": "Wake-on-LAN Service",
        "port": 9,
        "category": "Network",
        "script": "wake_secondary_pc.py",
        "folder": "trading"
    },
    "ai_agent": {
        "name": "AI Agentic Agent",
        "port": 8765,
        "url": "http://127.0.0.1:8765/health",
        "category": "AI",
        "script": "ai_agentic_agent.py",
        "folder": "trading"
    },
    "network_security": {
        "name": "Network Security Scanner",
        "port": 8888,
        "url": "http://127.0.0.1:8888/health",
        "category": "Security",
        "script": "autonomous_network_security.py",
        "folder": "trading"
    }
}

def check_service_health(service_id, service_info):
    """Check if a service is healthy"""
    try:
        # Try URL health check first
        if "url" in service_info:
            response = requests.get(service_info["url"], timeout=2)
            if response.status_code == 200:
                return {
                    "status": "online",
                    "response_time": response.elapsed.total_seconds() * 1000,
                    "details": response.json() if response.headers.get('content-type') == 'application/json' else {}
                }
        
        # Try port check
        if "port" in service_info:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', service_info["port"]))
            sock.close()
            if result == 0:
                return {"status": "online", "response_time": None, "details": {}}
        
        # Try process check
        if "process" in service_info:
            for proc in psutil.process_iter(['name']):
                if service_info["process"] in proc.info['name']:
                    return {"status": "online", "response_time": None, "details": {"pid": proc.pid}}
        
        return {"status": "offline", "response_time": None, "details": {}}
    
    except Exception as e:
        return {"status": "error", "response_time": None, "details": {"error": str(e)}}

def update_service_status():
    """Background thread to continuously monitor services"""
    global service_status
    while True:
        for service_id, service_info in SERVICES.items():
            health = check_service_health(service_id, service_info)
            service_status[service_id] = {
                **service_info,
                **health,
                "last_check": datetime.now().isoformat()
            }
        time.sleep(5)  # Update every 5 seconds

def update_system_metrics():
    """Background thread to collect system metrics"""
    global system_metrics
    while True:
        try:
            system_metrics = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "network": {
                    "bytes_sent": psutil.net_io_counters().bytes_sent,
                    "bytes_recv": psutil.net_io_counters().bytes_recv
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            system_metrics = {"error": str(e)}
        time.sleep(2)

def check_wsl_docker_podman():
    """Check WSL, Docker, and Podman status"""
    status = {}
    
    # Check WSL
    try:
        result = subprocess.run(
            ['wsl', '--list', '--verbose'],
            capture_output=True,
            text=True,
            timeout=5
        )
        wsl_running = 'Running' in result.stdout
        status['wsl'] = {
            'status': 'online' if wsl_running else 'offline',
            'details': result.stdout.strip()
        }
    except Exception as e:
        status['wsl'] = {'status': 'error', 'details': str(e)}
    
    # Check Docker in WSL
    try:
        result = subprocess.run(
            ['wsl', '--exec', 'bash', '-c', 'docker --version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        status['docker'] = {
            'status': 'online' if result.returncode == 0 else 'offline',
            'version': result.stdout.strip(),
            'details': result.stderr if result.returncode != 0 else ''
        }
    except Exception as e:
        status['docker'] = {'status': 'error', 'details': str(e)}
    
    # Check Podman in WSL
    try:
        result = subprocess.run(
            ['wsl', '--exec', 'bash', '-c', 'podman --version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        status['podman'] = {
            'status': 'online' if result.returncode == 0 else 'offline',
            'version': result.stdout.strip(),
            'details': result.stderr if result.returncode != 0 else ''
        }
    except Exception as e:
        status['podman'] = {'status': 'error', 'details': str(e)}
    
    return status

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('command_center.html')

@app.route('/api/services')
def get_services():
    """Get current service status"""
    return jsonify(service_status)

@app.route('/api/metrics')
def get_metrics():
    """Get system metrics"""
    return jsonify(system_metrics)

@app.route('/api/health/ports')
def get_health_ports():
    """Get port health status (200 OK) for all trading servers"""
    health_status = {}
    ports_to_check = [
        ("Main Server", 8080, "http://127.0.0.1:8080/health"),
        ("Ensemble Server", 5560, "http://127.0.0.1:5560/health"),
        ("Sentiment Server", 8081, "http://127.0.0.1:8081/health"),
        ("WOL Service", 9, "udp://127.0.0.1:9"),
    ]
    
    for name, port, url in ports_to_check:
        try:
            if "udp" in url:
                # Simple UDP port check
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(1)
                try:
                    sock.sendto(b"ping", ("127.0.0.1", port))
                    health_status[name] = {"status": "online", "port": port, "code": 200}
                except:
                    health_status[name] = {"status": "offline", "port": port, "code": 0}
                sock.close()
            else:
                # HTTP health check
                response = requests.get(url, timeout=2)
                health_status[name] = {
                    "status": "online" if response.status_code == 200 else "offline",
                    "port": port,
                    "code": response.status_code
                }
        except requests.exceptions.Timeout:
            health_status[name] = {"status": "timeout", "port": port, "code": 0}
        except Exception as e:
            health_status[name] = {"status": "error", "port": port, "code": 0, "error": str(e)}
    
    return jsonify(health_status)

@app.route('/api/drives/usage')
def get_drives_usage():
    """Get disk usage for project root and data folders"""
    drive_usage = {}
    
    paths_to_track = {
        "Project Root": PROJECT_ROOT,
        "Data Folder": PROJECT_ROOT / "Data",
        "Models": PROJECT_ROOT / "models",
        "Logs": PROJECT_ROOT / "logs",
    }
    
    for name, path in paths_to_track.items():
        try:
            if path.exists():
                stat = psutil.disk_usage(str(path))
                drive_usage[name] = {
                    "path": str(path),
                    "total": stat.total,
                    "used": stat.used,
                    "free": stat.free,
                    "percent": stat.percent
                }
            else:
                drive_usage[name] = {"path": str(path), "error": "Path not found"}
        except Exception as e:
            drive_usage[name] = {"path": str(path), "error": str(e)}
    
    return jsonify(drive_usage)

@app.route('/api/wsl-status')
def get_wsl_status():
    """Get WSL, Docker, and Podman status"""
    return jsonify(check_wsl_docker_podman())

@app.route('/api/system/info')
def get_system_info():
    """Get system information including drives and platform"""
    try:
        info = {
            'platform': platform_manager.get_platform_name() if platform_manager else sys.platform,
            'project_root': str(PROJECT_ROOT),
            'secondary_drive': str(SECONDARY_DRIVE) if SECONDARY_DRIVE else None,
            'drives': {}
        }
        
        if platform_manager:
            drives = platform_manager.get_drives()
            for key, val in drives.items():
                info['drives'][key] = {
                    'path': str(val['path']),
                    'type': val['type'],
                    'available': val.get('available', True)
                }
        
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agent/chat', methods=['POST'])
def agent_chat():
    """Handle agent chat messages with database storage"""
    global current_conversation_id
    data = request.json
    user_message = data.get('message', '')
    model = data.get('model', 'default')
    
    # Create new conversation if none exists
    if current_conversation_id is None:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO conversations (header, summary) VALUES (?, ?)', 
                      (user_message[:100], 'Active conversation'))
        current_conversation_id = cursor.lastrowid
        conn.commit()
        conn.close()
    
    # Save user message to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (conversation_id, type, message) VALUES (?, ?, ?)',
                  (current_conversation_id, 'user', user_message))
    conn.commit()
    conn.close()
    
    # Add to session messages
    agent_messages.append({
        'type': 'user',
        'message': user_message,
        'timestamp': datetime.now().isoformat()
    })
    
    # Try Ollama first, then fallback to AI agent
    try:
        # Try Ollama
        if model != 'default':
            response = requests.post(
                'http://127.0.0.1:11434/api/generate',
                json={'model': model, 'prompt': user_message, 'stream': False},
                timeout=30
            )
            if response.status_code == 200:
                agent_response = response.json().get('response', 'No response')
            else:
                raise Exception("Ollama unavailable")
        else:
            # Try AI Agent on port 5000
            response = requests.post(
                'http://127.0.0.1:5000/chat',
                json={'message': user_message},
                timeout=30
            )
            if response.status_code == 200:
                agent_response = response.json().get('response', 'No response')
            else:
                agent_response = f"Agent says: I received your message '{user_message[:50]}...'"
    except Exception as e:
        agent_response = f"💡 AI Agent is offline. Start the agent server first:\n\n`python ai_agentic_agent.py`\n\nOr use Ollama models if installed."
    
    # Save agent response to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (conversation_id, type, message) VALUES (?, ?, ?)',
                  (current_conversation_id, 'agent', agent_response))
    conn.commit()
    conn.close()
    
    # Add agent response to session
    agent_messages.append({
        'type': 'agent',
        'message': agent_response,
        'timestamp': datetime.now().isoformat()
    })
    
    return jsonify({
        'success': True,
        'response': agent_response
    })

@app.route('/api/agent/history')
def get_agent_history():
    """Get agent chat history"""
    return jsonify(agent_messages[-50:])  # Last 50 messages

@app.route('/api/trading/stats')
def get_trading_stats():
    """Get trading statistics"""
    try:
        # Try to get stats from trading server
        response = requests.get('http://127.0.0.1:8081/stats', timeout=2)
        if response.status_code == 200:
            return jsonify(response.json())
    except:
        pass
    
    # Return mock data if server unavailable
    return jsonify({
        "total_trades": 0,
        "win_rate": 0.0,
        "profit_loss": 0.0,
        "open_positions": 0
    })

@app.route('/api/logs/<service_id>')
def get_service_logs(service_id):
    """Get logs for a specific service"""
    # Try to find log file
    log_dirs = [
        PROJECT_ROOT / "logs",
        Path.home() / ".master_orchestrator" / "logs"
    ]
    
    logs = []
    for log_dir in log_dirs:
        if log_dir.exists():
            for log_file in log_dir.glob(f"*{service_id}*.log"):
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        logs.extend(f.readlines()[-100:])  # Last 100 lines
                except:
                    pass
    
    return jsonify({"logs": logs})

@app.route('/api/service/start/<service_id>', methods=['POST'])
def start_service(service_id):
    """Start a service"""
    if service_id not in SERVICES:
        return jsonify({"success": False, "error": "Service not found"})
    
    service = SERVICES[service_id]
    script = service.get('script')
    
    if not script:
        return jsonify({"success": False, "error": "No script defined for this service"})
    
    try:
        # Get project folder
        folder = service.get('folder', 'trading')
        project_path = PROJECT_ROOTS.get(folder, PROJECT_ROOT)
        script_path = Path(project_path) / script
        
        if not script_path.exists():
            return jsonify({"success": False, "error": f"Script not found: {script_path}"})
        
        # Start service in background
        if sys.platform == 'win32':
            subprocess.Popen(
                ['python', str(script_path)],
                cwd=str(project_path),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            subprocess.Popen(
                ['python', str(script_path)],
                cwd=str(project_path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        return jsonify({"success": True, "message": f"Starting {service['name']}..."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/service/folder/<service_id>', methods=['POST'])
def open_service_folder(service_id):
    """Open service project folder (cross-platform)"""
    if service_id not in SERVICES:
        return jsonify({"success": False, "error": "Service not found"})
    
    service = SERVICES[service_id]
    folder = service.get('folder')
    
    if not folder or folder not in PROJECT_ROOTS:
        return jsonify({"success": False, "error": "No folder defined"})
    
    try:
        project_path = Path(PROJECT_ROOTS[folder])
        if not project_path.exists():
            return jsonify({"success": False, "error": f"Path does not exist: {project_path}"})
        
        # Use platform_manager if available
        if platform_manager:
            success = platform_manager.open_folder(project_path)
            if success:
                return jsonify({"success": True, "message": f"Opening {project_path}"})
            else:
                return jsonify({"success": False, "error": "Failed to open folder"})
        
        # Fallback to direct OS calls
        if platform_manager and platform_manager.is_windows:
            os.startfile(str(project_path))
        elif platform_manager and platform_manager.is_mac:
            subprocess.run(['open', str(project_path)], check=True)
        else:  # Linux and fallback
            subprocess.run(['xdg-open', str(project_path)], check=True)
        
        return jsonify({"success": True, "message": f"Opening {project_path}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/conversations')
def get_conversations():
    """Get all conversation history"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, created_at, header, summary,
               (SELECT COUNT(*) FROM messages WHERE conversation_id = conversations.id) as message_count
        FROM conversations
        ORDER BY created_at DESC
        LIMIT 50
    ''')
    conversations = []
    for row in cursor.fetchall():
        conversations.append({
            'id': row[0],
            'created_at': row[1],
            'header': row[2],
            'summary': row[3],
            'message_count': row[4]
        })
    conn.close()
    return jsonify(conversations)

@app.route('/api/conversation/<int:conv_id>')
def get_conversation(conv_id):
    """Get specific conversation messages"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, type, message
        FROM messages
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
    ''', (conv_id,))
    messages = []
    for row in cursor.fetchall():
        messages.append({
            'timestamp': row[0],
            'type': row[1],
            'message': row[2]
        })
    conn.close()
    return jsonify(messages)

@app.route('/api/conversation/new', methods=['POST'])
def new_conversation():
    """Start a new conversation"""
    global current_conversation_id
    current_conversation_id = None
    agent_messages.clear()
    return jsonify({"success": True, "message": "New conversation started"})

@app.route('/api/ollama/models')
def get_ollama_models():
    """Get available Ollama models"""
    try:
        response = requests.get('http://127.0.0.1:11434/api/tags', timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return jsonify({"success": True, "models": [m['name'] for m in models]})
    except:
        pass
    return jsonify({"success": False, "models": []})

@app.route('/api/action/<action_id>', methods=['POST'])
def execute_action(action_id):
    """Execute a quick action"""
    if action_id not in ACTIONS:
        return jsonify({"success": False, "error": "Action not found"})
    
    action = ACTIONS[action_id]
    
    try:
        # Handle direct commands
        if "command" in action:
            if sys.platform == 'win32':
                subprocess.Popen(
                    action["command"],
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                subprocess.Popen(action["command"], shell=True)
            return jsonify({"success": True, "message": f"Executed: {action['name']}"})
        
        # Handle single script
        if "script" in action:
            folder = action.get('folder', 'trading')
            project_path = PROJECT_ROOTS.get(folder, PROJECT_ROOT)
            script_path = Path(project_path) / action["script"]
            
            if not script_path.exists():
                return jsonify({"success": False, "error": f"Script not found: {script_path}"})
            
            if sys.platform == 'win32':
                subprocess.Popen(
                    ['python', str(script_path)],
                    cwd=str(project_path),
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                subprocess.Popen(
                    ['python', str(script_path)],
                    cwd=str(project_path)
                )
            return jsonify({"success": True, "message": f"Started: {action['name']}"})
        
        # Handle multiple scripts
        if "scripts" in action:
            folder = action.get('folder', 'trading')
            project_path = PROJECT_ROOTS.get(folder, PROJECT_ROOT)
            started = []
            
            for script in action["scripts"]:
                script_path = Path(project_path) / script
                if script_path.exists():
                    if sys.platform == 'win32':
                        subprocess.Popen(
                            ['python', str(script_path)],
                            cwd=str(project_path),
                            creationflags=subprocess.CREATE_NEW_CONSOLE
                        )
                    else:
                        subprocess.Popen(
                            ['python', str(script_path)],
                            cwd=str(project_path)
                        )
                    started.append(script)
            
            if started:
                return jsonify({"success": True, "message": f"Started: {', '.join(started)}"})
            else:
                return jsonify({"success": False, "error": "No scripts found"})
        
        # Handle folder opening
        if "folder" in action and "script" not in action and "scripts" not in action:
            folder = action['folder']
            project_path = PROJECT_ROOTS.get(folder, PROJECT_ROOT)
            if sys.platform == 'win32':
                os.startfile(str(project_path))
            else:
                subprocess.Popen(['xdg-open', str(project_path)])
            return jsonify({"success": True, "message": f"Opened: {project_path}"})
        
        return jsonify({"success": False, "error": "Unknown action type"})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/scan/ports', methods=['POST'])
def scan_ports():
    """Scan local ports and return active ones (non-blocking)"""
    try:
        import socket
        import threading
        
        common_ports = [80, 443, 8080, 8081, 5560, 5561, 8765, 8888, 9999, 3306, 5432, 27017, 6379, 11434]
        ports = []
        ports_lock = threading.Lock()
        
        service_map = {
            80: 'HTTP', 443: 'HTTPS', 8080: 'Main Server',
            8081: 'Sentiment', 5561: 'AI Ensemble', 8765: 'AI Agent',
            8888: 'Network Security', 9999: 'Dashboard',
            3306: 'MySQL', 5432: 'PostgreSQL', 27017: 'MongoDB',
            6379: 'Redis', 11434: 'Ollama'
        }
        
        def scan_single_port(port):
            """Scan a single port without blocking"""
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.2)  # Reduced timeout
                result = sock.connect_ex(('127.0.0.1', port))
                sock.close()
                
                if result == 0:
                    with ports_lock:
                        ports.append({
                            'port': port,
                            'status': 'LISTENING',
                            'service': service_map.get(port, 'Unknown')
                        })
            except:
                pass
        
        # Use threads for parallel scanning (faster)
        threads = []
        for port in common_ports:
            t = threading.Thread(target=scan_single_port, args=(port,), daemon=True)
            threads.append(t)
            t.start()
        
        # Wait for all threads (max 2 seconds total)
        for t in threads:
            t.join(timeout=2)
        
        return jsonify({"success": True, "ports": ports})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/scan/network', methods=['POST'])
def scan_network():
    """Scan network interfaces"""
    try:
        import psutil
        interfaces = []
        
        # Get network interfaces
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()
        
        for iface_name, addrs in net_if_addrs.items():
            for addr in addrs:
                if addr.family == socket.AF_INET:  # IPv4
                    status = 'UP' if net_if_stats.get(iface_name, None) and net_if_stats[iface_name].isup else 'DOWN'
                    interfaces.append({
                        'name': iface_name,
                        'ip': addr.address,
                        'netmask': addr.netmask,
                        'status': status
                    })
        
        return jsonify({"success": True, "interfaces": interfaces, "neighbors": []})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/scan/connections', methods=['POST'])
def scan_connections():
    """Get active network connections"""
    try:
        import psutil
        connections = []
        
        # Get TCP connections
        conns = psutil.net_connections(kind='tcp')
        
        for conn in conns[:50]:  # Limit to 50 connections
            if conn.status == 'LISTEN' or conn.status == 'ESTABLISHED':
                connections.append({
                    'local_addr': conn.laddr.ip if conn.laddr else '0.0.0.0',
                    'local_port': conn.laddr.port if conn.laddr else 0,
                    'remote_addr': conn.raddr.ip if conn.raddr else '-',
                    'remote_port': conn.raddr.port if conn.raddr else 0,
                    'state': conn.status,
                    'pid': conn.pid if conn.pid else 0
                })
        
        return jsonify({"success": True, "connections": connections})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/actions')
def get_actions():
    """Get all available actions"""
    return jsonify(ACTIONS)

@app.route('/api/failover/status')
def get_failover_status():
    """Get secondary PC failover status"""
    try:
        status_file = PROJECT_ROOT / "failover_status.json"
        if status_file.exists():
            with open(status_file, 'r') as f:
                return jsonify(json.load(f))
        else:
            return jsonify({
                "status": "not_configured",
                "message": "Failover system not configured"
            })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

@app.route('/api/test')
def test_route():
    """Test route"""
    return jsonify({"message": "Test route works", "success": True})

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Start the unified command center"""
    # Set UTF-8 encoding for console output
    import sys
    if sys.platform == 'win32':
        import os
        os.system('chcp 65001 > nul')
    
    print("=" * 80)
    print("TARGET UNIFIED COMMAND CENTER")
    print("=" * 80)
    print()
    print("Starting background monitors...")
    
    # Start background threads
    threading.Thread(target=update_service_status, daemon=True).start()
    threading.Thread(target=update_system_metrics, daemon=True).start()
    
    print("[OK] Service monitor started")
    print("[OK] System metrics collector started")
    print()
    
    # Check WSL/Docker/Podman
    print("Checking WSL, Docker, and Podman...")
    container_status = check_wsl_docker_podman()
    for name, status in container_status.items():
        symbol = "OK" if status['status'] == 'online' else "X"
        print(f"[{symbol}] {name.upper()}: {status['status']}")
        if 'version' in status:
            print(f"  -> {status['version']}")
    print()
    
    # Start Flask server
    port = 9999
    url = f"http://127.0.0.1:{port}"
    
    print(f"Starting web interface on port {port}...")
    print(f"Dashboard: {url}")
    print()
    print("=" * 80)
    print("Press Ctrl+C to stop")
    print("=" * 80)
    print()
    
    # Open browser
    threading.Timer(2, lambda: webbrowser.open(url)).start()
    
    # Run Flask
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True, use_reloader=False)

if __name__ == '__main__':
    main()
