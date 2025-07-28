import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, UnivariateSpline
from scipy.signal import find_peaks
import os
import csv
import glob
from datetime import datetime

# Note: This program can use pandas for easier data handling if available
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("pandas モジュールが見つかりません。基本的な CSV 処理を使用します。")
    print("pandas をインストールするには: pip install pandas")
    print("より高度な機能を使用するには pandas のインストールをお勧めします。")

def get_float_input(prompt, default, min_val=None, max_val=None):
    """Get float input from user with validation"""
    while True:
        try:
            value_str = input(f"{prompt} [{default}]: ").strip()
            if value_str == "":
                return default
            value = float(value_str)
            
            if min_val is not None and value < min_val:
                print(f"値が小さすぎます。{min_val}以上の値を入力してください。")
                continue
            if max_val is not None and value > max_val:
                print(f"値が大きすぎます。{max_val}以下の値を入力してください。")
                continue
                
            return value
        except ValueError:
            print("有効な数値を入力してください。")

def get_int_input(prompt, default, min_val=None, max_val=None):
    """Get integer input from user with validation"""
    while True:
        try:
            value_str = input(f"{prompt} [{default}]: ").strip()
            if value_str == "":
                return default
            value = int(value_str)
            
            if min_val is not None and value < min_val:
                print(f"値が小さすぎます。{min_val}以上の値を入力してください。")
                continue
            if max_val is not None and value > max_val:
                print(f"値が大きすぎます。{max_val}以下の値を入力してください。")
                continue
                
            return value
        except ValueError:
            print("有効な整数を入力してください。")

def get_yes_no_input(prompt, default=True):
    """Get yes/no input from user"""
    default_str = "Y" if default else "N"
    while True:
        response = input(f"{prompt} [{default_str}]: ").strip().upper()
        if response == "":
            return default
        if response in ["Y", "YES"]:
            return True
        if response in ["N", "NO"]:
            return False
        print("Y または N で回答してください。")

def find_csv_files(directory="results", pattern="*dqdv*.csv"):
    """Find CSV files matching the pattern in the directory"""
    files = glob.glob(os.path.join(directory, pattern))
    return sorted(files)

def load_csv_file(file_path):
    """Load data from a CSV file"""
    if PANDAS_AVAILABLE:
        try:
            df = pd.read_csv(file_path)
            # Check if the required columns exist
            if 'Voltage (V)' in df.columns and 'dQ/dV (Ah/V)' in df.columns:
                return df
            else:
                print(f"警告: ファイル {file_path} に必要な列がありません。")
                return None
        except Exception as e:
            print(f"エラー: ファイル {file_path} の読み込みに失敗しました: {e}")
            return None
    else:
        # Fallback to basic CSV processing without pandas
        try:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)  # Read header row
                
                # Check if required columns exist
                voltage_idx = None
                dqdv_idx = None
                
                for i, header in enumerate(headers):
                    if header == 'Voltage (V)':
                        voltage_idx = i
                    elif header == 'dQ/dV (Ah/V)':
                        dqdv_idx = i
                
                if voltage_idx is None or dqdv_idx is None:
                    print(f"警告: ファイル {file_path} に必要な列がありません。")
                    return None
                
                # Read data
                voltage = []
                dqdv = []
                
                for row in reader:
                    if len(row) > max(voltage_idx, dqdv_idx):
                        try:
                            vol = float(row[voltage_idx])
                            dq = float(row[dqdv_idx])
                            voltage.append(vol)
                            dqdv.append(dq)
                        except ValueError:
                            # Skip rows with non-numeric values
                            continue
                
                # Create a simple dictionary to mimic pandas DataFrame
                return {
                    'Voltage (V)': np.array(voltage),
                    'dQ/dV (Ah/V)': np.array(dqdv),
                    'columns': headers
                }
        except Exception as e:
            print(f"エラー: ファイル {file_path} の読み込みに失敗しました: {e}")
            return None

