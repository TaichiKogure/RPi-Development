"""
Noise Level Measurement Module

This module contains functions for measuring WiFi noise levels.
"""

import re
import subprocess
import logging

logger = logging.getLogger(__name__)

def get_noise_level(interface):
    """
    Get the WiFi noise level on the current channel.
    
    Args:
        interface (str): The WiFi interface to use
        
    Returns:
        int or None: Noise level in dBm, or None if measurement fails
    """
    try:
        # Get the current channel
        iw_output = subprocess.check_output(
            ["iw", "dev", interface, "info"],
            universal_newlines=True
        )

        channel_match = re.search(r"channel\s*(\d+)", iw_output)
        if not channel_match:
            logger.warning("Could not determine current WiFi channel")
            return None

        channel = channel_match.group(1)

        # Get noise level using iw survey
        survey_output = subprocess.check_output(
            ["iw", "dev", interface, "survey", "dump"],
            universal_newlines=True
        )

        # Find the section for the current frequency
        noise_level = None
        in_current_channel = False
        for line in survey_output.splitlines():
            if f"frequency:" in line and channel in line:
                in_current_channel = True
            elif "frequency:" in line and in_current_channel:
                break
            elif in_current_channel and "noise:" in line:
                noise_match = re.search(r"noise:\s*([-\d]+)\s*dBm", line)
                if noise_match:
                    noise_level = int(noise_match.group(1))
                    break

        if noise_level is not None:
            logger.debug(f"Noise level on channel {channel}: {noise_level} dBm")
            return noise_level
        else:
            logger.warning(f"Could not find noise level for channel {channel}")
            return None
    except subprocess.SubprocessError as e:
        logger.error(f"Error getting noise level: {e}")
        return None