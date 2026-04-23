#!/bin/bash

# Looting Larry - Enterprise Network Security Suite
# Professional-grade homelab security scanning toolkit

# Color definitions
RED='\033[1;31m'
ORANGE='\033[1;33m'
PURPLE='\033[1;35m'
GREEN='\033[1;32m'
CYAN='\033[1;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# Configuration
SUITE_DIR="$HOME/looting_larry"
SCANS_DIR="$SUITE_DIR/scans"
LOGS_DIR="$SUITE_DIR/logs"
CONFIG_FILE="$SUITE_DIR/config.conf"

# Create directory structure
mkdir -p "$SCANS_DIR" "$LOGS_DIR"

# ASCII Art Pirate
show_banner() {
    clear
    echo -e "${RED}"
    cat << "EOF"
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                                                                       ║
    ║           ██╗      ██████╗  ██████╗ ████████╗██╗███╗   ██╗ ██████╗  ║
    ║           ██║     ██╔═══██╗██╔═══██╗╚══██╔══╝██║████╗  ██║██╔════╝  ║
    ║           ██║     ██║   ██║██║   ██║   ██║   ██║██╔██╗ ██║██║  ███╗ ║
    ║           ██║     ██║   ██║██║   ██║   ██║   ██║██║╚██╗██║██║   ██║ ║
    ║           ███████╗╚██████╔╝╚██████╔╝   ██║   ██║██║ ╚████║╚██████╔╝ ║
    ║           ╚══════╝ ╚═════╝  ╚═════╝    ╚═╝   ╚═╝╚═╝  ╚═══╝ ╚═════╝  ║
    ║                                                                       ║
EOF
    echo -e "${ORANGE}"
    cat << "EOF"
    ║              ██╗      █████╗ ██████╗ ██████╗ ██╗   ██╗               ║
    ║              ██║     ██╔══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝               ║
    ║              ██║     ███████║██████╔╝██████╔╝ ╚████╔╝                ║
    ║              ██║     ██╔══██║██╔══██╗██╔══██╗  ╚██╔╝                 ║
    ║              ███████╗██║  ██║██║  ██║██║  ██║   ██║                  ║
    ║              ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝                  ║
    ║                                                                       ║
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
    ║                 Enterprise Network Security Suite                    ║
    ║                    Professional Grade v2.1.0                         ║
    ╚═══════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Network info display
show_network_info() {
    echo -e "\n${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${WHITE}                     NETWORK CONFIGURATION STATUS                      ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
   
    # Local IP
    LOCAL_IP=$(ip addr show | grep "inet " | grep -v "127.0.0.1" | head -1 | awk '{print $2}' | cut -d'/' -f1)
    echo -e "${WHITE}Local IP Address:${NC}      ${PURPLE}$LOCAL_IP${NC}"
   
    # Gateway
    GATEWAY=$(ip route | grep default | awk '{print $3}')
    echo -e "${WHITE}Default Gateway:${NC}       ${PURPLE}$GATEWAY${NC}"
   
    # Network range
    LOCAL_NETWORK=$(ip route | grep -v default | grep -E "192.168|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\." | head -1 | awk '{print $1}')
    echo -e "${WHITE}Local Network Range:${NC}   ${PURPLE}$LOCAL_NETWORK${NC}"
   
    # Public IP
    echo -e "\n${WHITE}Checking external IP...${NC}"
    PUBLIC_IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || echo "Unable to fetch")
    echo -e "${WHITE}Public IP Address:${NC}     ${PURPLE}$PUBLIC_IP${NC}"
   
    # VPN Status
    if [ "$PUBLIC_IP" = "151.245.80.158" ]; then
        echo -e "${WHITE}VPN Status:${NC}            ${GREEN}✓ NordVPN ACTIVE${NC}"
    elif [ "$PUBLIC_IP" = "Unable to fetch" ]; then
        echo -e "${WHITE}VPN Status:${NC}            ${ORANGE}⚠ Unable to verify${NC}"
    else
        echo -e "${WHITE}VPN Status:${NC}            ${ORANGE}⚠ Different IP detected${NC}"
    fi
   
    echo -e "\n${DIM}Note: Local scans operate on LAN and bypass VPN tunnel${NC}\n"
}

