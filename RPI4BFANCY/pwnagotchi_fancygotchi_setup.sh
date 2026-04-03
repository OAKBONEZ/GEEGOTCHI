#!/bin/bash

#############################################################################
# Pwnagotchi + Fancygotchi 2.0 + Waveshare Display Setup Script
# Target: Raspberry Pi 4B (8GB) running jayofelony v2.9.5.4 64-bit
# Display: Waveshare 2.4"/2.8" SPI TFT (320x240, XPT2046 touch)
#############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Config
PWNAGOTCHI_CONFIG="/etc/pwnagotchi/config.toml"
PWNAGOTCHI_PLUGINS="/opt/pwnagotchi/plugins/custom"
FANCYGOTCHI_REPO="https://github.com/V0r-T3x/Fancygotchi.git"
DISPLAY_TYPE="waveshare_28v2"  # Options: waveshare_28v2, waveshare_3, etc.
DISPLAY_ROTATION="0"  # 0, 1, 2, 3 (0=normal, 1=90deg, 2=180deg, 3=270deg)

#############################################################################
# Utility Functions
#############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

check_rpi_model() {
    log_info "Checking Raspberry Pi model..."
    if ! grep -q "Raspberry Pi 4" /proc/cpuinfo; then
        log_warning "This script is optimized for RPi 4B. Detected: $(grep 'Model' /proc/cpuinfo | head -1)"
    else
        log_success "Raspberry Pi 4B detected"
    fi
}

check_os_arch() {
    log_info "Checking OS architecture..."
    ARCH=$(uname -m)
    if [[ "$ARCH" != "aarch64" ]]; then
        log_error "This script requires 64-bit OS. Detected: $ARCH"
        exit 1
    fi
    log_success "64-bit architecture confirmed"
}

#############################################################################
# SPI Enablement
#############################################################################

enable_spi() {
    log_info "Enabling SPI interface..."
    
    # Check if already enabled
    if raspi-gpio get 7 | grep -q "LVL=1"; then
        log_success "SPI already enabled"
        return
    fi
    
    # Enable via raspi-config (non-interactive)
    if command -v raspi-config &> /dev/null; then
        log_info "Enabling SPI via raspi-config..."
        raspi-config nonint do_spi 0
        log_success "SPI enabled"
    else
        log_warning "raspi-config not found. Manual SPI setup may be needed."
    fi
}

#############################################################################
# System Dependencies
#############################################################################

install_system_deps() {
    log_info "Installing system dependencies..."
    
    apt-get update -qq
    apt-get install -y \
        python3-pip \
        python3-dev \
        libopenjp2-7 \
        libtiff5 \
        libjasper1 \
        libharfbuzz0b \
        libwebp6 \
        libtiff5 \
        git \
        gcc \
        > /dev/null 2>&1
    
    log_success "System dependencies installed"
}

#############################################################################
# Python Dependencies
#############################################################################

install_python_deps() {
    log_info "Installing Python dependencies..."
    
    # Upgrade pip
    python3 -m pip install --upgrade pip setuptools wheel -q
    
    # Core display libraries
    python3 -m pip install --upgrade \
        pillow \
        luma.core \
        luma.lcd \
        RPi.GPIO \
        spidev \
        adafruit-circuitpython-ads1x15 \
        -q
    
    log_success "Python dependencies installed"
}

#############################################################################
# Fancygotchi Plugin Installation
#############################################################################

install_fancygotchi() {
    log_info "Installing Fancygotchi 2.0 plugin..."
    
    # Stop pwnagotchi during plugin install
    log_info "Stopping pwnagotchi service..."
    systemctl stop pwnagotchi 2>/dev/null || log_warning "pwnagotchi service not running"
    
    # Create custom plugins directory if it doesn't exist
    mkdir -p "$PWNAGOTCHI_PLUGINS"
    
    # Clone Fancygotchi
    if [ -d "$PWNAGOTCHI_PLUGINS/Fancygotchi" ]; then
        log_info "Fancygotchi directory exists, updating..."
        cd "$PWNAGOTCHI_PLUGINS/Fancygotchi"
        git pull origin main -q
    else
        log_info "Cloning Fancygotchi repository..."
        git clone "$FANCYGOTCHI_REPO" "$PWNAGOTCHI_PLUGINS/Fancygotchi" -q
    fi
    
    log_success "Fancygotchi plugin installed"
}

