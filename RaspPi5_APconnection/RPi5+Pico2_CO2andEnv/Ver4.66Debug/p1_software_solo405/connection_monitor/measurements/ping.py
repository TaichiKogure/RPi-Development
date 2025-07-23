"""
Ping Measurement Module

This module contains functions for measuring ping times and checking device online status.
"""

import re
import subprocess
import logging

logger = logging.getLogger(__name__)

def measure_ping(device_id, device_info, ping_count, ping_timeout):
    """
    Measure ping time to the specified device.
    
    Args:
        device_id (str): The device ID (P2 or P3)
        device_info (dict): Device information including IP address
        ping_count (int): Number of ping packets to send
        ping_timeout (int): Timeout for ping in seconds
        
    Returns:
        float or None: Average ping time in milliseconds, or None if measurement fails
    """
    if not device_info or not device_info.get("ip"):
        logger.warning(f"No IP address configured for {device_id}")
        return None

    try:
        # Measure ping time
        ping_output = subprocess.check_output(
            [
                "ping", "-c", str(ping_count),
                "-W", str(ping_timeout),
                device_info["ip"]
            ],
            universal_newlines=True
        )

        # Extract average ping time
        avg_match = re.search(r"min/avg/max/mdev = [\d.]+/([\d.]+)/[\d.]+/[\d.]+", ping_output)
        if avg_match:
            avg_ping = float(avg_match.group(1))
            logger.debug(f"Average ping time to {device_id}: {avg_ping} ms")
            return avg_ping
        else:
            logger.warning(f"Could not extract ping time for {device_id}")
            return None
    except subprocess.SubprocessError as e:
        logger.error(f"Error pinging {device_id}: {e}")
        return None

def check_device_online(device_id, device_info):
    """
    Check if the device is online.
    
    Args:
        device_id (str): The device ID (P2 or P3)
        device_info (dict): Device information including IP address
        
    Returns:
        bool: True if the device is online, False otherwise
    """
    if not device_info or not device_info.get("ip"):
        return False

    try:
        # Try to ping the device once
        result = subprocess.run(
            [
                "ping", "-c", "1", "-W", "1", device_info["ip"]
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        return result.returncode == 0
    except subprocess.SubprocessError:
        return False