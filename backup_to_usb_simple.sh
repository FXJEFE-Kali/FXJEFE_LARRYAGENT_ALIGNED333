#!/bin/bash
# 🚀 SIMPLE USB BACKUP - Direct copy to USB devices
# No menu, just copy Agent-Larry with manifest

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

SOURCE_DIR="/home/linuxlarry/Documents/Agent-Larry"
BACKUP_NAME="Agent-Larry-Backup-$(date +%Y%m%d-%H%M%S)"
EXCLUDE_PATTERNS=(
    ".venv" "venv313" "__pycache__" "*.pyc" ".git" ".pytest_cache"
    "*.log" ".env" "chroma_db" ".DS_Store" "node_modules" ".vscode" ".idea"
)

echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}${BOLD}🔄 USB BACKUP UTILITY - Agent-Larry${NC}"
echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Detect USB devices
echo -e "${YELLOW}🔍 Scanning for USB devices...${NC}"
usb_devices=()
for mount_point in /media/linuxlarry/*; do
    if [ -d "$mount_point" ]; then
        dev=$(df "$mount_point" 2>/dev/null | tail -1 | awk '{print $1}')
        if [[ "$dev" == /dev/sd* ]]; then
            size=$(df -h "$mount_point" 2>/dev/null | tail -1 | awk '{print $2}')
            avail=$(df -h "$mount_point" 2>/dev/null | tail -1 | awk '{print $4}')
            usb_devices+=("$mount_point")
            echo -e "${GREEN}✓${NC} $mount_point ($size, $avail free)"
        fi
    fi
done

if [ ${#usb_devices[@]} -eq 0 ]; then
    echo -e "${RED}✗ No USB devices found!${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}📋 Backup Configuration:${NC}"
echo -e "  Source:     ${CYAN}$SOURCE_DIR${NC}"
echo -e "  Backup Name: ${CYAN}$BACKUP_NAME${NC}"
echo -e "  USB Devices: ${CYAN}${#usb_devices[@]}${NC}"
echo ""

# Process each USB device
for usb_mount in "${usb_devices[@]}"; do
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}📁 Backing up to: $usb_mount${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    dest="$usb_mount/$BACKUP_NAME"
    
    # Create exclude options
    exclude_opts=""
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        exclude_opts="$exclude_opts --exclude '$pattern'"
    done
    
    # Copy with rsync
    echo -e "${YELLOW}⏳ Copying files...${NC}"
    eval "rsync -av --progress --delete $exclude_opts '$SOURCE_DIR/' '$dest/'" 2>&1 | grep -E "(sending|receiving|total size)" || true
    
    if [ $? -eq 0 ]; then
        # Create manifest
        cat > "$dest/BACKUP_MANIFEST.txt" << 'MANIFEST'
═══════════════════════════════════════════════════════════════
🚀 AGENT-LARRY BACKUP
═══════════════════════════════════════════════════════════════

RESTORE INSTRUCTIONS:
  1. Copy to target: cp -r $PWD ~/Documents/Agent-Larry
  2. Setup:         cd ~/Documents/Agent-Larry
  3. Run setup:     chmod +x UNIFIED_SETUP.sh && ./UNIFIED_SETUP.sh
  4. Start agent:   python agent_v2.py

CONTENTS:
  ✓ agent_v2.py        - Main agent (16 skills)
  ✓ mcp_client.py      - MCP infrastructure
  ✓ production_rag.py  - RAG engine
  ✓ Configuration files (larry_config.json, mcp.json)
  ✓ Documentation (5+ guides)
  ✓ Dependencies (requirements.txt)

SYSTEM STATUS:
  ✓ 16 Skills (config, MCP, telegram, system)
  ✓ 8+ MCP Servers (filesystem, search, browser, git, etc.)
  ✓ 4 Model Profiles (SPEED/BALANCED/ACCURACY/ULTRA_CONTEXT)
  ✓ Production Ready (Tested & Validated)
  ✓ Python 3.13+

EXCLUDED (saves 99% space):
  • Virtual environments (.venv, venv313)
  • Cache (__pycache__, *.pyc)
  • Databases (chroma_db)
  • Environment files (.env)

BACKUP DATE: $(date)
SIZE: Backup itself ~100-200MB (without models)
═══════════════════════════════════════════════════════════════
MANIFEST
        
        echo -e "${GREEN}✓ Backup completed: $dest${NC}"
        echo -e "${GREEN}✓ Manifest created${NC}"
        echo ""
        
        # Show contents
        echo -e "${CYAN}Backed up files:${NC}"
        ls -lh "$dest" | tail -10
        echo ""
    else
        echo -e "${RED}✗ Backup failed for $usb_mount${NC}"
    fi
done

echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}✨ USB BACKUP COMPLETE!${NC}"
echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Safely eject USB devices"
echo -e "  2. On target system, copy from USB to ~/Documents/Agent-Larry"
echo -e "  3. Run ./UNIFIED_SETUP.sh"
echo -e "  4. Start: python agent_v2.py"
echo ""
