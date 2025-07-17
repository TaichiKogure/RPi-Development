"""
Signal Strength Measurement Module

This module contains functions for measuring WiFi signal strength.
"""

import re
import subprocess
import logging

logger = logging.getLogger(__name__)

def get_signal_strength(device_id, device_info, interface):
    """
    Get the WiFi signal strength for the specified device.
    
    Args:
        device_id (str): The device ID (P2 or P3)
        device_info (dict): Device information including IP and MAC address
        interface (str): The WiFi interface to use
        
    Returns:
        int or None: Signal strength in dBm, or None if measurement fails
    """
    if not device_info or not device_info.get("ip"):
        logger.warning(f"No IP address configured for {device_id}")
        return None

    # First, try to get the MAC address if we don't have it
    if not device_info.get("mac"):
        try:
            # Ping the device to ensure it's in the ARP table
            subprocess.run(
                ["ping", "-c", "1", "-W", "1", device_info["ip"]],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Get the MAC address from the ARP table
            arp_output = subprocess.check_output(
                ["arp", "-n", device_info["ip"]],
                universal_newlines=True
            )

            # Extract MAC address using regex
            mac_match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", arp_output)
            if mac_match:
                device_info["mac"] = mac_match.group(0)
                logger.info(f"Found MAC address for {device_id}: {device_info['mac']}")
            else:
                logger.warning(f"Could not find MAC address for {device_id}")
                return None
        except subprocess.SubprocessError as e:
            logger.error(f"Error getting MAC address for {device_id}: {e}")
            return None

    try:
        # Get signal strength using iw
        iw_output = subprocess.check_output(
            ["iw", "dev", interface, "station", "dump"],
            universal_newlines=True
        )

        # Find the section for our device's MAC address
        mac_section = None
        sections = iw_output.split("Station")
        for section in sections:
            if device_info["mac"].lower() in section.lower():
                mac_section = section
                break

        if not mac_section:
            logger.warning(f"Device {device_id} ({device_info['mac']}) not found in iw output")
            return None

        # Extract signal strength
        signal_match = re.search(r"signal:\s*([-\d]+)\s*dBm", mac_section)
        if signal_match:
            signal_strength = int(signal_match.group(1))
            logger.debug(f"Signal strength for {device_id}: {signal_strength} dBm")
            return signal_strength
        else:
            logger.warning(f"Could not find signal strength for {device_id}")
            return None
    except subprocess.SubprocessError as e:
        logger.error(f"Error getting signal strength for {device_id}: {e}")
        return None