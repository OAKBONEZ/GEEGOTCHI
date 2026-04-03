#!/usr/bin/env markdown

# Pwnagotchi + Fancygotchi 2.0 Setup Checklist

## Pre-Flight Verification

### Hardware Checklist
- [ ] RPi 4B with 8GB RAM
- [ ] Waveshare 2.4" or 2.8" SPI TFT display (320x240, XPT2046)
- [ ] MicroSD card (16GB+ recommended)
- [ ] USB-C power supply (minimum 3A)
- [ ] USB-A to USB-C cable (for flashing/connection)
- [ ] Breadboard or jumper wires (for GPIO testing)
- [ ] Test meter (optional, for SPI voltage verification)

### Software Checklist
- [ ] jayofelony Pwnagotchi v2.9.5.4 64-bit image flashed to SD card
- [ ] RPi 4B boots successfully (green LED activity)
- [ ] SSH access working: `ssh pi@10.0.0.2`
- [ ] Web UI accessible: `http://10.0.0.2:8080`
- [ ] Git installed: `which git`

---

## GPIO Wiring (Critical!)

### Waveshare SPI Display Pin Mapping

| Signal | RPi GPIO | Physical Pin | Waveshare Pin | Notes |
|--------|----------|--------------|---------------|-------|
| GND    | GND      | 6, 9, 14, 20, 25, 30, 34, 39 | GND | Multiple pins available |
| VCC    | 3.3V     | 1, 17        | VCC           | **DO NOT use 5V** |
| SPI_CLK | GPIO11  | 23           | CLK           | SPI clock |
| SPI_MOSI | GPIO10 | 19           | DIN           | SPI data out |
| SPI_MISO | GPIO9  | 21           | (not used)    | Can leave unconnected |
| CE/CS  | GPIO8    | 24           | CS            | Chip select |
| DC     | GPIO25   | 22           | DC            | Data/Command |
| RST    | GPIO27   | 13           | RST           | Reset (pull low momentarily) |
| LED    | 3.3V     | 1 or 17      | LED/BL        | Backlight (brightness) |

### Wiring Diagram ASCII
```
RPi 4B (Top view)
┌─────────────────────┐
│  1(3.3V) 2(5V)     │
│  3(SDA)  4(5V)     │
│  5(SCL)  6(GND)    │
│  7(CE0)  8(CS)     │──→ Waveshare CS
│  9(GND)  10(MOSI)  │──→ Waveshare DIN
│ 11(CLK)  12(MISO)  │──→ Waveshare (unused)
│ 13(RST)  14(GND)   │
│ 15(RXD)  16(TXD)   │
│ 17(3.3V) 18(GPIO)  │
│ 19(MOSI) 20(GND)   │
│ 21(MISO) 22(DC)    │──→ Waveshare DC
│ 23(CLK)  24(CS)    │
│ 25(GND)  26(GPIO)  │
└─────────────────────┘

GPIO27 (Pin 13) connects to Waveshare RST
GPIO25 (Pin 22) connects to Waveshare DC
GPIO11 (Pin 23) connects to Waveshare CLK
GPIO10 (Pin 19) connects to Waveshare DIN
GPIO8 (Pin 24) connects to Waveshare CS
3.3V (Pin 1/17) connects to Waveshare VCC
GND (any pin) connects to Waveshare GND & LED
```

### Wiring Verification Checklist
- [ ] All GND pins connected (RPi → Display)
- [ ] VCC connected to 3.3V only (NOT 5V)
- [ ] SPI pins correct: CLK, MOSI, MISO, CS
- [ ] DC pin to GPIO25
- [ ] RST pin to GPIO27
- [ ] Backlight (LED) connected to 3.3V
- [ ] No loose wires or cold solder joints
- [ ] Continuity checked with multimeter

---

## Setup Procedure

### Step 1: Boot into Pwnagotchi
```bash
# Insert SD card into RPi 4B
# Power on via USB-C
# Wait 30-40 seconds for boot
# Verify green LED activity
```

### Step 2: SSH into RPi
```bash
# From your computer:
ssh pi@10.0.0.2
# Default password: raspberry (or pwnagotchi)
```

### Step 3: Run Pre-Flight Diagnostics (Optional)
```bash
# Test the display without setup
cd ~
sudo python3 waveshare_display_test.py
# Should show test pattern on display
```

### Step 4: Run Setup Script
```bash
# Make script executable
chmod +x pwnagotchi_fancygotchi_setup.sh

# Run with sudo
sudo ./pwnagotchi_fancygotchi_setup.sh

# Script will:
# ✓ Enable SPI interface
# ✓ Install system dependencies
# ✓ Install Python packages (pillow, luma.core, luma.lcd)
# ✓ Clone Fancygotchi 2.0 plugin
# ✓ Update config.toml with display settings
# ✓ Verify GPIO/SPI connectivity
# ✓ Restart pwnagotchi service
```

### Step 5: Enable Fancygotchi in Web UI
```
1. Open: http://10.0.0.2:8080
2. Navigate: Settings → Plugins
3. Find: "fancygotchi"
4. Toggle: ON
5. Click: Refresh
6. Navigate back to main UI (should show Fancygotchi)
```

### Step 6: Select Theme
```
1. In Fancygotchi UI: Click on theme selector
2. Options should include:
   - default (basic theme)
   - cyber (neon matrix style)
   - custom themes (if you create any)
3. Select and apply
```

---

## Display Type Selection

Edit `/etc/pwnagotchi/config.toml` and set:

```toml
ui.display.type = "waveshare_28v2"  # for 2.8" or 2.4"
```

