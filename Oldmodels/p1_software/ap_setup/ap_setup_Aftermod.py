#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 Access Point Setup Script
Version: 3.0.0

このスクリプトは、Raspberry Pi 5をP2およびP3デバイス用のWiFiアクセスポイントとして設定します。
必要なパッケージ、ネットワークインターフェース、およびサービスのインストールと設定を行い、
スタンドアロンのアクセスポイントを作成します。

機能:
- 内蔵WiFiをアクセスポイントとして設定
- IPアドレス割り当て用のDHCPサーバーを設定
- インターネット共有のためのネットワークアドレス変換(NAT)を設定
- USBドングルを使用したデュアルWiFiセットアップのオプションを提供
- APモードとクライアントモードを切り替える機能
- USBドングルの有無を自動検出し、適切なモードを設定

要件:
- Raspberry Pi 5（Raspberry Pi OS Bullseye以降）
- root権限（sudoで実行）
- 初期パッケージインストール用のインターネット接続

使用方法:
    sudo python3 ap_setup.py [--configure | --enable | --disable | --status | --switch-mode | --auto-config]

This script configures the Raspberry Pi 5 as a WiFi access point for P2 and P3 devices.
It handles the installation and configuration of necessary packages, network interfaces,
and services to create a standalone access point.

Features:
- Configures the built-in WiFi as an access point
- Sets up DHCP server for IP address assignment
- Configures network address translation (NAT) for internet sharing
- Provides options for dual WiFi setup with USB dongle
- Includes functions to switch between AP mode and client mode
- Auto-detects USB WiFi dongle and configures appropriate mode

Requirements:
- Raspberry Pi 5 with Raspberry Pi OS (Bullseye or newer)
- Root privileges (run with sudo)
- Internet connection for initial package installation

Usage:
    sudo python3 ap_setup.py [--configure | --enable | --disable | --status | --switch-mode | --auto-config]
"""

import os
import sys
import subprocess
import argparse
import shutil
import time
import re
import logging
import locale
from pathlib import Path
import ipaddress

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/ap_setup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure locale for language support
try:
    locale.setlocale(locale.LC_ALL, 'ja_JP.UTF-8')
    LANG = 'ja'
except locale.Error:
    LANG = 'en'
    logger.warning("Japanese locale not available, using English")

# Bilingual messages
MESSAGES = {
    'ap_mode_enabled': {
        'en': "Access Point mode enabled successfully",
        'ja': "アクセスポイントモードが正常に有効化されました"
    },
    'client_mode_enabled': {
        'en': "Client mode enabled successfully",
        'ja': "クライアントモードが正常に有効化されました"
    },
    'dongle_detected': {
        'en': "USB WiFi dongle detected",
        'ja': "USB WiFiドングルが検出されました"
    },
    'no_dongle_detected': {
        'en': "No USB WiFi dongle detected, using built-in WiFi for AP mode",
        'ja': "USB WiFiドングルが検出されませんでした。内蔵WiFiをAPモードに使用します"
    },
    'switching_to_ap': {
        'en': "Switching to Access Point mode",
        'ja': "アクセスポイントモードに切り替えています"
    },
    'switching_to_client': {
        'en': "Switching to Client mode",
        'ja': "クライアントモードに切り替えています"
    },
    'mode_switch_error': {
        'en': "Error switching mode",
        'ja': "モード切替エラー"
    },
    'current_mode': {
        'en': "Current mode: {}",
        'ja': "現在のモード: {}"
    },
    'ap_mode': {
        'en': "Access Point",
        'ja': "アクセスポイント"
    },
    'client_mode': {
        'en': "Client",
        'ja': "クライアント"
    },
    'auto_config_success': {
        'en': "Automatic configuration completed successfully",
        'ja': "自動設定が正常に完了しました"
    },
    'auto_config_error': {
        'en': "Error during automatic configuration",
        'ja': "自動設定中にエラーが発生しました"
    }
}

def get_message(key, lang=LANG):
    """Get message in the specified language."""
    if key in MESSAGES:
        return MESSAGES[key].get(lang, MESSAGES[key]['en'])
    return key

# Default configuration
DEFAULT_CONFIG = {
    "ap_interface": "wlan0",
    "ap_ssid": "RaspberryPi5_AP",
    "ap_password": "raspberry",
    "ap_country": "JP",
    "ap_channel": "6",
    "ap_ip": "192.168.0.1",
    "ap_netmask": "255.255.255.0",
    "ap_dhcp_range_start": "192.168.0.50",
    "ap_dhcp_range_end": "192.168.0.150",
    "ap_dhcp_lease_time": "24h",
    "client_interface": "wlan1",
    "priority_mode": "ap"  # 'ap' or 'client'
}

# Paths to configuration files
CONFIG_PATH = Path("/etc/raspap")
HOSTAPD_CONF = "/etc/hostapd/hostapd.conf"
DNSMASQ_CONF = "/etc/dnsmasq.conf"
DHCPCD_CONF = "/etc/dhcpcd.conf"
SYSCTL_CONF = "/etc/sysctl.conf"
INTERFACES_CONF = "/etc/network/interfaces"
RASPAP_CONFIG = str(CONFIG_PATH / "raspap.conf")

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
    """Configure dnsmasq for DHCP server with valid IP addresses."""
    logger.info("Configuring dnsmasq...")

    # Validate IP addresses in the configuration
    try:
        ip_start = ipaddress.IPv4Address(config['ap_dhcp_range_start'])
        ip_end = ipaddress.IPv4Address(config['ap_dhcp_range_end'])
        ap_ip = ipaddress.IPv4Address(config['ap_ip'])
    except ipaddress.AddressValueError as e:
        logger.error(f"Invalid IP address in config: {e}")
        return False

    # Ensure IP range is valid
    if not (ip_start < ip_end):
        logger.error("Invalid DHCP range: Start IP must be less than End IP")
        return False

    # Check if the ap_ip falls within the same subnet as the DHCP range
    network = ipaddress.IPv4Network(f"{ap_ip}/{config['ap_netmask']}", strict=False)
    if not (ap_ip in network and ip_start in network and ip_end in network):
        logger.error("IP addresses must be within the same subnet")
        return False

    # Backup original configuration if it exists
    if os.path.exists(DNSMASQ_CONF) and not os.path.exists(f"{DNSMASQ_CONF}.orig"):
        shutil.copy2(DNSMASQ_CONF, f"{DNSMASQ_CONF}.orig")

    dnsmasq_config = f"""# dnsmasq configuration for Raspberry Pi 5 AP
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

