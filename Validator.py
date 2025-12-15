#!/usr/bin/env python3
"""
PioneerOS System Validation Suite
Tests all components before flashing to Raspberry Pi
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

class PioneerValidator:
    def __init__(self, buildroot_path="/mnt/data/buildroot"):
        self.buildroot = Path(buildroot_path)
        self.output = self.buildroot / "output"
        self.images = self.output / "images"
        self.target = self.output / "target"
        self.host = self.output / "host"
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {"passed": 0, "failed": 0, "warnings": 0}
        }
    
    def log(self, status, test_name, message, details=""):
        """Log test result"""
        symbol = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
        color = Colors.GREEN if status == "PASS" else Colors.RED if status == "FAIL" else Colors.YELLOW
        
        print(f"{color}{symbol} {test_name}{Colors.END}: {message}")
        if details:
            print(f"  {details}")
        
        self.results["tests"][test_name] = {
            "status": status,
            "message": message,
            "details": details
        }
        
        if status == "PASS":
            self.results["summary"]["passed"] += 1
        elif status == "FAIL":
            self.results["summary"]["failed"] += 1
        else:
            self.results["summary"]["warnings"] += 1
    
    def run_cmd(self, cmd, cwd=None):
        """Run shell command and return output"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, 
                text=True, cwd=cwd, timeout=10
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def test_image_exists(self):
        """Test 1: Check SD card image exists"""
        img_path = self.images / "sdcard.img"
        if img_path.exists():
            size_mb = img_path.stat().st_size / (1024**2)
            self.log("PASS", "Image File", f"Found at {img_path}", 
                    f"Size: {size_mb:.1f} MB")
        else:
            self.log("FAIL", "Image File", "sdcard.img not found", 
                    f"Expected at {img_path}")
    
    def test_kernel_exists(self):
        """Test 2: Check kernel image"""
        kernel = self.images / "Image"
        if kernel.exists():
            size_mb = kernel.stat().st_size / (1024**2)
            self.log("PASS", "Kernel Image", "Linux kernel found", 
                    f"Size: {size_mb:.1f} MB")
        else:
            self.log("FAIL", "Kernel Image", "Kernel not found")
    
    def test_dtb_exists(self):
        """Test 3: Check device tree blob"""
        dtb = self.images / "bcm2711-rpi-4-b.dtb"
        if dtb.exists():
            self.log("PASS", "Device Tree", "BCM2711 DTB found")
        else:
            self.log("FAIL", "Device Tree", "DTB for RPi4 not found")
    
    def test_rootfs_exists(self):
        """Test 4: Check root filesystem"""
        rootfs = self.images / "rootfs.ext4"
        if rootfs.exists():
            size_mb = rootfs.stat().st_size / (1024**2)
            self.log("PASS", "Root Filesystem", "ext4 rootfs found", 
                    f"Size: {size_mb:.1f} MB")
        else:
            self.log("FAIL", "Root Filesystem", "rootfs.ext4 not found")
    
    def test_boot_partition(self):
        """Test 5: Check boot partition"""
        boot_vfat = self.images / "boot.vfat"
        if boot_vfat.exists():
            self.log("PASS", "Boot Partition", "boot.vfat created")
        else:
            self.log("FAIL", "Boot Partition", "boot.vfat not found")
    
    def test_python_in_rootfs(self):
        """Test 6: Check Python3 installation"""
        python_paths = [
            self.target / "usr/bin/python3",
            self.target / "usr/lib/python3.11",
        ]
        
        found = [p for p in python_paths if p.exists()]
        if len(found) >= 1:
            self.log("PASS", "Python3", f"Found {len(found)}/2 components")
        else:
            self.log("FAIL", "Python3", "Python3 not found in rootfs")
    
    def test_opencv_libs(self):
        """Test 7: Check OpenCV libraries"""
        opencv_patterns = ["libopencv_core.so", "libopencv_imgproc.so"]
        lib_dir = self.target / "usr/lib"
        
        if lib_dir.exists():
            found = []
            for pattern in opencv_patterns:
                matches = list(lib_dir.glob(f"**/{pattern}*"))
                if matches:
                    found.append(pattern)
            
            if len(found) >= 1:
                self.log("PASS", "OpenCV4", f"Found {len(found)} core libraries")
            else:
                self.log("WARN", "OpenCV4", "OpenCV libraries not confirmed")
        else:
            self.log("WARN", "OpenCV4", "Cannot verify (lib dir not accessible)")
    
    def test_network_config(self):
        """Test 8: Check network configuration"""
        net_config = self.buildroot / "board/raspberrypi/overlay/etc/network/interfaces"
        
        if net_config.exists():
            content = net_config.read_text()
            if "192.168.1.10" in content and "eth0" in content:
                self.log("PASS", "Network Config", "Static IP configured (192.168.1.10)")
            else:
                self.log("WARN", "Network Config", "Config exists but may be incomplete")
        else:
            self.log("FAIL", "Network Config", "Network interfaces file missing")
    
    def test_ssh_server(self):
        """Test 9: Check SSH server (Dropbear)"""
        dropbear_paths = [
            self.target / "usr/sbin/dropbear",
            self.target / "etc/init.d/S50dropbear"
        ]
        
        found = [p for p in dropbear_paths if p.exists()]
        if len(found) >= 1:
            self.log("PASS", "SSH Server", f"Dropbear found ({len(found)}/2 files)")
        else:
            self.log("FAIL", "SSH Server", "Dropbear not found")
    
    def test_i2c_tools(self):
        """Test 10: Check I2C tools"""
        i2c_detect = self.target / "usr/sbin/i2cdetect"
        
        if i2c_detect.exists():
            self.log("PASS", "I2C Tools", "i2cdetect found")
        else:
            self.log("WARN", "I2C Tools", "i2c-tools not confirmed")
    
    def test_kernel_modules(self):
        """Test 11: Check kernel modules"""
        modules_dir = self.target / "lib/modules"
        
        if modules_dir.exists():
            module_dirs = list(modules_dir.iterdir())
            if module_dirs:
                self.log("PASS", "Kernel Modules", f"Found modules directory")
            else:
                self.log("WARN", "Kernel Modules", "Modules directory empty")
        else:
            self.log("WARN", "Kernel Modules", "Cannot verify modules")
    
    def test_rootfs_overlay(self):
        """Test 12: Check custom overlay applied"""
        startup_script = self.target / "etc/init.d/S99robotics"
        
        if startup_script.exists():
            self.log("PASS", "Custom Overlay", "Robotics startup script present")
        else:
            self.log("WARN", "Custom Overlay", "Startup script not found")
    
    def test_wifi_config(self):
        """Test 13: Check WiFi configuration"""
        wpa_conf = self.target / "etc/wpa_supplicant.conf"
        
        if wpa_conf.exists():
            content = wpa_conf.read_text()
            if "YOUR_SSID" in content:
                self.log("WARN", "WiFi Config", "Default credentials not changed")
            else:
                self.log("PASS", "WiFi Config", "WiFi credentials configured")
        else:
            self.log("WARN", "WiFi Config", "wpa_supplicant.conf not found")
    
    def test_utilities(self):
        """Test 14: Check system utilities"""
        utils = ["htop", "nano", "file"]
        found = []
        
        for util in utils:
            util_path = self.target / f"usr/bin/{util}"
            if util_path.exists():
                found.append(util)
        
        if len(found) >= 2:
            self.log("PASS", "System Utilities", f"Found {len(found)}/{len(utils)} tools")
        else:
            self.log("WARN", "System Utilities", f"Only {len(found)}/{len(utils)} tools found")
    
    def test_firmware_files(self):
        """Test 15: Check Raspberry Pi firmware"""
        firmware_files = ["start4.elf", "fixup4.dat"]
        rpi_fw_dir = self.images / "rpi-firmware"
        
        if rpi_fw_dir.exists():
            found = [f for f in firmware_files if (rpi_fw_dir / f).exists()]
            if len(found) == len(firmware_files):
                self.log("PASS", "RPi Firmware", "All firmware files present")
            else:
                self.log("WARN", "RPi Firmware", f"Found {len(found)}/{len(firmware_files)} files")
        else:
            self.log("FAIL", "RPi Firmware", "Firmware directory not found")
    
    def test_image_size(self):
        """Test 16: Validate image size"""
        img_path = self.images / "sdcard.img"
        
        if img_path.exists():
            size_gb = img_path.stat().st_size / (1024**3)
            if 1.5 <= size_gb <= 4:
                self.log("PASS", "Image Size", f"Size OK ({size_gb:.2f} GB)")
            elif size_gb < 1.5:
                self.log("WARN", "Image Size", f"Smaller than expected ({size_gb:.2f} GB)")
            else:
                self.log("WARN", "Image Size", f"Larger than expected ({size_gb:.2f} GB)")
    
    def test_toolchain(self):
        """Test 17: Check cross-compilation toolchain"""
        gcc = self.host / "bin/aarch64-buildroot-linux-gnu-gcc"
        
        if gcc.exists():
            self.log("PASS", "Toolchain", "Cross-compiler present")
        else:
            self.log("WARN", "Toolchain", "Cross-compiler not found")
    
    def generate_report(self):
        """Generate final validation report"""
        print("\n" + "="*70)
        print(f"{Colors.BLUE}PIONEROS VALIDATION REPORT{Colors.END}")
        print("="*70)
        
        total = self.results["summary"]["passed"] + self.results["summary"]["failed"] + self.results["summary"]["warnings"]
        passed = self.results["summary"]["passed"]
        failed = self.results["summary"]["failed"]
        warnings = self.results["summary"]["warnings"]
        
        print(f"\nTotal Tests: {total}")
        print(f"{Colors.GREEN}✓ Passed: {passed}{Colors.END}")
        print(f"{Colors.RED}✗ Failed: {failed}{Colors.END}")
        print(f"{Colors.YELLOW}⚠ Warnings: {warnings}{Colors.END}")
        
        # Readiness assessment
        print("\n" + "-"*70)
        if failed == 0 and passed >= 12:
            print(f"{Colors.GREEN}STATUS: READY FOR DEPLOYMENT ✓{Colors.END}")
            print("System passed all critical tests. Safe to flash to SD card.")
        elif failed <= 2 and warnings <= 3:
            print(f"{Colors.YELLOW}STATUS: CONDITIONAL PASS ⚠{Colors.END}")
            print("System mostly functional. Review warnings before deployment.")
        else:
            print(f"{Colors.RED}STATUS: NOT READY ✗{Colors.END}")
            print("Critical failures detected. Fix issues before flashing.")
        
        # Save JSON report
        report_path = self.buildroot / "validation_report.json"
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nDetailed report saved: {report_path}")
        print("="*70 + "\n")
    
    def run_all_tests(self):
        """Execute all validation tests"""
        print(f"\n{Colors.BLUE}Starting PioneerOS Validation...{Colors.END}\n")
        
        # Critical tests
        self.test_image_exists()
        self.test_kernel_exists()
        self.test_dtb_exists()
        self.test_rootfs_exists()
        self.test_boot_partition()
        
        # Software tests
        self.test_python_in_rootfs()
        self.test_opencv_libs()
        self.test_ssh_server()
        self.test_i2c_tools()
        
        # Configuration tests
        self.test_network_config()
        self.test_wifi_config()
        self.test_rootfs_overlay()
        
        # System tests
        self.test_kernel_modules()
        self.test_utilities()
        self.test_firmware_files()
        self.test_image_size()
        self.test_toolchain()
        
        # Generate report
        self.generate_report()

if __name__ == "__main__":
    validator = PioneerValidator()
    validator.run_all_tests()