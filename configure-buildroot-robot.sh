#!/bin/bash
# Automated Buildroot configuration for Raspberry Pi 4B robotics system
# Usage: ./configure-buildroot-robot.sh

set -e

BUILDROOT_DIR="${HOME}/buildroot"
BOARD_DIR="board/raspberrypi"
OVERLAY_DIR="${BOARD_DIR}/overlay"

cd "${BUILDROOT_DIR}"

echo "==> Creating board directory structure..."
mkdir -p "${BOARD_DIR}/fragments"
mkdir -p "${OVERLAY_DIR}/etc/network"
mkdir -p "${OVERLAY_DIR}/etc/init.d"

echo "==> Creating kernel configuration fragment..."
cat > "${BOARD_DIR}/linux-fragments.config" << 'EOF'
# PWM for motor control
CONFIG_PWM=y
CONFIG_PWM_SYSFS=y
CONFIG_PWM_BCM2835=y

# I2C for sensors
CONFIG_I2C=y
CONFIG_I2C_CHARDEV=y
CONFIG_I2C_BCM2835=y

# V4L2 for camera
CONFIG_MEDIA_SUPPORT=y
CONFIG_VIDEO_DEV=y
CONFIG_VIDEO_V4L2=y
CONFIG_VIDEO_BCM2835=m
CONFIG_USB_VIDEO_CLASS=m

# GPIO access
CONFIG_GPIO_SYSFS=y
CONFIG_GPIOLIB=y
EOF

echo "==> Creating network configuration overlay..."
cat > "${OVERLAY_DIR}/etc/network/interfaces" << 'EOF'
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet static
    address 192.168.1.10
    netmask 255.255.255.0
    gateway 192.168.1.1

auto wlan0
iface wlan0 inet dhcp
    wpa-conf /etc/wpa_supplicant.conf
EOF

cat > "${OVERLAY_DIR}/etc/wpa_supplicant.conf" << 'EOF'
ctrl_interface=/var/run/wpa_supplicant
update_config=1

network={
    ssid="YOUR_SSID"
    psk="YOUR_PASSWORD"
}
EOF

echo "==> Creating robot startup script..."
cat > "${OVERLAY_DIR}/etc/init.d/S99robotics" << 'EOF'
#!/bin/sh
#
# Start robotics system
#

case "$1" in
  start)
    echo "Starting robotics system..."
    
    # Export GPIO pins if needed
    # echo 18 > /sys/class/gpio/export 2>/dev/null || true
    
    # Enable PWM
    if [ -d /sys/class/pwm/pwmchip0 ]; then
        echo 0 > /sys/class/pwm/pwmchip0/export 2>/dev/null || true
        echo 1 > /sys/class/pwm/pwmchip0/export 2>/dev/null || true
    fi
    
    # Mount tmpfs for logs
    mount -t tmpfs -o size=64m tmpfs /var/log
    
    echo "Robotics system ready"
    ;;
  stop)
    echo "Stopping robotics system..."
    ;;
  restart|reload)
    "$0" stop
    "$0" start
    ;;
  *)
    echo "Usage: $0 {start|stop|restart}"
    exit 1
esac

exit $?
EOF
chmod +x "${OVERLAY_DIR}/etc/init.d/S99robotics"

echo "==> Creating sysctl tuning..."
cat > "${OVERLAY_DIR}/etc/sysctl.conf" << 'EOF'
# Memory management for low-RAM robotics
vm.swappiness=10
vm.vfs_cache_pressure=50
vm.dirty_ratio=10
vm.dirty_background_ratio=5
EOF

echo "==> Starting with base RPi4 64-bit configuration..."
make raspberrypi4_64_defconfig

echo "==> Applying custom configuration..."
cat >> .config << 'EOF'
# ========================================
# Toolchain Configuration
# ========================================
BR2_TOOLCHAIN_BUILDROOT_CXX=y
BR2_TOOLCHAIN_BUILDROOT_WCHAR=y
BR2_TOOLCHAIN_BUILDROOT_LOCALE=y

