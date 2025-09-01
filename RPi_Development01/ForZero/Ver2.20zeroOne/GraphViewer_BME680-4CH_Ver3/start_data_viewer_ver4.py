#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Launcher for DataViewer Ver4
Usage:
  sudo ~/envmonitor-venv/bin/python3 start_data_viewer_ver4.1.py
"""
import subprocess
import sys

if __name__ == '__main__':
    py = sys.executable or '/usr/bin/python3'
    cmd = [py, 'DataViewerVer4.1.py', '--port', '8081',
           '--p1-path', '/var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_fixed.csv',
           '--p2-path', '/var/lib(FromThonny)/raspap_solo/data/RawData_P2/P2_fixed.csv',
           '--p3-path', '/var/lib(FromThonny)/raspap_solo/data/RawData_P3/P3_fixed.csv',
           '--p4-path', '/var/lib(FromThonny)/raspap_solo/data/RawData_P4/P4_fixed.csv',
           '--days', '1']
    subprocess.run(cmd, check=True)