def detect_usb_wifi_dongle():
    """Detect if a USB WiFi dongle is connected to the system."""
    logger.info("Detecting USB WiFi dongle...")

    try:
        # Get list of all network interfaces
        result = subprocess.run(
            ["ip", "link", "show"],
            capture_output=True,
            text=True,
            check=True
        )

        # Look for wlan interfaces other than wlan0 (which is typically the built-in WiFi)
        interfaces = result.stdout
        wifi_interfaces = re.findall(r'\d+: (wlan\d+):', interfaces)

        # Filter out wlan0 (built-in WiFi)
        usb_wifi_interfaces = [iface for iface in wifi_interfaces if iface != 'wlan0']

        if usb_wifi_interfaces:
            logger.info(f"USB WiFi dongle detected: {usb_wifi_interfaces[0]}")
            print(get_message('dongle_detected'))
            return usb_wifi_interfaces[0]
        else:
            logger.info("No USB WiFi dongle detected")
            print(get_message('no_dongle_detected'))
            return None

    except Exception as e:
        logger.error(f"Error detecting USB WiFi dongle: {e}")
        return None

def get_current_mode():
    """Determine the current mode (AP or client) based on active services."""
    try:
        hostapd_active = subprocess.run(
            ["systemctl", "is-active", "hostapd"],
            capture_output=True,
            text=True,
            check=False
        ).stdout.strip() == "active"

        if hostapd_active:
            return "ap"
        else:
            return "client"
    except Exception as e:
        logger.error(f"Error determining current mode: {e}")
        return None

