#!/bin/bash

# ============================================================================
# LOOTING LARRY - ULTIMATE EDITION (WSL-COMPATIBLE)
# Self-installing, crash-proof, persistent network security suite
# ============================================================================

set +e  # Don't exit on errors in WSL
export DEBIAN_FRONTEND=noninteractive

# ============================================================================
# SUDOERS CONFIGURATION - NO PASSWORD REQUIRED
# ============================================================================

configure_passwordless_sudo() {
    # Check if already configured
    if sudo -n true 2>/dev/null; then
        return 0
    fi
    
    echo "[*] Configuring passwordless sudo..."
    
    # Get current user
    CURRENT_USER=$(whoami)
    
    # Create sudoers file for passwordless sudo
    echo "$CURRENT_USER ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/looting-larry > /dev/null 2>&1 || {
        echo "[!] Could not configure passwordless sudo"
        echo "[!] You may need to enter password this one time"
    }
    
    # Set proper permissions
    sudo chmod 0440 /etc/sudoers.d/looting-larry 2>/dev/null || true
    
    echo "[*] Passwordless sudo configured"
}

# ============================================================================
# ERROR HANDLING
# ============================================================================

handle_error() {
    echo "[ERROR] Error on line $1 - continuing..."
    return 0
}

trap 'handle_error $LINENO' ERR

# ============================================================================
# OS DETECTION
# ============================================================================

detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if grep -qi microsoft /proc/version 2>/dev/null; then
            OS="WSL"
        else
            OS="Linux"
        fi
        
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            DISTRO=$ID
        else
            DISTRO="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macOS"
        DISTRO="macos"
    else
        OS="Unknown"
        DISTRO="unknown"
    fi
}

detect_os

# ============================================================================
# PRIVILEGE ESCALATION
# ============================================================================

ensure_root() {
    if [ "$EUID" -ne 0 ] 2>/dev/null; then
        if [ "$1" != "--already-elevated" ]; then
            echo "[*] Elevating to root..."
            
            # Try passwordless sudo first
            if sudo -n true 2>/dev/null; then
                exec sudo bash "$0" --already-elevated "${@:2}"
            else
                # Configure passwordless sudo and retry
                echo "[*] Setting up passwordless sudo (enter password once)..."
                sudo bash -c "echo '$(whoami) ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/looting-larry; chmod 0440 /etc/sudoers.d/looting-larry"
                exec sudo bash "$0" --already-elevated "${@:2}"
            fi
        fi
    fi
}

# ============================================================================
# CONFIGURATION
# ============================================================================

# Use Windows-accessible path if on WSL
if [ "$OS" = "WSL" ]; then
    # Store in user home which is accessible from Windows
    SUITE_DIR="$HOME/looting_larry"
else
    SUITE_DIR="$HOME/looting_larry"
fi

SCANS_DIR="$SUITE_DIR/scans"
LOGS_DIR="$SUITE_DIR/logs"
DB_DIR="$SUITE_DIR/database"
CONFIG_FILE="$SUITE_DIR/config.conf"
DB_FILE="$DB_DIR/scans.db"
DAEMON_PID_FILE="$SUITE_DIR/daemon.pid"
INSTALL_LOG="$SUITE_DIR/install.log"

mkdir -p "$SUITE_DIR" "$SCANS_DIR" "$LOGS_DIR" "$DB_DIR" 2>/dev/null || true

# Colors
RED='\033[1;31m'
ORANGE='\033[1;33m'
YELLOW='\033[1;33m'
PURPLE='\033[1;35m'
GREEN='\033[1;32m'
CYAN='\033[1;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ============================================================================
# DEPENDENCY INSTALLATION
# ============================================================================

install_dependencies() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${WHITE}                   DEPENDENCY INSTALLATION CHECK                       ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
    
    # Fix Kali repository issues first
    if [ "$DISTRO" = "kali" ]; then
        echo -e "${ORANGE}[*] Fixing Kali Linux repositories...${NC}"
        
        # Update sources.list to use main Kali repos
        cat > /tmp/kali-sources.list << 'EOF'