def detect_peaks(voltage, dqdv, prominence=0.1, width=None, height=None, distance=None, v_min=None, v_max=None):
    """Detect peaks in dQ/dV curve with adjustable parameters"""
    # Filter data by voltage range if specified
    if v_min is not None or v_max is not None:
        v_min = voltage.min() if v_min is None else v_min
        v_max = voltage.max() if v_max is None else v_max
        mask = (voltage >= v_min) & (voltage <= v_max)
        voltage_filtered = voltage[mask]
        dqdv_filtered = dqdv[mask]
    else:
        voltage_filtered = voltage
        dqdv_filtered = dqdv
    
    # Find peaks
    peaks, properties = find_peaks(dqdv_filtered, prominence=prominence, width=width, height=height, distance=distance)
    
    # Get peak information
    peak_voltages = voltage_filtered[peaks]
    peak_dqdvs = dqdv_filtered[peaks]
    peak_prominences = properties['prominences']
    peak_widths = properties['widths'] if 'widths' in properties else np.zeros_like(peaks)
    
    # Create peak data
    peak_data = []
    for i in range(len(peaks)):
        peak_data.append({
            'index': peaks[i],
            'voltage': peak_voltages[i],
            'dqdv': peak_dqdvs[i],
            'prominence': peak_prominences[i],
            'width': peak_widths[i] if i < len(peak_widths) else 0
        })
    
    return peak_data, voltage_filtered, dqdv_filtered

def plot_dqdv_with_peaks(file_paths, prominence=0.1, width=None, height=None, distance=None, v_min=None, v_max=None):
    """Plot dQ/dV curves with detected peaks"""
    plt.figure(figsize=(12, 8))
    
    all_peak_data = []
    
    for file_path in file_paths:
        # Extract file info from filename
        file_name = os.path.basename(file_path)
        
        # Load data
        data = load_csv_file(file_path)
        if data is None:
            continue
        
        # Extract voltage and dQ/dV data
        if PANDAS_AVAILABLE:
            voltage = data['Voltage (V)'].values
            dqdv = data['dQ/dV (Ah/V)'].values
        else:
            voltage = data['Voltage (V)']
            dqdv = data['dQ/dV (Ah/V)']
        
        # Detect peaks
        peak_data, voltage_filtered, dqdv_filtered = detect_peaks(
            voltage, dqdv, prominence, width, height, distance, v_min, v_max
        )
        
        # Store peak data for potential CSV export
        for peak in peak_data:
            peak['file'] = file_name
        all_peak_data.extend(peak_data)
        
        # Plot dQ/dV curve
        plt.plot(voltage_filtered, dqdv_filtered, label=file_name)
        
        # Mark peaks
        peak_voltages = [peak['voltage'] for peak in peak_data]
        peak_dqdvs = [peak['dqdv'] for peak in peak_data]
        plt.plot(peak_voltages, peak_dqdvs, 'ro', markersize=8)
        
        # Annotate peaks
        for i, peak in enumerate(peak_data):
            plt.annotate(f"{i+1}", 
                        (peak['voltage'], peak['dqdv']),
                        xytext=(5, 5),
                        textcoords='offset points',
                        fontsize=9)
    
    # Set labels and title
    plt.xlabel('Voltage (V)')
    plt.ylabel('dQ/dV (Ah/V)')
    plt.title('dQ/dV Curves with Detected Peaks')
    plt.grid(True)
    plt.legend()
    
    plt.tight_layout()
    plt.show()
    
    return all_peak_data

def export_peaks_to_csv(peak_data):
    """Export peak data to CSV file"""
    if not peak_data:
        print("エクスポートするピークデータがありません。")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs('results', exist_ok=True)
    
    # Create output filename
    output_file = f"results/peaks_{timestamp}.csv"
    
    # Write data to CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['File', 'Peak Number', 'Voltage (V)', 'dQ/dV (Ah/V)', 'Prominence', 'Width'])
        
        # Group peaks by file
        files = set(peak['file'] for peak in peak_data)
        for file in files:
            file_peaks = [p for p in peak_data if p['file'] == file]
            for i, peak in enumerate(file_peaks):
                writer.writerow([
                    peak['file'],
                    i+1,
                    peak['voltage'],
                    peak['dqdv'],
                    peak['prominence'],
                    peak['width']
                ])
    
    print(f"ピークデータを保存しました: {output_file}")