def switch_mode(target_mode):
    """Switch between AP mode and client mode."""
    current_mode = get_current_mode()
    config = load_config()

    if current_mode == target_mode:
        logger.info(f"Already in {target_mode} mode")
        print(get_message('current_mode').format(
            get_message('ap_mode' if target_mode == 'ap' else 'client_mode')
        ))
        return True

    try:
        if target_mode == "ap":
            logger.info("Switching to AP mode")
            print(get_message('switching_to_ap'))

            # Disable client mode if active
            if current_mode == "client":
                # Restore wpa_supplicant configuration for wlan0
                subprocess.run(["systemctl", "stop", "wpa_supplicant"], check=False)

                # Configure dhcpcd for static IP
                configure_dhcpcd(config)

                # Enable and start AP services
                enable_services()
            else:
                # First-time AP setup
                configure_ap()

            # Update config to prioritize AP mode
            config["priority_mode"] = "ap"
            save_config(config)

            print(get_message('ap_mode_enabled'))
            return True

        elif target_mode == "client":
            logger.info("Switching to client mode")
            print(get_message('switching_to_client'))

            # Disable AP services
            disable_services()

            # Remove static IP configuration for wlan0
            with open(DHCPCD_CONF, 'r') as f:
                dhcpcd_content = f.read()

            # Remove wlan0 static configuration
            dhcpcd_content = re.sub(
                r'interface wlan0\s+static ip_address=.*?\s+nohook wpa_supplicant\s*\n',
                '',
                dhcpcd_content
            )

            with open(DHCPCD_CONF, 'w') as f:
                f.write(dhcpcd_content)

            # Restart dhcpcd to apply changes
            subprocess.run(["systemctl", "restart", "dhcpcd"], check=True)

            # Enable wpa_supplicant for client mode
            subprocess.run(["systemctl", "enable", "wpa_supplicant"], check=True)
            subprocess.run(["systemctl", "start", "wpa_supplicant"], check=True)

            # Update config to prioritize client mode
            config["priority_mode"] = "client"
            save_config(config)

            print(get_message('client_mode_enabled'))
            return True

        else:
            logger.error(f"Invalid mode: {target_mode}")
            return False

    except Exception as e:
        logger.error(f"Error switching mode: {e}")
        print(get_message('mode_switch_error'))
        return False

def auto_configure():
    """Automatically configure the system based on USB WiFi dongle presence."""
    logger.info("Starting automatic configuration...")

    try:
        # Detect USB WiFi dongle
        usb_wifi_interface = detect_usb_wifi_dongle()
        config = load_config()

        if usb_wifi_interface:
            # USB WiFi dongle detected
            # Set client_interface to the detected USB WiFi interface
            config["client_interface"] = usb_wifi_interface
            save_config(config)

            # If priority mode is AP, configure AP mode on built-in WiFi
            if config["priority_mode"] == "ap":
                switch_mode("ap")
            else:
                # Otherwise, configure client mode on built-in WiFi
                switch_mode("client")
        else:
            # No USB WiFi dongle detected, prioritize AP mode
            switch_mode("ap")

        logger.info("Automatic configuration completed successfully")
        print(get_message('auto_config_success'))
        return True

    except Exception as e:
        logger.error(f"Error during automatic configuration: {e}")
        print(get_message('auto_config_error'))
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

    # Check current mode
    current_mode = get_current_mode()
    print(f"Current mode: {get_message('ap_mode' if current_mode == 'ap' else 'client_mode')}")

    # Check for USB WiFi dongle
    usb_wifi_interface = detect_usb_wifi_dongle()
    if usb_wifi_interface:
        print(f"USB WiFi dongle: {usb_wifi_interface}")
    else:
        print("USB WiFi dongle: Not detected")

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
    parser = argparse.ArgumentParser(description="Raspberry Pi 5 Access Point Setup")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--configure", action="store_true", help="Configure the access point")
    group.add_argument("--enable", action="store_true", help="Enable the access point")
    group.add_argument("--disable", action="store_true", help="Disable the access point")
    group.add_argument("--status", action="store_true", help="Check the status of the access point")
    group.add_argument("--switch-mode", choices=["ap", "client"], 
                      help="Switch between access point mode (ap) and client mode (client)")
    group.add_argument("--auto-config", action="store_true", 
                      help="Automatically configure based on USB WiFi dongle presence")

    args = parser.parse_args()

    # Check if running as root for all operations except status
    if not args.status:
        check_root()

    if args.configure:
        configure_ap()
    elif args.enable:
        enable_services()
    elif args.disable:
        disable_services()
    elif args.status:
        check_status()
    elif args.switch_mode:
        switch_mode(args.switch_mode)
    elif args.auto_config:
        auto_configure()
    else:
        parser.print_help()

def warn_if_networkmanager():
    """Warn if NetworkManager is detected on the system."""
    try:
        result = subprocess.run(["which", "nmcli"], capture_output=True, text=True)
        if result.returncode == 0:
            logger.warning("NetworkManager is installed. Consider configuring IP with nmcli instead of dhcpcd.")
    except Exception as e:
        logger.error(f"Failed to check for NetworkManager: {e}")


# Example call for the warning at script startup
warn_if_networkmanager()

if __name__ == "__main__":
    main()