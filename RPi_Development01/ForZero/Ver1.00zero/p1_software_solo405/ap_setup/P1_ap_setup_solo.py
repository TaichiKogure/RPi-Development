#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 Access Point Setup Script for Solo Version 4.0
Version: 4.0.0-solo

This script configures the Raspberry Pi 5 as a WiFi access point for P2 and P3 devices
with BME680 and MH-Z19C sensors. It handles the installation and configuration of necessary packages,
network interfaces, and services to create a standalone access point.

Features:
- Configures the built-in WiFi as an access point
- Sets up DHCP server for IP address assignment
- Configures network address translation (NAT) for internet sharing
- Provides options for dual WiFi setup with USB dongle
- Includes functions to switch between AP mode and client mode

Requirements:
- Raspberry Pi 5 with Raspberry Pi OS (Bullseye or newer)
- Root privileges (run with sudo)
- Internet connection for initial package installation

Usage:
    sudo python3 P1_ap_setup_solo.py [--configure | --enable | --disable | --status]
"""

import os
import sys
import subprocess
import argparse
import shutil
import time
import re
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/ap_setup_solo.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "ap_interface": "wlan0",
    "ap_ssid": "RaspberryPi5_AP_Solo2",
    "ap_password": "raspberry",
    "ap_country": "JP",
    "ap_channel": "6",
    "ap_ip": "192.168.0.2",
    "ap_netmask": "255.255.255.0",
    "ap_dhcp_range_start": "192.168.0.50",
    "ap_dhcp_range_end": "192.168.0.150",
    "ap_dhcp_lease_time": "24h",
    "client_interface": "wlan1",
    "priority_mode": "ap"  # 'ap' or 'client'
}

# Paths to configuration files
CONFIG_PATH = Path("/etc/raspap_solo")
HOSTAPD_CONF = "/etc/hostapd/hostapd.conf"
DNSMASQ_CONF = "/etc/dnsmasq.conf"
DHCPCD_CONF = "/etc/dhcpcd.conf"
SYSCTL_CONF = "/etc/sysctl.conf"
INTERFACES_CONF = "/etc/network/interfaces"
RASPAP_CONFIG = str(CONFIG_PATH / "raspap_solo.conf")

def check_root():
    """Check if the script is run with root privileges."""
    if os.geteuid() != 0:
        logger.error("This script must be run as root (sudo)")
        sys.exit(1)

def install_dependencies():
    """Install required packages for access point functionality."""
    logger.info("Installing required packages...")

    try:
        # Update package lists
        subprocess.run(["apt-get", "update"], check=True)

        # Install required packages
        packages = [
            "hostapd", "dnsmasq", "iptables", "iptables-persistent", 
            "bridge-utils", "iw", "rfkill", "wireless-tools"
        ]

        subprocess.run(["apt-get", "install", "-y"] + packages, check=True)

        # Stop services initially to configure them
        subprocess.run(["systemctl", "stop", "hostapd"], check=False)
        subprocess.run(["systemctl", "stop", "dnsmasq"], check=False)

        logger.info("Required packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

def configure_hostapd(config):
    """Configure hostapd for the access point."""
    logger.info("Configuring hostapd...")

    hostapd_config = f"""# hostapd configuration file
interface={config['ap_interface']}
driver=nl80211
ssid={config['ap_ssid']}
hw_mode=g
channel={config['ap_channel']}
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={config['ap_password']}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
country_code={config['ap_country']}
ieee80211n=1
ieee80211d=1
"""

    try:
        with open(HOSTAPD_CONF, 'w') as f:
            f.write(hostapd_config)

        # Update hostapd default configuration
        with open("/etc/default/hostapd", 'w') as f:
            f.write('DAEMON_CONF="/etc/hostapd/hostapd.conf"\n')

        logger.info("hostapd configured successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to configure hostapd: {e}")
        return False

def configure_dnsmasq(config):
    """Configure dnsmasq for DHCP server."""
    logger.info("Configuring dnsmasq...")

    # Backup original configuration if it exists
    if os.path.exists(DNSMASQ_CONF) and not os.path.exists(f"{DNSMASQ_CONF}.orig"):
        shutil.copy2(DNSMASQ_CONF, f"{DNSMASQ_CONF}.orig")

    dnsmasq_config = f"""# dnsmasq configuration for Raspberry Pi 5 AP Solo Ver4.0
