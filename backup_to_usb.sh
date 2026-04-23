#!/bin/bash
# 🚀 USB BACKUP & SYNC UTILITY
# Intelligently copies Agent-Larry workspace to USB devices

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

SOURCE_DIR="/home/linuxlarry/Documents/Agent-Larry"
MOUNT_BASE="/media/linuxlarry"
BACKUP_NAME="Agent-Larry-Backup-$(date +%Y%m%d-%H%M%S)"
EXCLUDE_PATTERNS=(
    ".venv" "venv313" "__pycache__" "*.pyc" ".git" ".pytest_cache"
    "*.log" ".env" "chroma_db" ".DS_Store" "node_modules"
    ".vscode" ".idea" "*.egg-info" "build" "dist"
)

# ════════════════════════════════════════════════════════════════════════════
# FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}${BOLD}$1${NC}"
    echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

detect_usb_devices() {
    echo -e "${YELLOW}🔍 Scanning for USB devices...${NC}"
    local usb_list=()
    
    for mount_point in $(ls -d "$MOUNT_BASE"/* 2>/dev/null); do
        if [ -d "$mount_point" ]; then
            local dev=$(df "$mount_point" | tail -1 | awk '{print $1}')
            local size=$(df -h "$mount_point" | tail -1 | awk '{print $2}')
            local avail=$(df -h "$mount_point" | tail -1 | awk '{print $4}')
            
            if [[ "$dev" == /dev/sd* ]]; then
                usb_list+=("$mount_point|$dev|$size|$avail")
                echo -e "${GREEN}✓${NC} Found: $mount_point ($size, $avail free) - $dev"
            fi
        fi
    done
    
    if [ ${#usb_list[@]} -eq 0 ]; then
        echo -e "${RED}✗ No USB devices found in $MOUNT_BASE${NC}"
        return 1
    fi
    
    printf '%s\n' "${usb_list[@]}"
}

calculate_size() {
    local source=$1
    local total=0
    
    # Use du to calculate size
    total=$(du -sb "$source" 2>/dev/null | awk '{print $1}')
    echo $((total / 1024 / 1024))  # Convert to MB
}

copy_to_usb() {
    local source=$1
    local usb_mount=$2
    local dest="$usb_mount/$BACKUP_NAME"
    
    echo ""
    echo -e "${YELLOW}📋 Copy Details:${NC}"
    echo -e "  Source:      ${CYAN}$source${NC}"
    echo -e "  Destination: ${CYAN}$dest${NC}"
    
    # Check space
    local source_size=$(calculate_size "$source")
    local avail_size=$(df "$usb_mount" | tail -1 | awk '{print $4}')
    local avail_mb=$((avail_size / 1024))
    
    echo -e "  Source Size: ${YELLOW}~${source_size}MB${NC}"
    echo -e "  Available:   ${YELLOW}${avail_mb}MB${NC}"
    
    if [ $source_size -gt $avail_mb ]; then
        echo -e "${RED}✗ Not enough space on USB (need ${source_size}MB, have ${avail_mb}MB)${NC}"
        return 1
    fi
    
    # Create exclude pattern for rsync
    local exclude_opts=""
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        exclude_opts="$exclude_opts --exclude '$pattern'"
    done
    
    echo ""
    echo -e "${YELLOW}⏳ Copying files (this may take a few minutes)...${NC}"
    
    # Use rsync for efficient copying with progress
    eval "rsync -av --progress --delete $exclude_opts '$source/' '$dest/'" 2>&1 | tail -20
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Copy completed successfully!${NC}"
        
        # Create manifest file
        {
            echo "═══════════════════════════════════════════════════════════════"
            echo "🚀 AGENT-LARRY BACKUP MANIFEST"
            echo "═══════════════════════════════════════════════════════════════"
            echo ""
            echo "Backup Date:     $(date)"
            echo "Source:          $SOURCE_DIR"
            echo "Destination:     $dest"
            echo "USB Device:      $usb_mount"
            echo "Backup Name:     $BACKUP_NAME"
            echo ""
            echo "Core Application:"
            echo "  ✓ agent_v2.py             - Main agent (16 skills, MCP integration)"
            echo "  ✓ mcp_client.py           - MCP infrastructure (8+ servers)"
            echo "  ✓ production_rag.py       - RAG engine (ChromaDB + embeddings)"
            echo "  ✓ web_tools.py            - Web scraping utilities"
            echo "  ✓ model_router.py         - Model selection logic"
            echo "  ✓ telegram_bot.py         - Telegram integration (optional)"
            echo ""
            echo "Configuration:"
            echo "  ✓ larry_config.json       - Configuration (profiles, models, RAG)"
            echo "  ✓ mcp.json                - MCP server configuration"
            echo ""
            echo "RESTORE: cd $dest && chmod +x UNIFIED_SETUP.sh && ./UNIFIED_SETUP.sh"
            echo ""
            echo "Size: ~${source_size}MB | Skills: 16 | MCP Servers: 8+ | Profiles: 4"
        } > "$dest/BACKUP_MANIFEST.txt"
        
        echo -e "${GREEN}✓ Manifest created: BACKUP_MANIFEST.txt${NC}"
        return 0
    else
        echo -e "${RED}✗ Copy failed!${NC}"
        return 1
    fi
}

# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

print_header "🔄 USB BACKUP & SYNC UTILITY"

if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}✗ Source directory not found: $SOURCE_DIR${NC}"
    exit 1
fi

echo -e "${CYAN}Source Directory:${NC} $SOURCE_DIR"
echo -e "${CYAN}Mount Path:      ${NC} $MOUNT_BASE"
echo ""

# Detect USB devices
usb_devices=()
while IFS='|' read -r mount dev size avail; do
    usb_devices+=("$mount|$dev|$size|$avail")
done < <(detect_usb_devices)

if [ ${#usb_devices[@]} -eq 0 ]; then
    echo -e "${RED}No USB devices found. Exiting.${NC}"
    exit 1
fi

# If multiple devices, ask user to choose
if [ ${#usb_devices[@]} -gt 1 ]; then
    print_header "🔀 Multiple USB Devices Detected"
    
    for i in "${!usb_devices[@]}"; do
        IFS='|' read -r mount dev size avail <<< "${usb_devices[$i]}"
        echo -e "  ${YELLOW}[$i]${NC} $mount ($size) - $dev"
    done
    
    read -p "Select device (0-$((${#usb_devices[@]} - 1))): " device_idx
    
    if ! [[ "$device_idx" =~ ^[0-9]+$ ]] || [ "$device_idx" -ge ${#usb_devices[@]} ]; then
        echo -e "${RED}Invalid selection.${NC}"
        exit 1
    fi
else
    device_idx=0
fi

IFS='|' read -r usb_mount dev size avail <<< "${usb_devices[$device_idx]}"

# Confirm backup
print_header "⚠️ Confirm Backup"
echo -e "This will copy Agent-Larry to: ${CYAN}$usb_mount${NC}"
echo -e "Backup name: ${YELLOW}$BACKUP_NAME${NC}"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

# Perform backup
print_header "🚀 Starting Backup"
if copy_to_usb "$SOURCE_DIR" "$usb_mount"; then
    print_header "✅ BACKUP COMPLETE!"
    echo -e "${GREEN}✓ Agent-Larry backed up to: $usb_mount/$BACKUP_NAME${NC}"
    echo ""
    echo -e "${YELLOW}📝 Next Steps:${NC}"
    echo -e "  1. Eject USB safely"
    echo -e "  2. On target system, copy to ~/Documents/Agent-Larry"
    echo -e "  3. Run: ./UNIFIED_SETUP.sh"
    echo -e "  4. Start: python agent_v2.py"
    echo ""
    ls -lh "$usb_mount/$BACKUP_NAME" | head -5
else
    print_header "❌ BACKUP FAILED"
    echo -e "${RED}Check the output above for details.${NC}"
    exit 1
fi
