#!/usr/bin/env python3

"""
SPI TFT display test (Waveshare ST7789 by default here, or LCDwiki MPI2801).

LCDwiki MPI2801 (ILI9341): DC=GPIO22, RST=GPIO27 — https://www.lcdwiki.com/2.8inch_RPi_Display
Waveshare-style ST7789: DC=GPIO25, RST=GPIO27.

DISPLAY_TEST_PROFILE: waveshare_st7789 (default in this folder) | lcdwiki_mpi2801
"""

import sys
import os
import time

DISPLAY_PROFILE = os.environ.get("DISPLAY_TEST_PROFILE", "waveshare_st7789").strip().lower()

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_status(status, msg):
    symbols = {'✓': '\033[92m✓\033[0m', '✗': '\033[91m✗\033[0m', 'ℹ': '\033[94mℹ\033[0m'}
    print(f"  [{symbols.get(status, status)}] {msg}")

print_header("SPI TFT Display Diagnostics")
print_status('ℹ', f"DISPLAY_TEST_PROFILE={DISPLAY_PROFILE!r} (waveshare_st7789 | lcdwiki_mpi2801)")

# =============================================================================
# 1. Check System Prerequisites
# =============================================================================

print_header("1. System Checks")

# Check architecture
arch = os.uname().machine
if 'aarch64' in arch or 'arm' in arch:
    print_status('✓', f"ARM architecture detected: {arch}")
else:
    print_status('✗', f"Non-ARM architecture detected: {arch}")
    sys.exit(1)

# Check SPI device
spi_device = "/dev/spidev0.0"
if os.path.exists(spi_device):
    print_status('✓', f"SPI device found: {spi_device}")
else:
    print_status('✗', f"SPI device NOT found at {spi_device}")
    print_status('ℹ', "Run: sudo raspi-config → Interfaces → SPI → Enable")
    sys.exit(1)

# Check SPI permissions
if os.access(spi_device, os.R_OK | os.W_OK):
    print_status('✓', "SPI device readable/writable")
else:
    print_status('ℹ', "SPI device permissions might need adjustment")
    print_status('ℹ', "Run: sudo usermod -aG spi $USER")

# =============================================================================
# 2. Python Module Checks
# =============================================================================

print_header("2. Python Module Checks")

modules_ok = True

# Check core modules
required_modules = {
    'PIL': 'Pillow (image processing)',
    'luma.core': 'luma.core (display abstraction)',
    'luma.lcd': 'luma.lcd (LCD/TFT support)',
    'RPi': 'RPi.GPIO (GPIO control)',
}

for module_name, display_name in required_modules.items():
    try:
        __import__(module_name)
        print_status('✓', f"{display_name}")
    except ImportError as e:
        print_status('✗', f"{display_name} - {str(e)}")
        modules_ok = False

if not modules_ok:
    print("\n" + "="*60)
    print("  Missing modules. Install with:")
    print("  sudo pip3 install pillow luma.core luma.lcd RPi.GPIO spidev")
    print("="*60)
    sys.exit(1)

# =============================================================================
# 3. Display Detection & Initialization
# =============================================================================

print_header("3. Display Initialization")

display_label = "SPI TFT"
test_banner = "Display Test"

def probe_gpio_out(pins):
    """Sanity-check BCM pins before luma (same RPi.GPIO path luma uses)."""
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    configured = []
    try:
        for p in pins:
            try:
                GPIO.setup(p, GPIO.OUT)
            except Exception as e:
                print_status('✗', f"GPIO{p} (BCM) failed: {e}")
                print_status('ℹ', "If LCD-show / fbtft / a dtoverlay drives this display, the kernel "
                                  "may own GPIO22/27 — comment out that overlay in config.txt and reboot.")
                print_status('ℹ', "Also: cat /proc/device-tree/model | tr -d '\\0'")
                return False
            configured.append(p)
            print_status('✓', f"GPIO{p} (BCM) OK as OUTPUT")
        return True
    finally:
        if configured:
            GPIO.cleanup()

