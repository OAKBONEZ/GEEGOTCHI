# 🎮 Fancygotchi Quick Setup Guide

## Files Ready on Your Computer

✅ **All setup files verified and ready:**
- `RPI4BFANCY/pwnagotchi_fancygotchi_setup.sh` - Main installer
- `RPI4BFANCY/waveshare_display_test.py` - Display test utility
- `RPI4BFANCY/SETUP_CHECKLIST.md` - Reference guide

---

## 🚀 Step 1: Transfer Files to RPi (Run on Your Computer)

Open **Command Prompt** or **PowerShell** and run:

```powershell
scp "C:\Users\gee\Documents\CLAUDE STORAGE\fancygotchi geegotchi\RPI4BFANCY\pwnagotchi_fancygotchi_setup.sh" pi@10.0.0.2:/tmp/

scp "C:\Users\gee\Documents\CLAUDE STORAGE\fancygotchi geegotchi\RPI4BFANCY\waveshare_display_test.py" pi@10.0.0.2:/tmp/
```

**Expected:** Files transfer without errors (may ask for password: `raspberry` or `pwnagotchi`)

---

## 🔌 Step 2: Test Display (Run on RPi via SSH)

Connect to your RPi:

```bash
ssh pi@10.0.0.2
```

Then run the display test:

```bash
sudo python3 /tmp/waveshare_display_test.py
```

**Expected Output:**
- ✓ ARM architecture detected
- ✓ SPI device found
- ✓ Modules imported successfully
- ✓ Display initialized (ST7789 detected)
- ✓ Test pattern rendered to display
- ✓ Animation test passed
- ✓ All checks passed!

**On your display:** You should see color bars, checkerboard pattern, and test text.

### If Test Fails:
- **No SPI device:** Enable SPI: `sudo raspi-config nonint do_spi 0` then `sudo reboot`
- **Missing modules:** Display test will tell you which ones - you'll install them in Step 3
- **Display black:** Check GPIO wiring again (3.3V VCC, all GNDs connected)

---

## ⚙️ Step 3: Run Full Setup (On RPi)

Make the setup script executable and run it:

```bash
chmod +x /tmp/pwnagotchi_fancygotchi_setup.sh

sudo /tmp/pwnagotchi_fancygotchi_setup.sh
```

**This will automatically:**
- ✓ Enable SPI interface
- ✓ Install system dependencies
- ✓ Install Python packages (pillow, luma.core, luma.lcd)
- ✓ Clone Fancygotchi plugin from GitHub
- ✓ Update Pwnagotchi config
- ✓ Enable Fancygotchi plugin
- ✓ Restart pwnagotchi service

**Watch the output for green checkmarks (✓)** - means it worked!

**Expected time:** 5-10 minutes depending on internet speed

---

## 🌐 Step 4: Enable in Web UI

1. Open your browser and go to: `http://10.0.0.2:8080`

2. Navigate to: **Settings** → **Plugins**

3. Find **"fancygotchi"** in the list

4. Toggle it **ON** (if not already enabled)

5. Click **"Refresh"** button

6. Go back to main page - **Fancygotchi should now appear on the display!**

---

## ✅ Verification Checklist

On the RPi, verify everything worked:

```bash
# Check plugin installed
ls -la /opt/pwnagotchi/plugins/custom/Fancygotchi/

# Check config was updated
grep -A 5 "fancygotchi" /etc/pwnagotchi/config.toml

# Check service logs (should see Fancygotchi loaded)
journalctl -u pwnagotchi -n 20

# Test Python imports
python3 -c "from luma.lcd.device import st7789; print('Display module OK')"
```

**All should show successful results (no errors).**

---

## 🎨 Display Rotation (If Needed)

If your display appears upside-down or rotated:

1. SSH to RPi
2. Edit config: `sudo nano /etc/pwnagotchi/config.toml`
3. Find `ui.display.rotation`
4. Change value: `0` (normal), `1` (90°), `2` (180°), `3` (270°)
5. Save (Ctrl+O, Enter, Ctrl+X)
6. Restart: `sudo systemctl restart pwnagotchi`

---

## 🆘 Troubleshooting Commands

```bash
# View detailed logs
journalctl -u pwnagotchi -n 50

# Restart pwnagotchi service
sudo systemctl restart pwnagotchi

# Check SPI is enabled
raspi-gpio get 11

# Check DC pin (GPIO25)
raspi-gpio get 25

# Check RST pin (GPIO27)
raspi-gpio get 27

# Test display again
sudo python3 /tmp/waveshare_display_test.py
```

---

## 📋 Summary

| Step | Command | On | Time |
|------|---------|----|----|
| 1 | SCP files | Your Computer | <1 min |
| 2 | Test display | RPi SSH | 2-3 min |
| 3 | Run setup script | RPi SSH | 5-10 min |
| 4 | Enable in Web UI | Browser | 1 min |
| 5 | Verify | RPi SSH | 2 min |

**Total time: ~15-20 minutes**

---

**Good luck! 🚀 Your Fancygotchi should be running soon!**