deb http://http.kali.org/kali kali-rolling main contrib non-free non-free-firmware
EOF
        
        sudo cp /tmp/kali-sources.list /etc/apt/sources.list 2>/dev/null || true
        rm -f /tmp/kali-sources.list
    fi
    
    # Update package lists with error handling
    echo -e "${WHITE}Updating package lists (may take a moment)...${NC}"
    sudo apt-get update 2>&1 | grep -v "Temporary failure" | head -20 || {
        echo -e "${YELLOW}[!] Some repository warnings (non-critical)${NC}"
    }
    
    # Essential packages
    PACKAGES=(
        "nmap"
        "netcat-traditional"
        "net-tools"
        "iproute2"
        "curl"
        "wget"
        "sqlite3"
        "python3"
        "python3-pip"
        "cron"
        "dnsutils"
        "traceroute"
    )
    
    for package in "${PACKAGES[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package" 2>/dev/null; then
            echo -e "${ORANGE}[*] Installing $package...${NC}"
            sudo apt-get install -y "$package" 2>&1 | tail -5 || {
                echo -e "${YELLOW}[!] Warning: $package installation had issues (continuing)${NC}"
            }
        else
            echo -e "${GREEN}[✓] $package already installed${NC}"
        fi
    done
    
    echo -e "\n${GREEN}[✓] Core dependencies installed${NC}\n"
}

# ============================================================================
# DATABASE SETUP
# ============================================================================

init_database() {
    if [ ! -f "$DB_FILE" ]; then
        echo -e "${ORANGE}[*] Initializing database...${NC}"
        
        sqlite3 "$DB_FILE" << 'EOF'
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id TEXT UNIQUE NOT NULL,
    scan_type TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    status TEXT DEFAULT 'running',
    network_range TEXT,
    hosts_found INTEGER DEFAULT 0,
    ports_found INTEGER DEFAULT 0,
    vulnerabilities INTEGER DEFAULT 0,
    output_path TEXT,
    error_log TEXT
);

CREATE TABLE IF NOT EXISTS hosts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    hostname TEXT,
    mac_address TEXT,
    os_guess TEXT,
    status TEXT DEFAULT 'up',
    first_seen DATETIME NOT NULL,
    last_seen DATETIME NOT NULL,
    FOREIGN KEY (scan_id) REFERENCES scans(scan_id),
    UNIQUE(scan_id, ip_address)
);

CREATE TABLE IF NOT EXISTS ports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER NOT NULL,
    port_number INTEGER NOT NULL,
    protocol TEXT NOT NULL,
    state TEXT NOT NULL,
    service TEXT,
    version TEXT,
    first_seen DATETIME NOT NULL,
    last_seen DATETIME NOT NULL,
    FOREIGN KEY (host_id) REFERENCES hosts(id),
    UNIQUE(host_id, port_number, protocol)
);

CREATE TABLE IF NOT EXISTS vulnerabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER NOT NULL,
    port_id INTEGER,
    cve_id TEXT,
    vulnerability_name TEXT NOT NULL,
    severity TEXT,
    description TEXT,
    discovered_date DATETIME NOT NULL,
    FOREIGN KEY (host_id) REFERENCES hosts(id),
    FOREIGN KEY (port_id) REFERENCES ports(id)
);

CREATE TABLE IF NOT EXISTS scan_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enabled INTEGER DEFAULT 1,
    interval_minutes INTEGER DEFAULT 60,
    scan_type TEXT DEFAULT 'discovery',
    last_run DATETIME,
    next_run DATETIME
);

INSERT OR IGNORE INTO scan_schedule (id, enabled, interval_minutes, scan_type)
VALUES (1, 1, 60, 'discovery');

CREATE INDEX IF NOT EXISTS idx_scans_date ON scans(start_time);
CREATE INDEX IF NOT EXISTS idx_hosts_ip ON hosts(ip_address);
CREATE INDEX IF NOT EXISTS idx_ports_number ON ports(port_number);
CREATE INDEX IF NOT EXISTS idx_vulns_severity ON vulnerabilities(severity);
EOF
        
        echo -e "${GREEN}[✓] Database initialized at $DB_FILE${NC}"
    else
        echo -e "${GREEN}[✓] Database exists${NC}"
    fi
}

# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

save_scan_to_db() {
    local scan_id=$1
    local scan_type=$2
    local status=$3
    local network_range=$4
    local output_path=$5
    
    sqlite3 "$DB_FILE" << EOF 2>/dev/null || true
INSERT OR REPLACE INTO scans (scan_id, scan_type, start_time, end_time, status, network_range, output_path)
VALUES (
    '$scan_id',
    '$scan_type',
    datetime('now'),
    datetime('now'),
    '$status',
    '$network_range',
    '$output_path'
);
EOF
}