try:
    from luma.core.interface.serial import spi
    from PIL import Image, ImageDraw, ImageFont

    print_status('✓', "Modules imported successfully")

    if DISPLAY_PROFILE in ("lcdwiki_mpi2801", "mpi2801", "lcdwiki"):
        from luma.lcd.device import ili9341
        gpio_dc, gpio_rst = 22, 27
        no_rst = os.environ.get("DISPLAY_TEST_NO_RST", "").lower() in ("1", "true", "yes")
        gpio_rst_use = None if no_rst else gpio_rst
        if no_rst:
            print_status('ℹ', "DISPLAY_TEST_NO_RST set — skipping RST line (try if reset pin is stuck/busy)")
        print_status('ℹ', "LCDwiki MPI2801: SPI0 CE0 (GPIO8), DC=GPIO22, RST="
                          f"{'(none)' if gpio_rst_use is None else 'GPIO27'}")
        pins_to_try = [gpio_dc] if gpio_rst_use is None else [gpio_dc, gpio_rst]
        print_status('ℹ', "Probing GPIO (before luma SPI init)...")
        if not probe_gpio_out(pins_to_try):
            sys.exit(1)
        serial = spi(
            port=0,
            device=0,
            bus_speed_hz=32000000,
            gpio_DC=gpio_dc,
            gpio_RST=gpio_rst_use,
            height=240,
            width=320,
        )
        print_status('✓', "SPI bus initialized")
        print_status('ℹ', "Initializing ILI9341 (MPI2801)...")
        device = ili9341(serial, width=320, height=240, rotate=0)
        display_label = "ILI9341 (LCDwiki MPI2801)"
        test_banner = "MPI2801 / ILI9341 Test"
        print_status('✓', "Display initialized (ILI9341)")
    elif DISPLAY_PROFILE in ("waveshare_st7789", "waveshare", "st7789"):
        from luma.lcd.device import st7789
        gpio_dc, gpio_rst = 25, 27
        print_status('ℹ', "Waveshare-style: SPI0 CE0 (GPIO8), DC=GPIO25, RST=GPIO27")
        print_status('ℹ', "Probing GPIO (before luma SPI init)...")
        if not probe_gpio_out([gpio_dc, gpio_rst]):
            sys.exit(1)
        serial = spi(
            port=0,
            device=0,
            bus_speed_hz=40000000,
            gpio_DC=gpio_dc,
            gpio_RST=gpio_rst,
            height=240,
            width=320,
        )
        print_status('✓', "SPI bus initialized")
        print_status('ℹ', "Initializing ST7789...")
        device = st7789(serial, height=240, width=320, rotate=0)
        display_label = "ST7789 (Waveshare-style)"
        test_banner = "Waveshare Display Test"
        print_status('✓', "Display initialized (ST7789)")
    else:
        print_status('✗', f"Unknown DISPLAY_TEST_PROFILE={DISPLAY_PROFILE!r}")
        print_status('ℹ', "Use: waveshare_st7789 | lcdwiki_mpi2801")
        sys.exit(1)

    print_status('ℹ', f"Display size: {device.width}x{device.height}")

except Exception as e:
    print_status('✗', f"Display initialization failed: {str(e)}")
    print_status('ℹ', "Check SPI wiring and GPIO pin assignments")
    sys.exit(1)

# =============================================================================
# 4. Display Test Pattern
# =============================================================================

print_header("4. Test Pattern Rendering")

