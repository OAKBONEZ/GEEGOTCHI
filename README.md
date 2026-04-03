# Fancygotchi - Pwnagotchi with Display Plugin

A complete setup guide and configuration files for running **Pwnagotchi** with the **Fancygotchi** display plugin on a Raspberry Pi 4B with Waveshare 2.8" SPI TFT display.

## 📋 Project Overview

This repository contains:
- **Setup scripts** for automated installation on Raspberry Pi
- **Configuration files** with SSID whitelist (includes "Vegemite Virus Vault")
- **Display test utilities** for hardware verification
- **Comprehensive documentation** for hardware wiring and troubleshooting

## 🎯 What is Pwnagotchi?

Pwnagotchi is a "Tamagotchi-like" AI-powered WiFi security tool that:
- Scans for nearby WiFi networks (airodump-ng)
- Learns from WiFi interactions using machine learning
- Captures handshakes to build a dataset
- Can perform deauthentication attacks on target networks

**Important:** Only use on networks you own or have explicit permission to test.

## 🎨 What is Fancygotchi?

Fancygotchi is a custom display plugin that renders the Pwnagotchi interface on external SPI TFT displays, providing:
- Live status visualization
- Network scanning display
- AI training feedback
- Theme support (default, cyber, custom)

## 🔧 Hardware Setup

### Requirements
- **Raspberry Pi 4B** (8GB RAM recommended)
- **Waveshare 2.8" SPI TFT Display** (320x240, XPT2046 touchscreen)
- **GPIO jumper wires** for SPI/DC/RST connections
- **3.3V power supply** (5V will damage the display!)
- **USB-C power** (minimum 3A for RPi 4B)

### Pin Configuration
| Function | GPIO | Physical Pin |
|----------|------|--------------|
| GND | GND | 6, 9, 14, 20, 25, 30, 34, 39 |
| VCC | 3.3V | 1, 17 |
| SPI_CLK | GPIO11 | 23 |
| SPI_MOSI | GPIO10 | 19 |
| CS | GPIO8 | 24 |
| DC | GPIO25 | 22 |
| RST | GPIO27 | 13 |
| LED (Backlight) | 3.3V | 1 or 17 |

See `SETUP_CHECKLIST.md` for detailed wiring diagram.

## 🚀 Quick Start

### Step 1: Transfer Files to RPi
```powershell
scp "RPI4BFANCY\pwnagotchi_fancygotchi_setup.sh" pi@10.0.0.2:/tmp/
scp "RPI4BFANCY\waveshare_display_test.py" pi@10.0.0.2:/tmp/
```

### Step 2: SSH and Test Display
```bash
ssh pi@10.0.0.2
sudo python3 /tmp/waveshare_display_test.py
```

### Step 3: Run Setup Script
```bash
chmod +x /tmp/pwnagotchi_fancygotchi_setup.sh
sudo /tmp/pwnagotchi_fancygotchi_setup.sh
```

### Step 4: Enable in Web UI
1. Open `http://10.0.0.2:8080`
2. Go to **Settings** → **Plugins**
3. Toggle **Fancygotchi** to **ON**
4. Click **Refresh**

## ⚙️ Configuration

### SSID Whitelist
The `config.toml` file includes a whitelist of SSIDs that Pwnagotchi will **ignore**:

```toml
[main.whitelist]
ssids = [
  "Vegemite Virus Vault"
]
```

**Add more SSIDs as needed to protect your own networks.**

### Display Rotation
If your display appears upside-down, adjust rotation in `config.toml`:
```toml
[ui.display]
rotation = 0   # 0=normal, 1=90°, 2=180°, 3=270°
```

Then restart the service:
```bash
sudo systemctl restart pwnagotchi
```

## 📂 File Structure

```
.
├── README.md                              # This file
├── config.toml                            # Main Pwnagotchi configuration
├── .gitignore                             # Git ignore patterns
├── QUICK_SETUP_GUIDE.md                   # Step-by-step setup guide
├── SETUP_CHECKLIST.md                     # Hardware checklist & wiring
├── setup-fancygotchi.sh                   # Fancygotchi setup script
├── waveshare_display_test.py              # Display hardware test
└── RPI4BFANCY/
    ├── pwnagotchi_fancygotchi_setup.sh    # Main installer script
    ├── waveshare_display_test.py          # Display test utility
    └── SETUP_CHECKLIST.md                 # Reference guide
```

## 🧪 Testing

### Display Test
Before running the full setup, test your display hardware:
```bash
sudo python3 /tmp/waveshare_display_test.py
```

Expected output:
- ✓ ARM architecture detected
- ✓ SPI device found
- ✓ Display initialized (ST7789 detected)
- ✓ Test pattern rendered
- ✓ All checks passed

### Verify Installation
After setup completes:
```bash
# Check service status
systemctl status pwnagotchi

# View logs
journalctl -u pwnagotchi -n 50

# Test Python imports
python3 -c "from luma.lcd.device import st7789; print('OK')"

# Verify plugin installed
ls -la /opt/pwnagotchi/plugins/custom/Fancygotchi/
```

## 🔧 Troubleshooting

### Display shows nothing
1. Check GPIO wiring (especially VCC - must be 3.3V only!)
2. Enable SPI: `sudo raspi-config nonint do_spi 0`
3. Test again: `sudo python3 /tmp/waveshare_display_test.py`
4. Check rotation setting in config.toml

### Plugin not loading
```bash
# Check logs
journalctl -u pwnagotchi -n 20 | grep -i fancygotchi

# Restart service
sudo systemctl restart pwnagotchi

# Verify config
grep -A 5 "fancygotchi" /etc/pwnagotchi/config.toml
```

### SPI not enabled
```bash
sudo raspi-config nonint do_spi 0
sudo reboot
```

### Permission errors
```bash
sudo usermod -aG gpio pi
sudo usermod -aG spi pi
sudo reboot
```

## 📖 Resources

- [Pwnagotchi Documentation](https://pwnagotchi.org)
- [jayofelony Pwnagotchi GitHub](https://github.com/jayofelony/pwnagotchi)
- [Fancygotchi GitHub](https://github.com/V0r-T3x/Fancygotchi)
- [Waveshare Display Documentation](https://www.waveshare.com/wiki/2.8inch_RPi_LCD_(A))
- [RPi GPIO Pinout](https://pinout.xyz/)

## ⚠️ Legal & Ethical Notice

**Pwnagotchi is designed for WiFi security testing and research.**

- ✅ Use on networks you own
- ✅ Use with explicit written permission from network owner
- ✅ Use for security education and learning
- ❌ Do NOT use for unauthorized access
- ❌ Do NOT use for illegal activities

Ensure compliance with all local laws and regulations regarding wireless device operation and testing.

## 📝 License

Configuration files and documentation are provided as-is for educational purposes.

---

**Last Updated:** April 2026
**Target System:** Raspberry Pi 4B 8GB + Waveshare 2.8" Display
**Pwnagotchi Version:** 2.9.5.4 (jayofelony)
**Fancygotchi Version:** 2.0