#############################################################################
# Config File Modifications
#############################################################################

backup_config() {
    log_info "Backing up pwnagotchi config..."
    if [[ -f "$PWNAGOTCHI_CONFIG" ]]; then
        BACKUP_FILE="${PWNAGOTCHI_CONFIG}.backup.$(date +%s)"
        cp "$PWNAGOTCHI_CONFIG" "$BACKUP_FILE"
        log_success "Config backed up to: $BACKUP_FILE"
    else
        log_warning "No existing config at $PWNAGOTCHI_CONFIG — a minimal one will be created"
    fi
}

ensure_config_exists() {
    if [[ -f "$PWNAGOTCHI_CONFIG" ]]; then
        return
    fi
    log_info "Creating minimal config.toml..."
    mkdir -p "$(dirname "$PWNAGOTCHI_CONFIG")"
    cat > "$PWNAGOTCHI_CONFIG" << 'EOF'
[main]
name = "pwnagotchi"

[ui.display]
enabled = true
type = "waveshare_28v2"
rotation = 0
color = "black"
EOF
    log_success "Minimal config created at $PWNAGOTCHI_CONFIG"
}

update_display_config() {
    log_info "Updating display configuration..."
    
    # Use Python to safely update TOML (handles comments and formatting)
    python3 << EOF
import re

config_file = "$PWNAGOTCHI_CONFIG"

with open(config_file, 'r') as f:
    content = f.read()

# Update display settings
updates = {
    r'ui\.display\.enabled\s*=\s*\w+': 'ui.display.enabled = true',
    r'ui\.display\.type\s*=\s*"[^"]*"': f'ui.display.type = "$DISPLAY_TYPE"',
    r'ui\.display\.rotation\s*=\s*\d+': f'ui.display.rotation = $DISPLAY_ROTATION',
    r'ui\.display\.color\s*=\s*"[^"]*"': 'ui.display.color = "black"',
}

for pattern, replacement in updates.items():
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
    else:
        # Add to [ui.display] section if not found
        if '[ui.display]' in content:
            insert_point = content.find('[ui.display]') + len('[ui.display]')
            content = content[:insert_point] + f'\n{replacement}' + content[insert_point:]

# Fancygotchi-specific config
fancygotchi_config = '''

# Fancygotchi Plugin
[main.plugins.fancygotchi]
enabled = true
theme = ''
rotation = 0
'''

if '[main.plugins.fancygotchi]' not in content:
    content += fancygotchi_config

with open(config_file, 'w') as f:
    f.write(content)

print("Config updated successfully")
EOF
    
    log_success "Display configuration updated"
}

#############################################################################
# GPIO & SPI Bus Check
#############################################################################

verify_gpio() {
    log_info "Verifying GPIO and SPI bus..."
    
    python3 << EOF
import os
import sys

# Check SPI device
spi_device = "/dev/spidev0.0"
if os.path.exists(spi_device):
    print("✓ SPI device found: /dev/spidev0.0")
else:
    print("✗ SPI device NOT found. Enable SPI in raspi-config")
    sys.exit(1)

# Check if we can import RPi.GPIO
try:
    import RPi.GPIO as GPIO
    print("✓ RPi.GPIO module available")
except ImportError:
    print("✗ RPi.GPIO import failed")
    sys.exit(1)

# Check if display libraries are available
try:
    from luma.lcd.device import st7789
    from PIL import Image
    print("✓ Display libraries (luma.lcd, PIL) available")
except ImportError as e:
    print(f"✗ Display library import failed: {e}")
    sys.exit(1)

print("\nAll GPIO/SPI checks passed!")
EOF
    
    log_success "GPIO/SPI verification complete"
}