# Main menu
show_menu() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${WHITE}                         OPERATION MENU                                ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
   
    echo -e "${WHITE}[${RED}1${WHITE}]${NC} Network Discovery Scan      ${DIM}(Identify all active hosts)${NC}"
    echo -e "${WHITE}[${RED}2${WHITE}]${NC} Comprehensive Security Audit${DIM}(Full vulnerability assessment)${NC}"
    echo -e "${WHITE}[${RED}3${WHITE}]${NC} Single Device Deep Scan     ${DIM}(Target specific IP address)${NC}"
    echo -e "${WHITE}[${RED}4${WHITE}]${NC} IPv6 Network Analysis       ${DIM}(Scan IPv6 infrastructure)${NC}"
    echo -e "${WHITE}[${RED}5${WHITE}]${NC} Continuous Monitoring       ${DIM}(Real-time network watch)${NC}"
    echo -e "${WHITE}[${RED}6${WHITE}]${NC} Port Sweep Analyzer         ${DIM}(Fast port enumeration)${NC}"
    echo -e "${WHITE}[${RED}7${WHITE}]${NC} View Scan Reports           ${DIM}(Access historical data)${NC}"
    echo -e "${WHITE}[${RED}8${WHITE}]${NC} Network Configuration       ${DIM}(Refresh network status)${NC}"
    echo -e "${WHITE}[${RED}9${WHITE}]${NC} System Diagnostics          ${DIM}(Verify tool availability)${NC}"
    echo -e "${WHITE}[${RED}0${WHITE}]${NC} Exit Suite\n"
   
    echo -e -n "${ORANGE}looting-larry>${NC} "
}

# Network discovery scan
network_discovery() {
    clear
    show_banner
    echo -e "\n${RED}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║${WHITE}                    NETWORK DISCOVERY OPERATION                        ${RED}║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
   
    DATE=$(date +%Y%m%d_%H%M%S)
    OUTPUT="$SCANS_DIR/discovery_$DATE"
   
    LOCAL_NETWORK=$(ip route | grep -v default | grep -E "192.168|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\." | head -1 | awk '{print $1}')
   
    echo -e "${WHITE}Target Network:${NC}    ${PURPLE}$LOCAL_NETWORK${NC}"
    echo -e "${WHITE}Scan ID:${NC}           ${PURPLE}discovery_$DATE${NC}"
    echo -e "${WHITE}Output Path:${NC}       ${DIM}$OUTPUT${NC}\n"
   
    echo -e "${ORANGE}[*] Initiating host discovery protocol...${NC}\n"
   
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}[!] WARNING: Running without root privileges. Results may be limited.${NC}"
        echo -e "${ORANGE}[*] Attempting unprivileged scan...${NC}\n"
        nmap -sn "$LOCAL_NETWORK" -oN "$OUTPUT.txt" | while IFS= read -r line; do
            if [[ $line =~ ([0-9]{1,3}\.){3}[0-9]{1,3} ]]; then
                IP=$(echo "$line" | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}')
                echo -e "${GREEN}[+]${NC} Host discovered: ${PURPLE}$IP${NC}"
            fi
            echo "$line" >> "$OUTPUT.log"
        done
    else
        sudo nmap -sn "$LOCAL_NETWORK" -oN "$OUTPUT.txt" -oG "$OUTPUT.gnmap" | while IFS= read -r line; do
            if [[ $line =~ ([0-9]{1,3}\.){3}[0-9]{1,3} ]]; then
                IP=$(echo "$line" | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}')
                echo -e "${GREEN}[+]${NC} Host discovered: ${PURPLE}$IP${NC}"
            fi
            echo "$line" >> "$OUTPUT.log"
        done
    fi
   
    # Summary
    HOSTS=$(grep -c "Up" "$OUTPUT.txt" 2>/dev/null || echo "0")
   
    echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${WHITE}                        DISCOVERY COMPLETE                             ${GREEN}║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
   
    echo -e "${WHITE}Active Hosts Detected:${NC} ${GREEN}$HOSTS${NC}"
    echo -e "${WHITE}Scan Report:${NC}           ${PURPLE}$OUTPUT.txt${NC}\n"
   
    read -p "Press ENTER to return to menu..."
}

