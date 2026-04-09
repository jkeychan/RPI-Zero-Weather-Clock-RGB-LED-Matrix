#!/bin/bash
# Pi Zero W system optimisations for RGB display clock
# Run once after a fresh Raspbian install (as a user with sudo access).
# Safe to re-run.

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Installing systemd services ==="

sudo cp "$SCRIPT_DIR/wifi-powersave-off.service" /etc/systemd/system/
sudo cp "$SCRIPT_DIR/cpu-performance-governor.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable wifi-powersave-off.service cpu-performance-governor.service
sudo systemctl start wifi-powersave-off.service cpu-performance-governor.service
echo "  wifi-powersave-off: $(systemctl is-active wifi-powersave-off.service)"
echo "  cpu-performance-governor: $(systemctl is-active cpu-performance-governor.service)"

echo ""
echo "=== Fixing /var/log/rgb permissions ==="
sudo mkdir -p /var/log/rgb
# The rpi-rgb-led-matrix library drops privileges to 'daemon' after GPIO init
sudo chown daemon:daemon /var/log/rgb
echo "  /var/log/rgb owner: $(stat -c '%U:%G' /var/log/rgb)"

echo ""
echo "=== Patching /boot/config.txt ==="
CFG=/boot/config.txt

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
echo "=== Enabling NTP time sync (systemd-timesyncd) ==="
sudo timedatectl set-ntp true
echo "  NTP sync: $(timedatectl show -p NTPSynchronized --value 2>/dev/null || echo 'unknown')"

echo ""
echo "=== Disabling unnecessary services ==="
for svc in ModemManager serial-getty@ttyS0; do
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
echo "Done. Reboot for /boot/config.txt changes to take effect."
echo "  sudo reboot"