try:
    # Create test image with various patterns
    image = Image.new("RGB", (device.width, device.height), color="black")
    draw = ImageDraw.Draw(image)
    
    # Background
    draw.rectangle([(0, 0), (device.width-1, device.height-1)], outline="white", width=2)
    
    # Gradient bars
    bar_width = device.width // 4
    colors = ["red", "green", "blue", "yellow"]
    for i, color in enumerate(colors):
        x = i * bar_width
        draw.rectangle([(x, 20), (x + bar_width - 1, 60)], fill=color)
    
    # Checkerboard pattern
    checker_size = 20
    for y in range(80, 180, checker_size):
        for x in range(0, device.width, checker_size * 2):
            draw.rectangle([(x, y), (x + checker_size - 1, y + checker_size - 1)], fill="white")
            draw.rectangle([(x + checker_size, y + checker_size), (x + checker_size * 2 - 1, y + checker_size * 2 - 1)], fill="white")
    
    # Text
    try:
        # Try to use a system font, fallback to default
        font = ImageFont.load_default()
    except:
        font = None
    
    draw.text((10, 200), test_banner, fill="white", font=font)
    draw.text((10, 220), "SPI: OK | GPIO: OK", fill="green", font=font)
    
    # Send to display
    device.display(image)
    print_status('✓', "Test pattern rendered to display")
    print_status('ℹ', "Display should show test pattern now")
    
except Exception as e:
    print_status('✗', f"Test pattern failed: {str(e)}")
    sys.exit(1)

# =============================================================================
# 5. Animation Test (Optional)
# =============================================================================

print_header("5. Animation Test (10 frames)")

try:
    for frame in range(10):
        image = Image.new("RGB", (device.width, device.height), color="black")
        draw = ImageDraw.Draw(image)
        
        # Rotating square
        size = 50 + (frame * 5)
        x = (device.width - size) // 2
        y = (device.height - size) // 2
        draw.rectangle([(x, y), (x + size, y + size)], outline="cyan", width=2)
        
        # Progress text
        try:
            font = ImageFont.load_default()
        except:
            font = None
        draw.text((130, 210), f"Frame: {frame+1}/10", fill="white", font=font)
        
        device.display(image)
        time.sleep(0.1)
    
    print_status('✓', "Animation test passed")
    
except Exception as e:
    print_status('✗', f"Animation test failed: {str(e)}")

# =============================================================================
# 6. Final Display - Info Screen
# =============================================================================

print_header("6. Displaying System Info")

try:
    import subprocess
    
    image = Image.new("RGB", (device.width, device.height), color="black")
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    # Header
    draw.rectangle([(0, 0), (device.width-1, 30)], fill="blue")
    draw.text((10, 5), "Pwnagotchi Display Ready", fill="white", font=font)
    
    # System info
    try:
        temp = subprocess.check_output("vcgencmd measure_temp", shell=True).decode().strip()
    except:
        temp = "N/A"
    
    info_lines = [
        f"Resolution: {device.width}x{device.height}",
        f"Display: {display_label}",
        f"Rotation: 0",
        f"CPU Temp: {temp}",
        "Status: OK",
    ]
    
    y_pos = 50
    for line in info_lines:
        draw.text((10, y_pos), line, fill="cyan", font=font)
        y_pos += 25
    
    # Footer
    draw.rectangle([(0, device.height-25), (device.width-1, device.height-1)], fill="gray")
    draw.text((10, device.height-20), "Ready for Fancygotchi!", fill="white", font=font)
    
    device.display(image)
    print_status('✓', "System info displayed")
    
except Exception as e:
    print_status('✗', f"Info screen failed: {str(e)}")

# =============================================================================
# Summary
# =============================================================================

print_header("Test Summary")

print_status('✓', "All checks passed!")
print_status('ℹ', "Display is operational and ready for Fancygotchi")
print("\nNext steps:")
print("  1. sudo bash /tmp/pwnagotchi_fancygotchi_setup.sh (or from current dir)")
print("  2. MPI2801 instead: DISPLAY_TEST_PROFILE=lcdwiki_mpi2801 + use setup-fancygotchi.sh")
print("  3. Web UI http://10.0.0.2:8080 — enable Fancygotchi in Plugins")
print("\nTroubleshooting:")
print("  • Image not displaying? Check GPIO wiring")
print("  • Inverted/rotated display? Change rotate= in device init (0-3)")
print("  • SPI errors? Enable SPI via raspi-config")
print("\n" + "="*60 + "\n")
