#!/bin/bash
# Fancygotchi setup for Jayofelony Pwnagotchi
# Display: LCDwiki MPI2801 2.8" ILI9341 (320x240) — Pi HDR pin 15=GPIO22 (DC/LCD_RS), pin 13=GPIO27 (RST)
# Pin table: https://www.lcdwiki.com/2.8inch_RPi_Display
# Target: RPi 4B running jayofelony image
# Run as: sudo bash setup-fancygotchi.sh

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
info() { echo -e "${BLUE}[..]${NC} $1"; }
warn() { echo -e "${YELLOW}[!!]${NC} $1"; }
fail() { echo -e "${RED}[!!]${NC} $1"; exit 1; }

[[ $EUID -ne 0 ]] && fail "Run as root: sudo bash setup-fancygotchi.sh"

CONFIG="/etc/pwnagotchi/config.toml"
CONFD="/etc/pwnagotchi/conf.d"
PLUGINS="/usr/local/share/pwnagotchi/custom-plugins"
LCDCONFIG="/home/pi/.pwn/lib/python3.11/site-packages/pwnagotchi/ui/hw/libs/waveshare/lcd/lcdconfig.py"

echo ""
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Fancygotchi + MPI2801 Display Setup${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo ""

# ── 1. Enable SPI ────────────────────────────────────────────
info "Enabling SPI..."
raspi-config nonint do_spi 0 2>/dev/null && ok "SPI enabled" || ok "SPI already enabled"

if [ -e /dev/spidev0.0 ]; then
    ok "SPI device /dev/spidev0.0 present"
else
    warn "SPI device not found — reboot may be needed after setup"
fi

# ── 2. Patch DC pin for MPI2801 (GPIO22 instead of GPIO25) ──
info "Patching display driver for MPI2801 (DC=GPIO22)..."

if [ -f "$LCDCONFIG" ]; then
    cp "$LCDCONFIG" "${LCDCONFIG}.bak"
    # Change dc=25 to dc=22 in the __init__ default parameter
    sed -i 's/dc=25/dc=22/' "$LCDCONFIG"
    ok "Patched DC pin: GPIO25 → GPIO22"
    info "Verify:"
    grep "dc=" "$LCDCONFIG" | head -1 | sed 's/^/  /'
else
    fail "lcdconfig.py not found at $LCDCONFIG"
fi

# ── 3. Create config.toml ────────────────────────────────────
info "Creating config.toml..."

mkdir -p "$(dirname $CONFIG)"
mkdir -p "$CONFD"

if [ -f "$CONFIG" ]; then
    cp "$CONFIG" "${CONFIG}.bak.$(date +%s)"
    ok "Existing config backed up"
fi

cat > "$CONFIG" << 'TOML'
ui.fps = 1
ui.display.enabled = true
ui.display.type = "wavesharelcd2in4"
ui.display.rotation = 0

main.plugins.Fancygotchi.enabled = true
main.plugins.Fancygotchi.rotation = 0
main.plugins.Fancygotchi.theme = ""
TOML

ok "config.toml created at $CONFIG"
info "Contents:"
cat "$CONFIG" | sed 's/^/  /'

# ── 4. Install Fancygotchi plugin ────────────────────────────
info "Downloading Fancygotchi plugin..."
mkdir -p "$PLUGINS"
curl -sS -o "$PLUGINS/Fancygotchi.py" -JL \
  https://raw.githubusercontent.com/V0r-T3x/Fancygotchi/main/Fancygotchi.py

if [ -f "$PLUGINS/Fancygotchi.py" ]; then
    ok "Fancygotchi.py installed to $PLUGINS/"
else
    fail "Download failed — check internet connection"
fi

# ── 5. Restart pwnagotchi ─────────────────────────────────────
echo ""
info "Restarting pwnagotchi service..."
systemctl restart pwnagotchi
sleep 5

if systemctl is-active --quiet pwnagotchi; then
    ok "Pwnagotchi is running"
else
    warn "Service may need a moment — checking logs..."
    journalctl -u pwnagotchi -n 15 --no-pager 2>/dev/null
fi

# ── Done ──────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Setup complete!${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo ""
echo "  Display:      MPI2801 2.8\" ILI9341 (320x240)"
echo "  Driver:       wavesharelcd2in4 (patched DC=GPIO22)"
echo "  Plugin:       $PLUGINS/Fancygotchi.py"
echo "  Config:       $CONFIG"
echo "  Driver patch: $LCDCONFIG"
echo ""
echo "  Next steps:"
echo "    1. If no SPI device, reboot: sudo reboot"
echo "    2. Open http://10.0.0.2:8080"
echo "    3. Plugins → Fancygotchi → Enable"
echo ""
echo "  If display is upside down:"
echo "    sudo nano $CONFIG"
echo "    Change: ui.display.rotation = 2"
echo "    sudo systemctl restart pwnagotchi"
echo ""
echo "  To undo DC pin patch:"
echo "    sudo cp ${LCDCONFIG}.bak ${LCDCONFIG}"
echo "    sudo systemctl restart pwnagotchi"
echo ""