update_scan_stats() {
    local scan_id=$1
    local hosts=$2
    local ports=$3
    local vulns=$4
    
    sqlite3 "$DB_FILE" << EOF 2>/dev/null || true
UPDATE scans SET
    hosts_found = $hosts,
    ports_found = $ports,
    vulnerabilities = $vulns,
    end_time = datetime('now'),
    status = 'completed'
WHERE scan_id = '$scan_id';
EOF
}

save_host_to_db() {
    local scan_id=$1
    local ip=$2
    local hostname=${3:-""}
    local mac=${4:-""}
    local os=${5:-""}
    
    sqlite3 "$DB_FILE" << EOF 2>/dev/null || true
INSERT OR REPLACE INTO hosts (scan_id, ip_address, hostname, mac_address, os_guess, first_seen, last_seen, status)
VALUES (
    '$scan_id',
    '$ip',
    '$hostname',
    '$mac',
    '$os',
    datetime('now'),
    datetime('now'),
    'up'
);
EOF
}

# ============================================================================
# NETWORK FUNCTIONS
# ============================================================================

get_network_range() {
    # Try multiple methods for WSL compatibility
    local range=""
    
    # Method 1: ip route
    range=$(ip route 2>/dev/null | grep -v default | grep -E "192.168|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\." | head -1 | awk '{print $1}')
    
    # Method 2: ifconfig
    if [ -z "$range" ]; then
        range=$(ifconfig 2>/dev/null | grep -oE "inet (192\.168|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)[0-9.]+" | head -1 | awk '{print $2}' | sed 's/\.[0-9]*$/.0\/24/')
    fi
    
    # Method 3: Default to common range
    if [ -z "$range" ]; then
        range="192.168.1.0/24"
    fi
    
    echo "$range"
}

get_local_ip() {
    ip addr show 2>/dev/null | grep "inet " | grep -v "127.0.0.1" | head -1 | awk '{print $2}' | cut -d'/' -f1 || echo "Unknown"
}

get_gateway() {
    ip route 2>/dev/null | grep default | awk '{print $3}' | head -1 || echo "Unknown"
}

# ============================================================================
# CRON SETUP
# ============================================================================

setup_cron_job() {
    echo -e "${ORANGE}[*] Setting up cron job for hourly scans...${NC}"
    
    # Ensure cron is running
    sudo service cron start 2>/dev/null || sudo /etc/init.d/cron start 2>/dev/null || true
    
    # Get absolute path to script
    SCRIPT_PATH=$(readlink -f "$0")
    
    # Remove existing cron jobs for this script
    (crontab -l 2>/dev/null | grep -v "looting_larry") | crontab - 2>/dev/null || true
    
    # Add new cron job - runs every hour
    (crontab -l 2>/dev/null; echo "0 * * * * $SCRIPT_PATH --scan-once >> $LOGS_DIR/cron.log 2>&1") | crontab - 2>/dev/null || {
        echo -e "${YELLOW}[!] Could not set up cron (may not be available in WSL)${NC}"
        return 1
    }
    
    echo -e "${GREEN}[✓] Cron job configured (hourly scans)${NC}"
}

# ============================================================================
# DAEMON
# ============================================================================

run_daemon() {
    echo "$$" > "$DAEMON_PID_FILE"
    
    echo -e "${GREEN}[✓] Daemon started (PID: $$)${NC}"
    echo "[$(date)] Daemon started" >> "$LOGS_DIR/daemon.log"
    
    while true; do
        echo "[$(date)] Running scheduled scan..." >> "$LOGS_DIR/daemon.log"
        run_automated_scan "discovery"
        
        sqlite3 "$DB_FILE" "UPDATE scan_schedule SET last_run = datetime('now'), next_run = datetime('now', '+1 hour') WHERE id = 1;" 2>/dev/null || true
        
        sleep 3600
    done
}

