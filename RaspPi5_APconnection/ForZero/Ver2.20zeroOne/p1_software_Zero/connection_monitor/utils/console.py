"""
Console Output Module for Connection Monitor

This module contains functions for displaying connection status in the console.
"""

import datetime
import logging

logger = logging.getLogger(__name__)

def print_connection_status(monitor):
    """
    Print the current connection status to the console.
    
    Args:
        monitor: The WiFiMonitor instance
    """
    with monitor.lock:
        latest_data = {
            device_id: data.get("latest", {})
            for device_id, data in monitor.connection_data.items()
        }

    print("\n" + "=" * 60)
    print(f"WiFi Connection Status - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    for device_id, data in latest_data.items():
        print(f"\nDevice: {device_id}")
        print("-" * 30)

        if not data:
            print("No data available")
            continue

        status = "ONLINE" if data.get("online", False) else "OFFLINE"
        print(f"Status: {status}")

        if data.get("online", False):
            signal_str = f"{data.get('signal_strength')} dBm" if data.get('signal_strength') is not None else "N/A"
            print(f"Signal Strength: {signal_str}")

            noise_str = f"{data.get('noise_level')} dBm" if data.get('noise_level') is not None else "N/A"
            print(f"Noise Level: {noise_str}")

            snr_str = f"{data.get('snr')} dB" if data.get('snr') is not None else "N/A"
            print(f"Signal-to-Noise Ratio: {snr_str}")

            ping_str = f"{data.get('ping_time'):.2f} ms" if data.get('ping_time') is not None else "N/A"
            print(f"Ping Time: {ping_str}")

            # Add signal quality assessment
            if data.get('signal_strength') is not None:
                signal = data.get('signal_strength')
                if signal >= -50:
                    quality = "Excellent"
                elif signal >= -60:
                    quality = "Very Good"
                elif signal >= -70:
                    quality = "Good"
                elif signal >= -80:
                    quality = "Fair"
                else:
                    quality = "Poor"
                print(f"Signal Quality: {quality}")

    print("\n" + "=" * 60)
    print("Press Ctrl+C to exit")