### Alternative Display Types (if needed)
- `waveshare_2` - Old 2" display
- `waveshare_3` - 3.5" display
- `st7789` - Generic ST7789 controller
- `ili9341` - ILI9341 controller (some variants)

### Rotation Settings
```toml
ui.display.rotation = 0   # Normal (0°)
ui.display.rotation = 1   # Rotated 90°
ui.display.rotation = 2   # Rotated 180°
ui.display.rotation = 3   # Rotated 270°
```

---

## Troubleshooting

### Display Not Showing Anything
**Check:**
1. GPIO wiring (recheck pin assignments)
2. SPI enabled: `raspi-gpio get 11` should show output
3. Power to display (3.3V on VCC, not 5V)
4. Rotation setting (try different values: 0, 1, 2, 3)

**Test:**
```bash
sudo python3 waveshare_display_test.py
```

### SPI Not Enabled
```bash
# Enable via raspi-config
sudo raspi-config nonint do_spi 0

# Or manually via device tree
sudo nano /boot/firmware/config.txt
# Add: dtparam=spi=on
```

### Plugin Not Loading
```bash
# Check plugin directory
ls -la /opt/pwnagotchi/plugins/custom/Fancygotchi/

# Check service logs
journalctl -u pwnagotchi -n 50

# Restart service
sudo systemctl restart pwnagotchi
```

### Permission Errors
```bash
# Ensure pi user has GPIO/SPI access
sudo usermod -aG gpio pi
sudo usermod -aG spi pi

# Reboot for changes to take effect
sudo reboot
```

### Display Inverted/Upside-Down
```bash
# Edit config.toml
sudo nano /etc/pwnagotchi/config.toml

# Change rotation value:
ui.display.rotation = 2  # For 180° (inverted)

# Restart
sudo systemctl restart pwnagotchi
```

---

## Quick Command Reference

### Service Management
```bash
sudo systemctl start pwnagotchi     # Start service
sudo systemctl stop pwnagotchi      # Stop service
sudo systemctl restart pwnagotchi   # Restart service
sudo systemctl status pwnagotchi    # Check status
journalctl -u pwnagotchi -n 50      # View logs
```

### Config & Files
```bash
sudo nano /etc/pwnagotchi/config.toml          # Edit main config
nano /opt/pwnagotchi/plugins/custom/Fancygotchi/config.toml  # Edit Fancygotchi config
ls -la /opt/pwnagotchi/plugins/custom/         # List plugins
```

### GPIO/SPI Testing
```bash
raspi-gpio get 25      # Check GPIO25 (DC pin) status
raspi-gpio get 27      # Check GPIO27 (RST pin) status
raspi-gpio set 27 op   # Set GPIO27 as output
cat /proc/device-tree/soc/spi@7e204000/status  # Check SPI status
```

### Network
```bash
sudo ping google.com               # Test internet
ifconfig                          # Check IP addresses
sudo systemctl restart networking  # Restart networking
```

---

## Configuration Files Reference

### Main Pwnagotchi Config
Path: `/etc/pwnagotchi/config.toml`

Key sections:
```toml
[ui.display]
enabled = true
type = "waveshare_28v2"
rotation = 0
color = "black"

[main.plugins.fancygotchi]
enabled = true
theme = ""  # Leave empty for default
rotation = 0
```

### Fancygotchi Theme Config
Path: `/opt/pwnagotchi/plugins/custom/Fancygotchi/themes/.default/`

Files:
- `config-h.toml` - Theme configuration
- `config-v.toml` - Vertical variant (if exists)

---

## Post-Setup Verification

Once setup completes, verify:

```bash
# 1. Check display loads
http://10.0.0.2:8080  # Web UI should display

# 2. Check Fancygotchi plugin
journalctl -u pwnagotchi -n 20 | grep -i fancygotchi

# 3. Verify config
grep -A 5 "fancygotchi" /etc/pwnagotchi/config.toml

# 4. Check plugin directory
ls -la /opt/pwnagotchi/plugins/custom/Fancygotchi/

# 5. Test Python imports
python3 -c "from luma.lcd.device import st7789; print('OK')"
```

---

## Notes & Tips

- **First Boot**: Pwnagotchi learns over time. Don't expect perfect results immediately.
- **Battery Life**: On RPi 4B without PiSugar, you'll need external USB power.
- **Heat**: RPi 4B can get hot. Consider a heatsink or case with airflow.
- **SD Card**: Use quality microSD cards (SanDisk, Samsung). Cheap cards cause corruption.
- **Theme Customization**: Themes can be modified in `/opt/pwnagotchi/plugins/custom/Fancygotchi/themes/`
- **Web UI Password**: Default is empty. Set one in config for security.

---

## Emergency Recovery

If something breaks:

```bash
# Restore config from backup
sudo cp /etc/pwnagotchi/config.toml.backup.XXXXX /etc/pwnagotchi/config.toml

# Remove Fancygotchi plugin (fallback to default UI)
sudo rm -rf /opt/pwnagotchi/plugins/custom/Fancygotchi

# Reinstall pwnagotchi (nuclear option)
sudo apt-get reinstall pwnagotchi

# Reflash SD card with fresh jayofelony image
# Then run setup script again
```

---

## Support & Resources

- **Pwnagotchi Docs**: https://pwnagotchi.org
- **jayofelony GitHub**: https://github.com/jayofelony/pwnagotchi
- **Fancygotchi GitHub**: https://github.com/V0r-T3x/Fancygotchi
- **Waveshare Display Docs**: https://www.waveshare.com/wiki/2.8inch_RPi_LCD_(A)
- **RPi GPIO Pinout**: https://pinout.xyz/

---

**Last Updated**: April 2026
**Created For**: B0N3S - Pwnagotchi + Fancygotchi on RPi 4B 8GB