# ========================================
# System Configuration
# ========================================
BR2_TARGET_GENERIC_HOSTNAME="robotpi"
BR2_TARGET_GENERIC_ISSUE="Robotics System"
BR2_TARGET_GENERIC_ROOT_PASSWD="robotics"
BR2_SYSTEM_DHCP="eth0"
BR2_TARGET_GENERIC_GETTY_PORT="ttyS0"
BR2_TARGET_GENERIC_GETTY_BAUDRATE_115200=y
BR2_ROOTFS_OVERLAY="board/raspberrypi/overlay"

# ========================================
# Kernel Configuration
# ========================================
BR2_LINUX_KERNEL_CONFIG_FRAGMENT_FILES="board/raspberrypi/linux-fragments.config"

# ========================================
# Networking Packages
# ========================================
BR2_PACKAGE_DROPBEAR=y
BR2_PACKAGE_DROPBEAR_DISABLE_REVERSEDNS=y
BR2_PACKAGE_WPA_SUPPLICANT=y
BR2_PACKAGE_WPA_SUPPLICANT_CLI=y
BR2_PACKAGE_WPA_SUPPLICANT_PASSPHRASE=y
BR2_PACKAGE_DHCPCD=y

# ========================================
# Hardware Support
# ========================================
BR2_PACKAGE_I2C_TOOLS=y
BR2_PACKAGE_RPI_FIRMWARE=y
BR2_PACKAGE_RPI_USERLAND=y

# ========================================
# Python & Libraries
# ========================================
BR2_PACKAGE_PYTHON3=y
BR2_PACKAGE_PYTHON3_PY_PYC=y
BR2_PACKAGE_PYTHON_NUMPY=y
BR2_PACKAGE_PYTHON_PIP=y

# ========================================
# OpenCV for Vision
# ========================================
BR2_PACKAGE_OPENCV4=y
BR2_PACKAGE_OPENCV4_LIB_PYTHON=y
BR2_PACKAGE_OPENCV4_WITH_JPEG=y
BR2_PACKAGE_OPENCV4_WITH_PNG=y
BR2_PACKAGE_OPENCV4_WITH_V4L=y
BR2_PACKAGE_OPENCV4_CONTRIB=y

# Image format support
BR2_PACKAGE_JPEG=y
BR2_PACKAGE_LIBPNG=y

# ========================================
# Utilities
# ========================================
BR2_PACKAGE_HTOP=y
BR2_PACKAGE_NANO=y
BR2_PACKAGE_V4L_UTILS=y
BR2_PACKAGE_FILE=y

# ========================================
# Filesystem
# ========================================
BR2_TARGET_ROOTFS_EXT2=y
BR2_TARGET_ROOTFS_EXT2_4=y
BR2_TARGET_ROOTFS_EXT2_SIZE="2G"

# Disable unneeded stuff
BR2_TARGET_ROOTFS_TAR=n
EOF

echo "==> Resolving dependencies..."
make olddefconfig

echo "==> Configuration complete!"
echo ""
echo "Configuration summary:"
echo "  - Base: Raspberry Pi 4 64-bit"
echo "  - Kernel: PWM, I2C, V4L2 enabled"
echo "  - Network: Static IP 192.168.1.10 on eth0"
echo "  - SSH: Dropbear on port 22"
echo "  - Serial: ttyS0 at 115200 baud"
echo "  - Vision: OpenCV4 + Python3 + NumPy"
echo "  - Root password: 'robotics'"
echo ""
echo "Next steps:"
echo "  1. Edit ${OVERLAY_DIR}/etc/wpa_supplicant.conf for WiFi"
echo "  2. Run: make -j\$(nproc)"
echo "  3. Flash: sudo dd if=output/images/sdcard.img of=/dev/sdX bs=4M status=progress"
echo ""
echo "To verify config: make menuconfig"