run_automated_scan() {
    local scan_type=$1
    local scan_id="auto_$(date +%Y%m%d_%H%M%S)"
    
    LOCAL_NETWORK=$(get_network_range)
    
    local output_dir="$SCANS_DIR/$scan_id"
    mkdir -p "$output_dir"
    
    save_scan_to_db "$scan_id" "$scan_type" "running" "$LOCAL_NETWORK" "$output_dir"
    
    nmap -sn "$LOCAL_NETWORK" -oN "$output_dir/hosts.txt" -oG "$output_dir/hosts.gnmap" >> "$LOGS_DIR/daemon.log" 2>&1 || true
    
    local hosts_found=$(grep -c "Host is up" "$output_dir/hosts.txt" 2>/dev/null || echo "0")
    
    grep "Host is up" "$output_dir/hosts.gnmap" 2>/dev/null | while read -r line; do
        local ip=$(echo "$line" | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}')
        [ -n "$ip" ] && save_host_to_db "$scan_id" "$ip"
    done
    
    update_scan_stats "$scan_id" "$hosts_found" "0" "0"
    
    echo "[$(date)] Scan $scan_id completed: $hosts_found hosts found" >> "$LOGS_DIR/daemon.log"
}

# ============================================================================
# ASCII BANNER
# ============================================================================

show_banner() {
    clear
    echo -e "${RED}"
    cat << "EOF"
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║           ██╗      ██████╗  ██████╗ ████████╗██╗███╗   ██╗ ██████╗  ║
    ║           ██║     ██╔═══██╗██╔═══██╗╚══██╔══╝██║████╗  ██║██╔════╝  ║
    ║           ██║     ██║   ██║██║   ██║   ██║   ██║██╔██╗ ██║██║  ███╗ ║
    ║           ██║     ██║   ██║██║   ██║   ██║   ██║██║╚██╗██║██║   ██║ ║
    ║           ███████╗╚██████╔╝╚██████╔╝   ██║   ██║██║ ╚████║╚██████╔╝ ║
    ║           ╚══════╝ ╚═════╝  ╚═════╝    ╚═╝   ╚═╝╚═╝  ╚═══╝ ╚═════╝  ║
EOF
    echo -e "${ORANGE}"
    cat << "EOF"
    ║              ██╗      █████╗ ██████╗ ██████╗ ██╗   ██╗               ║
    ║              ██║     ██╔══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝               ║
    ║              ██║     ███████║██████╔╝██████╔╝ ╚████╔╝                ║
    ║              ██║     ██╔══██║██╔══██╗██╔══██╗  ╚██╔╝                 ║
    ║              ███████╗██║  ██║██║  ██║██║  ██║   ██║                  ║
    ║              ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝                  ║
EOF
    echo -e "${RED}"
    cat << "EOF"
    ║                        ___                                            ║
    ║                      .'   '.         _____                            ║
    ║                     /       \    _.-'     '-.                         ║
    ║                    |  O   O  | .'             '.                      ║
    ║                    |    >    |/                 \                     ║
    ║                    |  \___/  |      NETWORK      |                    ║
    ║                     \       /|     SECURITY      |                    ║
    ║                      '.___.' |      SCANNER      |                    ║
    ║                    _____|_____|_________________/                     ║
    ║                   /     |     |                                       ║
    ║                  /      |     |    "Arr! Plunderin' yer ports"       ║
    ║                 |_______|_____|                                       ║
    ║                         |                                             ║
    ║                        / \                                            ║
    ║                       /   \                                           ║
    ║                      /     \                                          ║
    ║                     /_______\                                         ║
    ║                                                                       ║
    ║              WSL EDITION - Windows 11 + Kali Linux                   ║
    ║                Self-Installing • Passwordless • Persistent            ║
    ╚═══════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

show_network_info() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${WHITE}                     NETWORK CONFIGURATION STATUS                      ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
    
    LOCAL_IP=$(get_local_ip)
    GATEWAY=$(get_gateway)
    LOCAL_NETWORK=$(get_network_range)
    
    echo -e "${WHITE}Operating System:${NC}      ${GREEN}$OS ($DISTRO)${NC}"
    echo -e "${WHITE}Local IP Address:${NC}      ${PURPLE}${LOCAL_IP}${NC}"
    echo -e "${WHITE}Default Gateway:${NC}       ${PURPLE}${GATEWAY}${NC}"
    echo -e "${WHITE}Local Network Range:${NC}   ${PURPLE}${LOCAL_NETWORK}${NC}"
    
    if command -v curl &> /dev/null; then
        PUBLIC_IP=$(curl -s --max-time 3 ifconfig.me 2>/dev/null || echo "Offline")
        echo -e "${WHITE}Public IP Address:${NC}     ${PURPLE}$PUBLIC_IP${NC}"
        
        if [ "$PUBLIC_IP" = "151.245.80.158" ]; then
            echo -e "${WHITE}VPN Status:${NC}            ${GREEN}✓ NordVPN ACTIVE${NC}"
        fi
    fi
    
    echo ""
}