# Comprehensive security audit
security_audit() {
    clear
    show_banner
    echo -e "\n${RED}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║${WHITE}                COMPREHENSIVE SECURITY AUDIT PROTOCOL                  ${RED}║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
   
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}[!] ERROR: Root privileges required for comprehensive audit${NC}"
        echo -e "${ORANGE}[*] Please run: sudo ./looting_larry.sh${NC}\n"
        read -p "Press ENTER to return to menu..."
        return
    fi
   
    DATE=$(date +%Y%m%d_%H%M%S)
    AUDIT_DIR="$SCANS_DIR/audit_$DATE"
    mkdir -p "$AUDIT_DIR"
   
    LOCAL_NETWORK=$(ip route | grep -v default | grep -E "192.168|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\." | head -1 | awk '{print $1}')
   
    echo -e "${WHITE}Target Network:${NC}    ${PURPLE}$LOCAL_NETWORK${NC}"
    echo -e "${WHITE}Audit ID:${NC}          ${PURPLE}audit_$DATE${NC}"
    echo -e "${WHITE}Output Directory:${NC}  ${DIM}$AUDIT_DIR${NC}\n"
   
    # Phase 1
    echo -e "${ORANGE}[Phase 1/4]${NC} ${WHITE}Host Discovery${NC}"
    echo -e "${DIM}├─ Scanning network for active devices...${NC}"
    sudo nmap -sn "$LOCAL_NETWORK" -oG "$AUDIT_DIR/hosts.gnmap" > /dev/null 2>&1
    HOSTS=$(grep -c "Up" "$AUDIT_DIR/hosts.gnmap")
    echo -e "${DIM}└─${NC} ${GREEN}✓${NC} Discovered ${GREEN}$HOSTS${NC} active hosts\n"
   
    grep "Up" "$AUDIT_DIR/hosts.gnmap" | awk '{print $2}' > "$AUDIT_DIR/live_hosts.txt"
   
    # Phase 2
    echo -e "${ORANGE}[Phase 2/4]${NC} ${WHITE}Port Enumeration${NC}"
    echo -e "${DIM}├─ Analyzing TCP/UDP port states...${NC}"
    sudo nmap -sS -sU -T4 --top-ports 1000 -iL "$AUDIT_DIR/live_hosts.txt" \
        -oN "$AUDIT_DIR/ports.txt" -oX "$AUDIT_DIR/ports.xml" > /dev/null 2>&1
    OPEN_PORTS=$(grep -c "open" "$AUDIT_DIR/ports.txt")
    echo -e "${DIM}└─${NC} ${GREEN}✓${NC} Identified ${GREEN}$OPEN_PORTS${NC} open ports\n"
   
    # Phase 3
    echo -e "${ORANGE}[Phase 3/4]${NC} ${WHITE}Service Detection${NC}"
    echo -e "${DIM}├─ Fingerprinting service versions...${NC}"
    sudo nmap -sV -sC --version-intensity 5 -iL "$AUDIT_DIR/live_hosts.txt" \
        -oN "$AUDIT_DIR/services.txt" > /dev/null 2>&1
    echo -e "${DIM}└─${NC} ${GREEN}✓${NC} Service enumeration complete\n"
   
    # Phase 4
    echo -e "${ORANGE}[Phase 4/4]${NC} ${WHITE}Vulnerability Assessment${NC}"
    echo -e "${DIM}├─ Executing CVE detection scripts...${NC}"
    sudo nmap --script vuln --script-args=unsafe=0 -iL "$AUDIT_DIR/live_hosts.txt" \
        -oN "$AUDIT_DIR/vulnerabilities.txt" > /dev/null 2>&1
    VULNS=$(grep -c "VULNERABLE" "$AUDIT_DIR/vulnerabilities.txt" || echo "0")
    echo -e "${DIM}└─${NC} ${ORANGE}⚠${NC}  Detected ${ORANGE}$VULNS${NC} potential vulnerabilities\n"
   
    # Generate summary
    cat > "$AUDIT_DIR/AUDIT_SUMMARY.txt" << EOF
