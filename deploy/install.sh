#!/bin/bash
# Pi Zero W system optimisations for RGB display clock
# Run once after a fresh Raspbian install (as a user with sudo access).
# Safe to re-run.
#
# NOTE on systemd's hardware watchdog (RuntimeWatchdogSec in system.conf):
# deliberately NOT enabled here. A short timeout (e.g. 15s) will self-trigger
# during ordinary heavy SD card I/O (apt upgrade, rsync, rpi-update) on this
# hardware and force an unclean reboot — this bit us once already. If you add
# one, use minutes, not seconds, and never touch it while a bulk file op is
# running.

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Installing systemd services ==="

sudo cp "$SCRIPT_DIR/cpu-performance-governor.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cpu-performance-governor.service
sudo systemctl start cpu-performance-governor.service
echo "  cpu-performance-governor: $(systemctl is-active cpu-performance-governor.service)"

echo ""
echo "=== Disabling WiFi power saving ==="
if systemctl is-active --quiet NetworkManager; then
    # Bookworm+/Trixie manage WiFi via NetworkManager — the old iw-based
    # oneshot service depends on wpa_supplicant@wlan0.service, which doesn't
    # exist under NetworkManager, and needs the (uninstalled) iw package.
    sudo mkdir -p /etc/NetworkManager/conf.d
    printf '[connection]\nwifi.powersave = 2\n' | sudo tee /etc/NetworkManager/conf.d/wifi-powersave-off.conf > /dev/null
    # Deliberately NOT reloading NetworkManager here: applying a powersave
    # change can make it briefly re-associate the WiFi link, which can drop
    # the very SSH session running this script (bit us once already). The
    # reboot at the end of this script picks it up with no live disruption.
    echo "  set via NetworkManager conf.d (wifi.powersave = 2) — takes effect on next reboot"
else
    # Legacy dhcpcd/wpa_supplicant stack (Bullseye and earlier)
    sudo cp "$SCRIPT_DIR/wifi-powersave-off.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now wifi-powersave-off.service
    echo "  wifi-powersave-off.service: $(systemctl is-active wifi-powersave-off.service)"
fi

echo ""
echo "=== Fixing /var/log/rgb permissions ==="
sudo mkdir -p /var/log/rgb
# The rpi-rgb-led-matrix library drops privileges to 'daemon' after GPIO init
sudo chown daemon:daemon /var/log/rgb
echo "  /var/log/rgb owner: $(stat -c '%U:%G' /var/log/rgb)"

echo ""
echo "=== Patching config.txt ==="
# Bookworm+/Trixie moved the real file to /boot/firmware/config.txt and left a
# "DO NOT EDIT — moved to ..." stub at the old /boot/config.txt path, which
# still passes a plain -f check. Prefer the firmware path when it's present.
if [ -f /boot/firmware/config.txt ]; then
    CFG=/boot/firmware/config.txt
else
    CFG=/boot/config.txt
fi
echo "  using: $CFG"

patch_config() {
    local key="$1"
    local comment_out="$2"   # 1 = comment the line out, 0 = set key=value
    local value="$3"

    if [ "$comment_out" = "1" ]; then
        # Comment out the line if it exists and isn't already commented
        sudo sed -i "s|^${key}|# ${key}|g" "$CFG"
        echo "  commented out: $key"
    else
        # Add or replace key=value
        if grep -q "^${key}=" "$CFG" 2>/dev/null; then
            sudo sed -i "s|^${key}=.*|${key}=${value}|" "$CFG"
        else
            echo "${key}=${value}" | sudo tee -a "$CFG" > /dev/null
        fi
        echo "  set: ${key}=${value}"
    fi
}

patch_config "gpu_mem" 0 "16"
patch_config "camera_auto_detect" 1 ""
patch_config "display_auto_detect" 1 ""
patch_config "dtoverlay=vc4-kms-v3d" 1 ""
patch_config "max_framebuffers" 1 ""

echo ""
echo "=== Patching cmdline.txt (isolcpus) ==="
# Same moved-stub situation as config.txt above — prefer the firmware path.
if [ -f /boot/firmware/cmdline.txt ]; then
    CMDLINE=/boot/firmware/cmdline.txt
else
    CMDLINE=/boot/cmdline.txt
fi
if [ -f "$CMDLINE" ]; then
    NPROC=$(nproc 2>/dev/null || echo 1)
    if [ "$NPROC" -lt 4 ]; then
        echo "  skipped: only ${NPROC} core(s) detected — isolcpus=3 reserves a 4th core"
        echo "  that doesn't exist on original Pi Zero W (single-core BCM2835); it's a"
        echo "  no-op there (kernel logs 'Unknown kernel command line parameter' and"
        echo "  ignores it). Only relevant on a 4-core board (Zero 2 W, Pi 2/3/4)."
    elif grep -q "isolcpus=" "$CMDLINE"; then
        echo "  isolcpus already set: $(grep -o 'isolcpus=[0-9,]*' "$CMDLINE")"
    else
        # On a 4-core board, reserve the last core for the LED matrix's real-time
        # GPIO/DMA refresh loop so other processes can't cause visible flicker/jitter.
        sudo sed -i 's/$/ isolcpus=3/' "$CMDLINE"
        echo "  appended: isolcpus=3"
    fi
else
    echo "  WARNING: cmdline.txt not found — see matrix/README.md if on a 4-core Pi"
fi

echo ""
echo "=== Enabling NTP time sync (systemd-timesyncd) ==="
sudo timedatectl set-ntp true
echo "  NTP sync: $(timedatectl show -p NTPSynchronized --value 2>/dev/null || echo 'unknown')"

echo ""
echo "=== Disabling unnecessary services ==="
for svc in ModemManager serial-getty@ttyS0 bluetooth hciuart; do
    if systemctl is-enabled "$svc" 2>/dev/null | grep -q enabled; then
        sudo systemctl disable --now "$svc" 2>/dev/null && echo "  disabled: $svc" || echo "  skipped: $svc"
    else
        echo "  already disabled: $svc"
    fi
done

echo ""
echo "=== Installing display services ==="
# Python service (legacy — kept for reference and easy rollback)
sudo cp "$SCRIPT_DIR/rgb_display_python.service" /etc/systemd/system/
echo "  installed: rgb_display_python.service"

# C++ service (preferred — lower CPU, no flicker)
sudo cp "$SCRIPT_DIR/rgb_display.service" /etc/systemd/system/
sudo systemctl daemon-reload
echo "  installed: rgb_display.service"
echo ""
echo "  To start the C++ binary (recommended):"
echo "    sudo systemctl enable --now rgb_display.service"
echo ""
echo "  To use the Python version instead:"
echo "    sudo systemctl disable --now rgb_display.service"
echo "    sudo systemctl enable --now rgb_display_python.service"

echo ""
echo "Done. Reboot for $CFG / $CMDLINE changes to take effect."
echo "  sudo reboot"