show_daemon_status() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${WHITE}                        DAEMON STATUS                                  ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
    
    if [ -f "$DAEMON_PID_FILE" ]; then
        DAEMON_PID=$(cat "$DAEMON_PID_FILE")
        if ps -p "$DAEMON_PID" > /dev/null 2>&1; then
            echo -e "${WHITE}Daemon Status:${NC}         ${GREEN}✓ RUNNING${NC} ${DIM}(PID: $DAEMON_PID)${NC}"
        else
            echo -e "${WHITE}Daemon Status:${NC}         ${RED}✗ STOPPED${NC}"
        fi
    else
        echo -e "${WHITE}Daemon Status:${NC}         ${RED}✗ NOT STARTED${NC}"
    fi
    
    if [ -f "$DB_FILE" ]; then
        LAST_SCAN=$(sqlite3 "$DB_FILE" "SELECT start_time FROM scans ORDER BY start_time DESC LIMIT 1;" 2>/dev/null)
        TOTAL_SCANS=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM scans;" 2>/dev/null)
        TOTAL_HOSTS=$(sqlite3 "$DB_FILE" "SELECT COUNT(DISTINCT ip_address) FROM hosts;" 2>/dev/null)
        
        echo -e "${WHITE}Last Scan:${NC}             ${PURPLE}${LAST_SCAN:-Never}${NC}"
        echo -e "${WHITE}Total Scans:${NC}           ${GREEN}${TOTAL_SCANS:-0}${NC}"
        echo -e "${WHITE}Unique Hosts Found:${NC}    ${GREEN}${TOTAL_HOSTS:-0}${NC}"
    fi
    
    echo ""
}

show_menu() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${WHITE}                         OPERATION MENU                                ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
    
    echo -e "${WHITE}[${RED}1${WHITE}]${NC} Run Network Discovery Now"
    echo -e "${WHITE}[${RED}2${WHITE}]${NC} View Scan History (Database)"
    echo -e "${WHITE}[${RED}3${WHITE}]${NC} View Discovered Hosts"
    echo -e "${WHITE}[${RED}4${WHITE}]${NC} Start Background Daemon"
    echo -e "${WHITE}[${RED}5${WHITE}]${NC} Stop Background Daemon"
    echo -e "${WHITE}[${RED}6${WHITE}]${NC} Setup Hourly Scans (Cron)"
    echo -e "${WHITE}[${RED}7${WHITE}]${NC} Database Statistics"
    echo -e "${WHITE}[${RED}8${WHITE}]${NC} Export Results to CSV"
    echo -e "${WHITE}[${RED}0${WHITE}]${NC} Exit\n"
    
    echo -e -n "${ORANGE}looting-larry>${NC} "
}

# ============================================================================
# MENU FUNCTIONS
# ============================================================================

run_manual_scan() {
    clear
    show_banner
    echo -e "\n${RED}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║${WHITE}                    MANUAL NETWORK DISCOVERY                           ${RED}║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
    
    LOCAL_NETWORK=$(get_network_range)
    
    SCAN_ID="manual_$(date +%Y%m%d_%H%M%S)"
    OUTPUT_DIR="$SCANS_DIR/$SCAN_ID"
    mkdir -p "$OUTPUT_DIR"
    
    echo -e "${WHITE}Target Network:${NC}    ${PURPLE}$LOCAL_NETWORK${NC}"
    echo -e "${WHITE}Scan ID:${NC}           ${PURPLE}$SCAN_ID${NC}\n"
    
    echo -e "${ORANGE}[*] Starting discovery scan...${NC}\n"
    
    save_scan_to_db "$SCAN_ID" "manual_discovery" "running" "$LOCAL_NETWORK" "$OUTPUT_DIR"
    
    nmap -sn "$LOCAL_NETWORK" -oN "$OUTPUT_DIR/hosts.txt" -oG "$OUTPUT_DIR/hosts.gnmap" 2>&1 | while IFS= read -r line; do
        if [[ $line =~ ([0-9]{1,3}\.){3}[0-9]{1,3} ]]; then
            IP=$(echo "$line" | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}')
            echo -e "${GREEN}[+]${NC} Host discovered: ${PURPLE}$IP${NC}"
            save_host_to_db "$SCAN_ID" "$IP"
        fi
    done
    
    HOSTS_FOUND=$(grep -c "Host is up" "$OUTPUT_DIR/hosts.txt" 2>/dev/null || echo "0")
    update_scan_stats "$SCAN_ID" "$HOSTS_FOUND" "0" "0"
    
    echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${WHITE}                        SCAN COMPLETE                                  ${GREEN}║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
    
    echo -e "${WHITE}Hosts Found:${NC}       ${GREEN}$HOSTS_FOUND${NC}"
    echo -e "${WHITE}Results:${NC}           ${PURPLE}$OUTPUT_DIR${NC}\n"
    
    read -p "Press ENTER to continue..."
}