================================================================================
                    LOOTING LARRY SECURITY AUDIT REPORT
================================================================================

Audit ID:           audit_$DATE
Target Network:     $LOCAL_NETWORK
Scan Date:          $(date)
Operator:           $(whoami)

================================================================================
                              EXECUTIVE SUMMARY
================================================================================

Active Hosts:       $HOSTS
Open Ports:         $OPEN_PORTS
Vulnerabilities:    $VULNS

================================================================================
                                 FINDINGS
================================================================================

Detailed results available in:
  - hosts.gnmap           (Host discovery data)
  - ports.txt             (Port enumeration)
  - services.txt          (Service fingerprints)
  - vulnerabilities.txt   (CVE assessment)

================================================================================
                              RECOMMENDATIONS
================================================================================

1. Review all open ports and disable unnecessary services
2. Update software versions to patch known vulnerabilities
3. Implement network segmentation for critical assets
4. Enable host-based firewalls on all devices
5. Schedule regular security audits (monthly recommended)

================================================================================
EOF
   
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${WHITE}                        AUDIT COMPLETE                                 ${GREEN}║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
   
    echo -e "${WHITE}Summary Report:${NC}    ${PURPLE}$AUDIT_DIR/AUDIT_SUMMARY.txt${NC}"
    echo -e "${WHITE}Full Results:${NC}      ${PURPLE}$AUDIT_DIR/${NC}\n"
   
    cat "$AUDIT_DIR/AUDIT_SUMMARY.txt"
   
    echo ""
    read -p "Press ENTER to return to menu..."
}

