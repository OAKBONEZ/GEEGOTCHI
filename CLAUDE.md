# CLAUDE.md - GEEGOTCHI Project Guide

## Project Overview

GEEGOTCHI is a Pwnagotchi setup and configuration project for a **Raspberry Pi 4B** with the **Fancygotchi** display plugin and a **Waveshare 2.8" SPI TFT display** (320x240). Pwnagotchi is an AI-powered WiFi security tool that learns from WiFi interactions and captures WPA handshakes.

**Target hardware:** Raspberry Pi 4B 8GB running jayofelony Pwnagotchi v2.9.5.4 (Raspberry Pi OS 64-bit)
**Target IP:** `10.0.0.2` (USB Ethernet gadget interface)
**Web UI:** `http://10.0.0.2:8080`

## Repository Structure

```
GEEGOTCHI/
├── config.toml                            # Pwnagotchi configuration (deploy to /etc/pwnagotchi/)
├── setup-fancygotchi.sh                   # Fancygotchi setup script
├── waveshare_display_test.py              # Display hardware diagnostic utility
├── waveshare_display_test_1.py            # Alternate display test version
├── init-git.ps1                           # PowerShell script for Windows git init
├── RPI4BFANCY/
│   ├── pwnagotchi_fancygotchi_setup.sh    # Main installer script (run this on the RPi)
│   ├── waveshare_display_test.py          # RPi-variant display test
│   └── SETUP_CHECKLIST.md                 # Hardware wiring reference
├── README.md
├── QUICK_SETUP_GUIDE.md
├── SETUP_CHECKLIST.md
└── GIT_INIT_SUMMARY.md
```

## Tech Stack

- **Bash** - Setup and installation scripts
- **Python 3** - Display test utilities and hardware diagnostics
- **TOML** - Pwnagotchi configuration format
- **Key Python libraries:** Pillow, luma.core, luma.lcd, RPi.GPIO, spidev

## Deployment Workflow

This project runs on a Raspberry Pi - there is no local build step. Files are transferred via SCP and executed on the RPi.

### Transfer files to RPi
```bash
scp RPI4BFANCY/pwnagotchi_fancygotchi_setup.sh pi@10.0.0.2:/tmp/
scp RPI4BFANCY/waveshare_display_test.py pi@10.0.0.2:/tmp/
scp config.toml pi@10.0.0.2:/tmp/
```

### On the RPi: Test display hardware first
```bash
ssh pi@10.0.0.2
sudo python3 /tmp/waveshare_display_test.py
```

### On the RPi: Run full setup
```bash
chmod +x /tmp/pwnagotchi_fancygotchi_setup.sh
sudo /tmp/pwnagotchi_fancygotchi_setup.sh
```

### On the RPi: Deploy config
```bash
sudo cp /tmp/config.toml /etc/pwnagotchi/config.toml
sudo systemctl restart pwnagotchi
```

## Verification Commands (run on RPi)

```bash
# Check plugin installed
ls -la /opt/pwnagotchi/plugins/custom/Fancygotchi/

# Verify config applied
grep -A 5 "fancygotchi" /etc/pwnagotchi/config.toml

# View live logs
journalctl -u pwnagotchi -f

# Check service status
systemctl status pwnagotchi

# Test Python display imports
python3 -c "from luma.lcd.device import st7789; print('OK')"
```

## Key Configuration: config.toml

The `config.toml` file configures the Pwnagotchi system. Key settings:

| Setting | Value | Notes |
|---|---|---|
| `ui.display.type` | `wavesharelcd2in4` | 320x240 SPI TFT display driver |
| `ui.display.rotation` | configurable | 0=normal, 1=90°, 2=180°, 3=270° |
| `ui.web.port` | `8080` | Web UI port |
| `main.plugins.fancygotchi` | enabled | theme="cyber", rotation=90 |
| Handshakes | `/home/pi/handshakes` | WPA handshake capture directory |

**SSID Whitelist:** The `main.whitelist` array in `config.toml` lists networks that Pwnagotchi will NOT attack. Always keep your own networks in this list. The placeholder `"YOUR_SSID_HERE"` must be replaced with real values before deployment.

**Sensitive values:** Passwords, real SSIDs, and API keys use placeholder values in the repo. Never commit real credentials.

## Display Hardware

Two supported display variants:
- **LCDwiki MPI2801** - ILI9341 chip, DC=GPIO22
- **Waveshare-style** - ST7789 chip, DC=GPIO25

SPI connections: MOSI=GPIO10, SCLK=GPIO11, CS=GPIO8, RST=GPIO24

See `SETUP_CHECKLIST.md` and `RPI4BFANCY/SETUP_CHECKLIST.md` for full GPIO wiring diagrams.

## Important Notes

- **This is a WiFi security tool.** Only use it to test networks you own or have explicit written permission to test. Capturing handshakes from networks you don't own is illegal in most jurisdictions.
- Scripts use color-coded output: GREEN=success, RED=error, YELLOW=warning, BLUE=info.
- The installer script (`pwnagotchi_fancygotchi_setup.sh`) creates backups of existing configs before modifying them.
- Pwnagotchi's web UI has authentication **disabled by default** in this config — only expose it on a trusted network.