view_scan_history() {
    clear
    show_banner
    echo -e "\n${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${WHITE}                        SCAN HISTORY                                   ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
    
    if [ ! -f "$DB_FILE" ]; then
        echo -e "${ORANGE}[!] No scan history found${NC}\n"
        read -p "Press ENTER to continue..."
        return
    fi
    
    sqlite3 -header -column "$DB_FILE" "SELECT scan_id, scan_type, start_time, hosts_found, status FROM scans ORDER BY start_time DESC LIMIT 20;" 2>/dev/null
    
    echo ""
    read -p "Press ENTER to continue..."
}

view_discovered_hosts() {
    clear
    show_banner
    echo -e "\n${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${WHITE}                      DISCOVERED HOSTS                                 ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
    
    if [ ! -f "$DB_FILE" ]; then
        echo -e "${ORANGE}[!] No hosts in database${NC}\n"
        read -p "Press ENTER to continue..."
        return
    fi
    
    sqlite3 -header -column "$DB_FILE" "SELECT DISTINCT ip_address, hostname, first_seen, last_seen FROM hosts ORDER BY last_seen DESC LIMIT 50;" 2>/dev/null
    
    echo ""
    read -p "Press ENTER to continue..."
}

start_daemon() {
    if [ -f "$DAEMON_PID_FILE" ]; then
        DAEMON_PID=$(cat "$DAEMON_PID_FILE")
        if ps -p "$DAEMON_PID" > /dev/null 2>&1; then
            echo -e "${ORANGE}[!] Daemon already running (PID: $DAEMON_PID)${NC}\n"
            read -p "Press ENTER to continue..."
            return
        fi
    fi
    
    echo -e "${ORANGE}[*] Starting background daemon...${NC}\n"
    nohup bash "$0" --daemon > "$LOGS_DIR/daemon.log" 2>&1 &
    sleep 2
    
    if [ -f "$DAEMON_PID_FILE" ]; then
        echo -e "${GREEN}[✓] Daemon started successfully${NC}\n"
    else
        echo -e "${RED}[!] Failed to start daemon${NC}\n"
    fi
    
    read -p "Press ENTER to continue..."
}

stop_daemon() {
    if [ ! -f "$DAEMON_PID_FILE" ]; then
        echo -e "${ORANGE}[!] Daemon not running${NC}\n"
        read -p "Press ENTER to continue..."
        return
    fi
    
    DAEMON_PID=$(cat "$DAEMON_PID_FILE")
    
    if ps -p "$DAEMON_PID" > /dev/null 2>&1; then
        echo -e "${ORANGE}[*] Stopping daemon (PID: $DAEMON_PID)...${NC}"
        kill "$DAEMON_PID" 2>/dev/null || true
        rm -f "$DAEMON_PID_FILE"
        echo -e "${GREEN}[✓] Daemon stopped${NC}\n"
    else
        echo -e "${ORANGE}[!] Daemon not running${NC}"
        rm -f "$DAEMON_PID_FILE"
    fi
    
    read -p "Press ENTER to continue..."
}