interface={config['ap_interface']}
dhcp-range={config['ap_dhcp_range_start']},{config['ap_dhcp_range_end']},{config['ap_netmask']},{config['ap_dhcp_lease_time']}
domain=wlan
address=/gw.wlan/{config['ap_ip']}
bogus-priv
server=8.8.8.8
server=8.8.4.4
"""

    try:
        with open(DNSMASQ_CONF, 'w') as f:
            f.write(dnsmasq_config)

        logger.info("dnsmasq configured successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to configure dnsmasq: {e}")
        return False

def configure_dhcpcd(config):
    """Configure dhcpcd for static IP assignment."""
    logger.info("Configuring dhcpcd...")

    # Backup original configuration if it exists
    if os.path.exists(DHCPCD_CONF) and not os.path.exists(f"{DHCPCD_CONF}.orig"):
        shutil.copy2(DHCPCD_CONF, f"{DHCPCD_CONF}.orig")

    # Read existing configuration
    with open(DHCPCD_CONF, 'r') as f:
        dhcpcd_content = f.read()

    # Check if configuration for ap_interface already exists
    interface_pattern = re.compile(f"interface {config['ap_interface']}.*?(?=interface|$)", re.DOTALL)
    interface_config = interface_pattern.search(dhcpcd_content)

    if interface_config:
        # Replace existing configuration
        new_config = f"interface {config['ap_interface']}\n    static ip_address={config['ap_ip']}/24\n    nohook wpa_supplicant\n\n"
        dhcpcd_content = interface_pattern.sub(new_config, dhcpcd_content)
    else:
        # Add new configuration
        dhcpcd_content += f"\ninterface {config['ap_interface']}\n    static ip_address={config['ap_ip']}/24\n    nohook wpa_supplicant\n"

    try:
        with open(DHCPCD_CONF, 'w') as f:
            f.write(dhcpcd_content)

        logger.info("dhcpcd configured successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to configure dhcpcd: {e}")
        return False

def configure_ip_forwarding():
    """Enable IP forwarding for internet sharing."""
    logger.info("Configuring IP forwarding...")

    try:
        # Enable IP forwarding immediately
        subprocess.run(["sh", "-c", "echo 1 > /proc/sys/net/ipv4/ip_forward"], check=True)

        # Enable IP forwarding permanently
        with open(SYSCTL_CONF, 'r') as f:
            sysctl_content = f.read()

        if "net.ipv4.ip_forward=1" not in sysctl_content:
            with open(SYSCTL_CONF, 'a') as f:
                f.write("\n# Enable IP forwarding for AP\nnet.ipv4.ip_forward=1\n")

        # Configure iptables for NAT
        subprocess.run([
            "iptables", "-t", "nat", "-A", "POSTROUTING", "-o", "eth0", "-j", "MASQUERADE"
        ], check=True)

        # Save iptables rules
        subprocess.run(["sh", "-c", "iptables-save > /etc/iptables/rules.v4"], check=True)

        logger.info("IP forwarding configured successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to configure IP forwarding: {e}")
        return False

def save_config(config):
    """Save the configuration to a file."""
    logger.info("Saving configuration...")

    try:
        # Create config directory if it doesn't exist
        os.makedirs(CONFIG_PATH, exist_ok=True)

        with open(RASPAP_CONFIG, 'w') as f:
            for key, value in config.items():
                f.write(f"{key}={value}\n")

        logger.info(f"Configuration saved to {RASPAP_CONFIG}")
        return True
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        return False

def load_config():
    """Load configuration from file or use defaults."""
    if os.path.exists(RASPAP_CONFIG):
        logger.info(f"Loading configuration from {RASPAP_CONFIG}")
        config = DEFAULT_CONFIG.copy()

        try:
            with open(RASPAP_CONFIG, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        if key in config:
                            config[key] = value

            logger.info("Configuration loaded successfully")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return DEFAULT_CONFIG
    else:
        logger.info("Using default configuration")
        return DEFAULT_CONFIG.copy()

def enable_services():
    """Enable and start the required services."""
    logger.info("Enabling and starting services...")

    try:
        # Enable services to start on boot
        subprocess.run(["systemctl", "unmask", "hostapd"], check=True)
        subprocess.run(["systemctl", "enable", "hostapd"], check=True)
        subprocess.run(["systemctl", "enable", "dnsmasq"], check=True)

        # Start services
        subprocess.run(["systemctl", "start", "hostapd"], check=True)
        subprocess.run(["systemctl", "start", "dnsmasq"], check=True)

        logger.info("Services enabled and started successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to enable services: {e}")
        return False

def disable_services():
    """Disable and stop the access point services."""
    logger.info("Disabling and stopping services...")

    try:
        # Stop services
        subprocess.run(["systemctl", "stop", "hostapd"], check=True)
        subprocess.run(["systemctl", "stop", "dnsmasq"], check=True)

        # Disable services
        subprocess.run(["systemctl", "disable", "hostapd"], check=True)
        subprocess.run(["systemctl", "disable", "dnsmasq"], check=True)

        # Restore original configurations if they exist
        for conf_file in [DHCPCD_CONF, DNSMASQ_CONF]:
            if os.path.exists(f"{conf_file}.orig"):
                shutil.copy2(f"{conf_file}.orig", conf_file)

        logger.info("Services disabled and stopped successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to disable services: {e}")
        return False

def check_status():
    """Check the status of the access point services."""
    logger.info("Checking access point status...")

    services = ["hostapd", "dnsmasq"]
    status = {}

    for service in services:
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service],
                capture_output=True,
                text=True,
                check=False
            )
            status[service] = result.stdout.strip()
        except Exception as e:
            status[service] = f"Error: {e}"

    # Check if wlan0 has the configured IP
    try:
        result = subprocess.run(
            ["ip", "addr", "show", "wlan0"],
            capture_output=True,
            text=True,
            check=False
        )
        ip_output = result.stdout
        config = load_config()
        if config["ap_ip"] in ip_output:
            status["ip_configured"] = "Yes"
        else:
            status["ip_configured"] = "No"
    except Exception as e:
        status["ip_configured"] = f"Error: {e}"

    # Print status
    print("\nAccess Point Status:")
    print(f"hostapd service: {status['hostapd']}")
    print(f"dnsmasq service: {status['dnsmasq']}")
    print(f"IP configured: {status['ip_configured']}")

    if status["hostapd"] == "active" and status["dnsmasq"] == "active" and status["ip_configured"] == "Yes":
        print("\nAccess point is running correctly.")

        # Show SSID and password
        config = load_config()
        print(f"\nSSID: {config['ap_ssid']}")
        print(f"Password: {config['ap_password']}")
        print(f"IP Address: {config['ap_ip']}")
    else:
        print("\nAccess point is not running correctly.")

    return status

def configure_ap():
    """Configure the Raspberry Pi as an access point."""
    logger.info("Starting access point configuration...")

    # Check if running as root
    check_root()

    # Load or use default configuration
    config = load_config()

    # Install required packages
    if not install_dependencies():
        logger.error("Failed to install dependencies. Exiting.")
        return False

    # Configure components
    if not configure_hostapd(config):
        logger.error("Failed to configure hostapd. Exiting.")
        return False

    if not configure_dnsmasq(config):
        logger.error("Failed to configure dnsmasq. Exiting.")
        return False

    if not configure_dhcpcd(config):
        logger.error("Failed to configure dhcpcd. Exiting.")
        return False

    if not configure_ip_forwarding():
        logger.error("Failed to configure IP forwarding. Exiting.")
        return False

    # Save configuration
    if not save_config(config):
        logger.error("Failed to save configuration. Exiting.")
        return False

    # Enable and start services
    if not enable_services():
        logger.error("Failed to enable services. Exiting.")
        return False

    logger.info("Access point configuration completed successfully")
    print("\nAccess point configuration completed successfully!")
    print(f"SSID: {config['ap_ssid']}")
    print(f"Password: {config['ap_password']}")
    print(f"IP Address: {config['ap_ip']}")
    print("\nReboot your Raspberry Pi for changes to take effect.")

    return True

def main():
    """Main function to parse arguments and execute commands."""
    parser = argparse.ArgumentParser(description="Raspberry Pi 5 Access Point Setup for Solo Version 4.0")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--configure", action="store_true", help="Configure the access point")
    group.add_argument("--enable", action="store_true", help="Enable the access point")
    group.add_argument("--disable", action="store_true", help="Disable the access point")
    group.add_argument("--status", action="store_true", help="Check the status of the access point")

    args = parser.parse_args()

    if args.configure:
        configure_ap()
    elif args.enable:
        enable_services()
    elif args.disable:
        disable_services()
    elif args.status:
        check_status()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()