#############################################################################
# Plugin Enablement
#############################################################################

enable_fancygotchi_plugin() {
    log_info "Enabling Fancygotchi plugin in config..."
    
    python3 << EOF
import re

config_file = "$PWNAGOTCHI_CONFIG"

with open(config_file, 'r') as f:
    content = f.read()

# Ensure [main.plugins.fancygotchi] section exists
if '[main.plugins.fancygotchi]' not in content:
    # Add before other plugin sections
    insert_marker = '[main.plugins'
    if insert_marker in content:
        insert_point = content.find(insert_marker)
        new_section = '''[main.plugins.fancygotchi]
enabled = true
theme = ''
rotation = 0

'''
        content = content[:insert_point] + new_section + content[insert_point:]
    else:
        content += '\n[main.plugins.fancygotchi]\nenabled = true\ntheme = \'\'\n'

# Ensure it's enabled
content = re.sub(
    r'\[main\.plugins\.fancygotchi\].*?enabled\s*=\s*\w+',
    lambda m: m.group(0).replace('enabled = false', 'enabled = true').replace('enabled=false', 'enabled=true'),
    content,
    flags=re.DOTALL
)

with open(config_file, 'w') as f:
    f.write(content)

print("Fancygotchi plugin enabled in config")
EOF
    
    log_success "Fancygotchi plugin enabled"
}

#############################################################################
# Restart Services
#############################################################################

restart_pwnagotchi() {
    log_info "Restarting pwnagotchi service..."
    
    systemctl restart pwnagotchi
    
    # Wait for service to stabilize
    sleep 3
    
    if systemctl is-active --quiet pwnagotchi; then
        log_success "Pwnagotchi service running"
    else
        log_error "Pwnagotchi service failed to start"
        log_info "Check logs with: journalctl -u pwnagotchi -n 50"
        return 1
    fi
}

#############################################################################
# Summary & Verification
#############################################################################

print_summary() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Pwnagotchi + Fancygotchi Setup Complete!${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Configuration:"
    echo "  Display Type:    $DISPLAY_TYPE"
    echo "  Rotation:        $DISPLAY_ROTATION"
    echo "  Config File:     $PWNAGOTCHI_CONFIG"
    echo "  Fancygotchi:     $PWNAGOTCHI_PLUGINS/Fancygotchi"
    echo ""
    echo "Next Steps:"
    echo "  1. Access web UI: http://10.0.0.2:8080 (via USB)"
    echo "  2. Go to Plugins → Fancygotchi → Enable"
    echo "  3. Refresh browser to load Fancygotchi UI"
    echo "  4. Select a theme (default or custom)"
    echo ""
    echo "Troubleshooting:"
    echo "  • Display not showing? Check rotation value (0-3)"
    echo "  • SPI not working? Run: raspi-gpio set 7 ps=10"
    echo "  • Plugin not loading? Check: journalctl -u pwnagotchi -n 50"
    echo "  • Config backup at: ${PWNAGOTCHI_CONFIG}.backup.*"
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

#############################################################################
# Main Execution
#############################################################################

main() {
    log_info "Starting Pwnagotchi + Fancygotchi Setup"
    log_info "Target: RPi 4B 64-bit with Waveshare Display"
    echo ""
    
    # Pre-flight checks
    check_root
    check_rpi_model
    check_os_arch
    echo ""
    
    # Installation steps
    enable_spi
    install_system_deps
    install_python_deps
    backup_config
    ensure_config_exists
    install_fancygotchi
    update_display_config
    enable_fancygotchi_plugin
    verify_gpio
    restart_pwnagotchi
    
    print_summary
}

# Run main function
main

exit 0