show_db_stats() {
    clear
    show_banner
    echo -e "\n${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${WHITE}                     DATABASE STATISTICS                               ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
    
    if [ ! -f "$DB_FILE" ]; then
        echo -e "${ORANGE}[!] Database not initialized${NC}\n"
        read -p "Press ENTER to continue..."
        return
    fi
    
    TOTAL_SCANS=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM scans;" 2>/dev/null)
    TOTAL_HOSTS=$(sqlite3 "$DB_FILE" "SELECT COUNT(DISTINCT ip_address) FROM hosts;" 2>/dev/null)
    
    echo -e "${WHITE}Database Location:${NC}     ${PURPLE}$DB_FILE${NC}"
    echo -e "${WHITE}Total Scans:${NC}           ${GREEN}${TOTAL_SCANS:-0}${NC}"
    echo -e "${WHITE}Unique Hosts:${NC}          ${GREEN}${TOTAL_HOSTS:-0}${NC}"
    
    echo -e "\n${WHITE}Most Recent Scans:${NC}\n"
    sqlite3 -header -column "$DB_FILE" "SELECT scan_type, start_time, hosts_found FROM scans ORDER BY start_time DESC LIMIT 5;" 2>/dev/null
    
    echo -e "\n${WHITE}Most Active Hosts:${NC}\n"
    sqlite3 -header -column "$DB_FILE" "SELECT ip_address, COUNT(*) as seen_count FROM hosts GROUP BY ip_address ORDER BY seen_count DESC LIMIT 5;" 2>/dev/null
    
    echo ""
    read -p "Press ENTER to continue..."
}

export_to_csv() {
    clear
    show_banner
    echo -e "\n${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${WHITE}                     EXPORT TO CSV                                     ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
    
    if [ ! -f "$DB_FILE" ]; then
        echo -e "${ORANGE}[!] Database not initialized${NC}\n"
        read -p "Press ENTER to continue..."
        return
    fi
    
    CSV_DIR="$SUITE_DIR/exports"
    mkdir -p "$CSV_DIR"
    
    DATE=$(date +%Y%m%d_%H%M%S)
    
    echo -e "${ORANGE}[*] Exporting data...${NC}\n"
    
    # Export scans
    sqlite3 -header -csv "$DB_FILE" "SELECT * FROM scans;" > "$CSV_DIR/scans_$DATE.csv" 2>/dev/null
    echo -e "${GREEN}[✓]${NC} Exported scans to: ${PURPLE}$CSV_DIR/scans_$DATE.csv${NC}"
    
    # Export hosts
    sqlite3 -header -csv "$DB_FILE" "SELECT * FROM hosts;" > "$CSV_DIR/hosts_$DATE.csv" 2>/dev/null
    echo -e "${GREEN}[✓]${NC} Exported hosts to: ${PURPLE}$CSV_DIR/hosts_$DATE.csv${NC}"
    
    echo -e "\n${WHITE}Files are accessible from Windows at:${NC}"
    echo -e "${PURPLE}\\\\wsl$\\kali-linux\\home\\$(whoami)\\looting_larry\\exports\\${NC}\n"
    
    read -p "Press ENTER to continue..."
}

# ============================================================================
# MAIN MENU
# ============================================================================

main_menu() {
    while true; do
        show_banner
        show_network_info
        show_daemon_status
        show_menu
        
        read -r choice
        
        case $choice in
            1) run_manual_scan ;;
            2) view_scan_history ;;
            3) view_discovered_hosts ;;
            4) start_daemon ;;
            5) stop_daemon ;;
            6) setup_cron_job; read -p "Press ENTER to continue..." ;;
            7) show_db_stats ;;
            8) export_to_csv ;;
            0)
                clear
                show_banner
                echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
                echo -e "${GREEN}║${WHITE}             Thank you for using Looting Larry Security Suite           ${GREEN}║${NC}"
                echo -e "${GREEN}║${WHITE}                       Stay secure, matey!                             ${GREEN}║${NC}"
                echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
                exit 0
                ;;
            *)
                ;;
        esac
    done
}

# ============================================================================
# ENTRY POINT
# ============================================================================

case "${1:-}" in
    --install)
        ensure_root "$@"
        show_banner
        install_dependencies
        init_database
        setup_cron_job
        echo -e "\n${GREEN}[✓] Installation complete!${NC}\n"
        exit 0
        ;;
    --daemon)
        ensure_root "$@"
        init_database
        run_daemon
        ;;
    --scan-once)
        ensure_root "$@"
        init_database
        run_automated_scan "discovery"
        exit 0
        ;;
    --already-elevated)
        shift
        # Continue with elevated privileges
        ;;
    *)
        ensure_root "$@"
        
        # First run setup
        if [ ! -f "$DB_FILE" ] || ! command -v nmap &> /dev/null; then
            show_banner
            echo -e "${ORANGE}[*] First-time setup detected${NC}\n"
            install_dependencies
            init_database
            echo ""
            read -p "Press ENTER to continue to main menu..."
        else
            init_database
        fi
        
        main_menu
        ;;
esac