def select_files_for_analysis():
    """Let the user select files for analysis"""
    # Find dQ/dV files
    dqdv_files = find_csv_files(pattern="*dqdv*.csv")
    
    # If no dQ/dV files, look for charge/discharge files
    if not dqdv_files:
        print("dQ/dV ファイルが見つかりません。充放電ファイルを検索します。")
        charge_files = find_csv_files(pattern="*charge*.csv")
        discharge_files = find_csv_files(pattern="*discharge*.csv")
        
        if not charge_files and not discharge_files:
            print("解析するCSVファイルが見つかりません。")
            print("先にシミュレーションを実行してCSVファイルを生成してください。")
            print("または LibDegradationSim03_DD.py を実行して dQ/dV データを生成してください。")
            return []
        
        print("\n利用可能なファイル:")
        all_files = charge_files + discharge_files
        for i, file in enumerate(all_files):
            print(f"{i+1}. {os.path.basename(file)}")
        
        print("\n注意: 充放電ファイルを選択した場合、先に dQ/dV 計算を実行する必要があります。")
        print("このプログラムは dQ/dV データを直接解析することを推奨します。")
        
        if get_yes_no_input("LibDegradationSim03_DD.py を実行して dQ/dV データを生成しますか？", True):
            print("LibDegradationSim03_DD.py を実行してください。")
            return []
    else:
        print("\n利用可能な dQ/dV ファイル:")
        for i, file in enumerate(dqdv_files):
            print(f"{i+1}. {os.path.basename(file)}")
    
        # Ask user to select files
        selected_indices = input("\n解析するファイルの番号をカンマ区切りで入力してください (例: 1,3,5): ").strip()
        if not selected_indices:
            return []
        
        try:
            indices = [int(idx.strip()) - 1 for idx in selected_indices.split(',')]
            selected_files = [dqdv_files[idx] for idx in indices if 0 <= idx < len(dqdv_files)]
            return selected_files
        except Exception as e:
            print(f"ファイル選択エラー: {e}")
            return []

def main():
    """Main function for peak detection in dQ/dV curves"""
    print("=" * 60)
    print("リチウムイオン電池シミュレーション - dQ/dV ピーク検出モード")
    print("=" * 60)
    print("このプログラムでは、dQ/dV 曲線からピークを検出して可視化します。")
    print("-" * 60)
    
    # Let user select files for analysis
    selected_files = select_files_for_analysis()
    if not selected_files:
        print("ファイルが選択されていないため、プログラムを終了します。")
        return
    
    # Get peak detection parameters
    print("\n【ピーク検出パラメータ】")
    prominence = get_float_input("ピークの顕著さ (prominence)", 0.1, min_val=0.0)
    
    use_width = get_yes_no_input("ピークの幅 (width) を指定しますか？", False)
    width = get_float_input("ピークの最小幅", 1.0, min_val=0.0) if use_width else None
    
    use_height = get_yes_no_input("ピークの高さ (height) を指定しますか？", False)
    height = get_float_input("ピークの最小高さ", 0.0, min_val=0.0) if use_height else None
    
    use_distance = get_yes_no_input("ピーク間の最小距離 (distance) を指定しますか？", False)
    distance = get_int_input("ピーク間の最小距離", 1, min_val=1) if use_distance else None
    
    # Get voltage range for peak detection
    use_v_range = get_yes_no_input("電圧範囲を指定しますか？", False)
    v_min = get_float_input("最小電圧 (V)", 3.0) if use_v_range else None
    v_max = get_float_input("最大電圧 (V)", 4.2) if use_v_range else None
    
    # Detect peaks and plot
    print("\nピークを検出しています...")
    peak_data = plot_dqdv_with_peaks(
        selected_files, prominence, width, height, distance, v_min, v_max
    )
    
    # Ask if user wants to export peak data to CSV
    if peak_data and get_yes_no_input("\nピークデータをCSVファイルに保存しますか？", True):
        export_peaks_to_csv(peak_data)
    
    print("\n解析が完了しました。")

if __name__ == "__main__":
    main()