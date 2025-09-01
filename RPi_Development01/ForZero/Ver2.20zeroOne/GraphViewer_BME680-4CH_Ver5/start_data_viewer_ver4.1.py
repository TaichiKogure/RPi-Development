#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DataViewer Ver4 起動ランチャー（Ver4.1 パッチ）
- 表示期間の手動指定は廃止され、直近24時間固定になりました。
- グラフは10分ごとに自動更新されます。
使い方:
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
           '--p4-path', '/var/lib(FromThonny)/raspap_solo/data/RawData_P4/P4_fixed.csv']
    subprocess.run(cmd, check=True)
