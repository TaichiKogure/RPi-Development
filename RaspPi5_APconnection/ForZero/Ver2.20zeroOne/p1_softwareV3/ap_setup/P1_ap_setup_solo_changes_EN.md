# P1_ap_setup_solo.py Change Report - Ver2.1

## Overview
This document explains the changes made to the `P1_ap_setup_solo.py` script to make it compatible with Ver2.0. Ver2.0 is a system that uses only BME680 sensors and does not use CO2 sensors (MH-Z19C).

## Changes Made

### 1. Version Number Update
- Updated the version number from "4.0.0-solo" to "2.1.0"
- Updated the script description from "Solo Version 4.0" to "Solo Version 2.1"

### 2. Removal of MH-Z19C Sensor References
- Removed references to "MH-Z19C" sensors in the docstring, mentioning only BME680 sensors

### 3. Device List Update
- Updated the device list in the docstring from "P2 and P3" to "P2, P3, P4, P5, and P6"
- This clarifies that the script supports all five sensor nodes

### 4. DNSMasq Configuration Comment Update
- Updated the DNSMasq configuration comment from "Solo Ver4.0" to "Solo Ver2.1"

## Unchanged Functionality
The following functionality remains unchanged:

1. Access point configuration (SSID, password, IP address, etc.)
2. DHCP server configuration
3. IP forwarding configuration
4. Service enable/disable functionality
5. Status check functionality

## Configuration Parameters
The current configuration parameters are as follows:

```python
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
```

## Usage
The usage of the script remains unchanged:

```bash
sudo python3 P1_ap_setup_solo.py [--configure | --enable | --disable | --status]
```

- `--configure`: Configure the access point
- `--enable`: Enable the access point
- `--disable`: Disable the access point
- `--status`: Check the status of the access point

## Important Notes
- This script must be run with root privileges (sudo)
- It is recommended to reboot the Raspberry Pi after making configuration changes
- The Ver2.0 system only supports BME680 sensors and does not support CO2 sensors (MH-Z19C)