# Single device scan
device_scan() {
    clear
    show_banner
    echo -e "\n${RED}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║${WHITE}                    TARGETED DEVICE ANALYSIS                           ${RED}║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
   
    echo -e -n "${WHITE}Enter target IP address:${NC} ${PURPLE}"
    read TARGET_IP
    echo -e "${NC}"
   
    # Validate IP
    if ! [[ $TARGET_IP =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        echo -e "${RED}[!] ERROR: Invalid IP address format${NC}\n"
        read -p "Press ENTER to return to menu..."
        return
    fi
   
    DATE=$(date +%Y%m%d_%H%M%S)
    DEVICE_DIR="$SCANS_DIR/device_${TARGET_IP}_$DATE"
    mkdir -p "$DEVICE_DIR"
   
    echo -e "${WHITE}Target Device:${NC}     ${PURPLE}$TARGET_IP${NC}"
    echo -e "${WHITE}Scan ID:${NC}           ${PURPLE}device_${TARGET_IP}_$DATE${NC}"
    echo -e "${WHITE}Output Path:${NC}       ${DIM}$DEVICE_DIR${NC}\n"
   
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}[!] WARNING: Root required for complete analysis${NC}\n"
    fi
   
    # Ping test
    echo -e "${ORANGE}[*]${NC} Testing connectivity..."
    if ping -c 1 -W 2 "$TARGET_IP" > /dev/null 2>&1; then
        echo -e "${GREEN}[+]${NC} Host is ${GREEN}ONLINE${NC}\n"
    else
        echo -e "${ORANGE}[!]${NC} Host not responding to ICMP (may be filtered)\n"
    fi
   
    # Quick scan
    echo -e "${ORANGE}[*]${NC} Performing quick port scan..."
    if [ "$EUID" -eq 0 ]; then
        sudo nmap -sS -F -T4 "$TARGET_IP" -oN "$DEVICE_DIR/quick_scan.txt" 2>&1 | while IFS= read -r line; do
            if [[ $line =~ "open" ]]; then
                PORT=$(echo "$line" | awk '{print $1}')
                SERVICE=$(echo "$line" | awk '{print $3}')
                echo -e "${GREEN}[+]${NC} ${PURPLE}$PORT${NC} - $SERVICE"
            fi
        done
    else
        nmap -sT -F -T4 "$TARGET_IP" -oN "$DEVICE_DIR/quick_scan.txt" 2>&1 | while IFS= read -r line; do
            if [[ $line =~ "open" ]]; then
                PORT=$(echo "$line" | awk '{print $1}')
                SERVICE=$(echo "$line" | awk '{print $3}')
                echo -e "${GREEN}[+]${NC} ${PURPLE}$PORT${NC} - $SERVICE"
            fi
        done
    fi
   
    echo ""
    echo -e "${ORANGE}[*]${NC} Deep analysis in progress (this may take several minutes)...\n"
   
    if [ "$EUID" -eq 0 ]; then
        # Full TCP scan
        echo -e "${DIM}├─ Full TCP port scan...${NC}"
        sudo nmap -sS -p- -T4 "$TARGET_IP" -oN "$DEVICE_DIR/tcp_full.txt" > /dev/null 2>&1
       
        # Service detection
        echo -e "${DIM}├─ Service version detection...${NC}"
        sudo nmap -sV -sC "$TARGET_IP" -oN "$DEVICE_DIR/services.txt" > /dev/null 2>&1
       
        # OS detection
        echo -e "${DIM}├─ Operating system fingerprinting...${NC}"
        sudo nmap -O "$TARGET_IP" -oN "$DEVICE_DIR/os_detection.txt" > /dev/null 2>&1
       
        # Vulnerability scan
        echo -e "${DIM}└─ Vulnerability assessment...${NC}\n"
        sudo nmap --script vuln "$TARGET_IP" -oN "$DEVICE_DIR/vulnerabilities.txt" > /dev/null 2>&1
    else
        nmap -sT -p- -T4 "$TARGET_IP" -oN "$DEVICE_DIR/tcp_full.txt" > /dev/null 2>&1
        nmap -sV -sC "$TARGET_IP" -oN "$DEVICE_DIR/services.txt" > /dev/null 2>&1
    fi
   
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${WHITE}                    DEVICE ANALYSIS COMPLETE                           ${GREEN}║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
   
    echo -e "${WHITE}Results Directory:${NC} ${PURPLE}$DEVICE_DIR${NC}\n"
   
    read -p "Press ENTER to return to menu..."
}

# Port sweep analyzer
port_sweep() {
    clear
    show_banner
    echo -e "\n${RED}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║${WHITE}                     RAPID PORT SWEEP ANALYZER                         ${RED}║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
   
    DATE=$(date +%Y%m%d_%H%M%S)
    OUTPUT="$SCANS_DIR/portsweep_$DATE"
   
    LOCAL_NETWORK=$(ip route | grep -v default | grep -E "192.168|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\." | head -1 | awk '{print $1}')
   
    echo -e "${WHITE}Target Network:${NC}    ${PURPLE}$LOCAL_NETWORK${NC}"
    echo -e "${WHITE}Scan Mode:${NC}         ${ORANGE}Fast (Top 100 ports)${NC}\n"
   
    echo -e "${ORANGE}[*]${NC} Initiating rapid port enumeration...\n"
   
    if [ "$EUID" -eq 0 ]; then
        sudo nmap -sS -F -T4 --open "$LOCAL_NETWORK" -oG "$OUTPUT.gnmap" 2>&1 | while IFS= read -r line; do
            if [[ $line =~ "Scanning" ]]; then
                IP=$(echo "$line" | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}')
                echo -e "${CYAN}[→]${NC} Sweeping ${PURPLE}$IP${NC}"
            elif [[ $line =~ "open" ]]; then
                PORT=$(echo "$line" | awk '{print $1}' | cut -d'/' -f1)
                echo -e "    ${GREEN}├─${NC} Port ${PURPLE}$PORT${NC} OPEN"
            fi
        done
    else
        echo -e "${RED}[!] Root privileges required for SYN scan${NC}"
        echo -e "${ORANGE}[*] Falling back to connect scan...${NC}\n"
        nmap -sT -F -T4 --open "$LOCAL_NETWORK" -oG "$OUTPUT.gnmap" 2>&1 | while IFS= read -r line; do
            if [[ $line =~ "Scanning" ]]; then
                IP=$(echo "$line" | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}')
                echo -e "${CYAN}[→]${NC} Sweeping ${PURPLE}$IP${NC}"
            elif [[ $line =~ "open" ]]; then
                PORT=$(echo "$line" | awk '{print $1}' | cut -d'/' -f1)
                echo -e "    ${GREEN}├─${NC} Port ${PURPLE}$PORT${NC} OPEN"
            fi
        done
    fi
   
    echo -e "\n${GREEN}[✓]${NC} Port sweep complete\n"
    echo -e "${WHITE}Results:${NC} ${PURPLE}$OUTPUT.gnmap${NC}\n"
   
    read -p "Press ENTER to return to menu..."
}

# View reports
view_reports() {
    clear
    show_banner
    echo -e "\n${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${WHITE}                        HISTORICAL SCAN REPORTS                        ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
   
    if [ ! -d "$SCANS_DIR" ] || [ -z "$(ls -A $SCANS_DIR 2>/dev/null)" ]; then
        echo -e "${ORANGE}[!]${NC} No scan reports found\n"
        read -p "Press ENTER to return to menu..."
        return
    fi
   
    echo -e "${WHITE}Available Reports:${NC}\n"
   
    COUNT=1
    for item in "$SCANS_DIR"/*; do
        if [ -e "$item" ]; then
            BASENAME=$(basename "$item")
            SIZE=$(du -sh "$item" 2>/dev/null | awk '{print $1}')
            MODIFIED=$(stat -c %y "$item" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1)
           
            if [ -d "$item" ]; then
                echo -e "${WHITE}[$COUNT]${NC} ${PURPLE}$BASENAME${NC} ${DIM}(Directory, $SIZE, Modified: $MODIFIED)${NC}"
            else
                echo -e "${WHITE}[$COUNT]${NC} ${PURPLE}$BASENAME${NC} ${DIM}($SIZE, Modified: $MODIFIED)${NC}"
            fi
            COUNT=$((COUNT + 1))
        fi
    done
   
    echo -e "\n${DIM}Scan directory: $SCANS_DIR${NC}\n"
   
    read -p "Press ENTER to return to menu..."
}

# System diagnostics
system_diagnostics() {
    clear
    show_banner
    echo -e "\n${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${WHITE}                        SYSTEM DIAGNOSTICS                             ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
   
    echo -e "${WHITE}Verifying security tool availability...${NC}\n"
   
    # Check nmap
    if command -v nmap &> /dev/null; then
        VERSION=$(nmap --version | head -1)
        echo -e "${GREEN}[✓]${NC} nmap:      ${GREEN}INSTALLED${NC} ${DIM}($VERSION)${NC}"
    else
        echo -e "${RED}[✗]${NC} nmap:      ${RED}NOT FOUND${NC}"
    fi
   
    # Check netcat
    if command -v nc &> /dev/null; then
        echo -e "${GREEN}[✓]${NC} netcat:    ${GREEN}INSTALLED${NC}"
    else
        echo -e "${ORANGE}[!]${NC} netcat:    ${ORANGE}NOT FOUND${NC}"
    fi
   
    # Check masscan
    if command -v masscan &> /dev/null; then
        echo -e "${GREEN}[✓]${NC} masscan:   ${GREEN}INSTALLED${NC}"
    else
        echo -e "${ORANGE}[!]${NC} masscan:   ${ORANGE}NOT FOUND${NC} ${DIM}(Optional)${NC}"
    fi
   
    # Check curl
    if command -v curl &> /dev/null; then
        echo -e "${GREEN}[✓]${NC} curl:      ${GREEN}INSTALLED${NC}"
    else
        echo -e "${RED}[✗]${NC} curl:      ${RED}NOT FOUND${NC}"
    fi
   
    echo -e "\n${WHITE}System Information:${NC}\n"
   
    echo -e "${WHITE}Hostname:${NC}          $(hostname)"
    echo -e "${WHITE}Kernel:${NC}            $(uname -r)"
    echo -e "${WHITE}Distribution:${NC}      $(lsb_release -d 2>/dev/null | cut -f2 || echo "Unknown")"
    echo -e "${WHITE}User:${NC}              $(whoami)"
   
    if [ "$EUID" -eq 0 ]; then
        echo -e "${WHITE}Privileges:${NC}        ${GREEN}ROOT${NC}"
    else
        echo -e "${WHITE}Privileges:${NC}        ${ORANGE}USER${NC} ${DIM}(sudo recommended)${NC}"
    fi
   
    echo -e "\n${WHITE}Suite Information:${NC}\n"
    echo -e "${WHITE}Installation:${NC}      ${PURPLE}$SUITE_DIR${NC}"
    echo -e "${WHITE}Scans Directory:${NC}   ${PURPLE}$SCANS_DIR${NC}"
    echo -e "${WHITE}Logs Directory:${NC}    ${PURPLE}$LOGS_DIR${NC}"
   
    TOTAL_SCANS=$(ls -1 "$SCANS_DIR" 2>/dev/null | wc -l)
    echo -e "${WHITE}Total Scans:${NC}       ${GREEN}$TOTAL_SCANS${NC}\n"
   
    read -p "Press ENTER to return to menu..."
}

# Main program loop
main() {
    while true; do
        show_banner
        show_network_info
        show_menu
       
        read -r choice
       
        case $choice in
            1) network_discovery ;;
            2) security_audit ;;
            3) device_scan ;;
            4)
                clear
                show_banner
                echo -e "\n${ORANGE}[!] IPv6 scanning module under development${NC}\n"
                read -p "Press ENTER to return to menu..."
                ;;
            5)
                clear
                show_banner
                echo -e "\n${ORANGE}[!] Continuous monitoring module under development${NC}\n"
                read -p "Press ENTER to return to menu..."
                ;;
            6) port_sweep ;;
            7) view_reports ;;
            8) continue ;;  # Refresh network info
            9) system_diagnostics ;;
            0)
                clear
                show_banner
                echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
                echo -e "${GREEN}║${WHITE}        Thank you for using Looting Larry Security Suite               ${GREEN}║${NC}"
                echo -e "${GREEN}║${WHITE}                    Stay secure, matey!                                ${GREEN}║${NC}"
                echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
                exit 0
                ;;
            *)
                echo -e "\n${RED}[!] Invalid selection${NC}"
                sleep 1
                ;;
        esac
    done
}

# Check for required tools
if ! command -v nmap &> /dev/null; then
    clear
    show_banner
    echo -e "\n${RED}[!] CRITICAL: nmap is not installed${NC}\n"
    echo -e "${WHITE}Install with:${NC} ${ORANGE}sudo apt install nmap${NC}\n"
    exit 1
fi

# Start the suite
main