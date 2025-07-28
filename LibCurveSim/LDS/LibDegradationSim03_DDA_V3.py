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
    """Load data from a CSV file, including current and phase data if available"""
    if PANDAS_AVAILABLE:
        try:
            df = pd.read_csv(file_path)
            # Check if the required columns exist
            if 'Voltage (V)' in df.columns and 'dQ/dV (Ah/V)' in df.columns:
                # Check for additional columns for V3 features
                has_current = 'Current (A)' in df.columns
                has_phase = 'Phase' in df.columns
                
                # Add flags to indicate which additional data is available
                df['has_current'] = has_current
                df['has_phase'] = has_phase
                
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
                current_idx = None
                phase_idx = None
                
                for i, header in enumerate(headers):
                    if header == 'Voltage (V)':
                        voltage_idx = i
                    elif header == 'dQ/dV (Ah/V)':
                        dqdv_idx = i
                    elif header == 'Current (A)':
                        current_idx = i
                    elif header == 'Phase':
                        phase_idx = i
                
                if voltage_idx is None or dqdv_idx is None:
                    print(f"警告: ファイル {file_path} に必要な列がありません。")
                    return None
                
                # Read data
                voltage = []
                dqdv = []
                current = [] if current_idx is not None else None
                phase = [] if phase_idx is not None else None
                
                for row in reader:
                    if len(row) > max(voltage_idx, dqdv_idx):
                        try:
                            vol = float(row[voltage_idx])
                            dq = float(row[dqdv_idx])
                            voltage.append(vol)
                            dqdv.append(dq)
                            
                            if current_idx is not None and len(row) > current_idx:
                                current.append(float(row[current_idx]))
                            if phase_idx is not None and len(row) > phase_idx:
                                phase.append(row[phase_idx])
                        except ValueError:
                            # Skip rows with non-numeric values
                            continue
                
                # Create a simple dictionary to mimic pandas DataFrame
                result = {
                    'Voltage (V)': np.array(voltage),
                    'dQ/dV (Ah/V)': np.array(dqdv),
                    'columns': headers,
                    'has_current': current is not None,
                    'has_phase': phase is not None
                }
                
                if current is not None:
                    result['Current (A)'] = np.array(current)
                if phase is not None:
                    result['Phase'] = np.array(phase)
                
                return result
        except Exception as e:
            print(f"エラー: ファイル {file_path} の読み込みに失敗しました: {e}")
            return None

def detect_peaks(voltage, dqdv, prominence=0.1, width=None, height=None, distance=None, v_min=None, v_max=None, current=None, phase=None):
    """
    Detect peaks in dQ/dV curve with adjustable parameters, optionally separating by phase
    Returns peak data, filtered voltage, and filtered dQ/dV
    """
    # Filter data by voltage range if specified
    if v_min is not None or v_max is not None:
        v_min = voltage.min() if v_min is None else v_min
        v_max = voltage.max() if v_max is None else v_max
        mask = (voltage >= v_min) & (voltage <= v_max)
        voltage_filtered = voltage[mask]
        dqdv_filtered = dqdv[mask]
        current_filtered = current[mask] if current is not None else None
        phase_filtered = phase[mask] if phase is not None else None
    else:
        voltage_filtered = voltage
        dqdv_filtered = dqdv
        current_filtered = current
        phase_filtered = phase
    
    # If phase data is available, separate by phase
    if phase_filtered is not None:
        # Detect peaks for each phase separately
        peak_data = []
        
        # Process CC phase
        cc_mask = (phase_filtered == 'CC')
        if np.any(cc_mask):
            cc_voltage = voltage_filtered[cc_mask]
            cc_dqdv = dqdv_filtered[cc_mask]
            cc_current = current_filtered[cc_mask] if current_filtered is not None else None
            
            # Find peaks in CC phase
            cc_peaks, cc_properties = find_peaks(cc_dqdv, prominence=prominence, width=width, height=height, distance=distance)
            
            # Get peak information for CC phase
            for i in range(len(cc_peaks)):
                peak_data.append({
                    'index': cc_peaks[i],
                    'voltage': cc_voltage[cc_peaks[i]],
                    'dqdv': cc_dqdv[cc_peaks[i]],
                    'prominence': cc_properties['prominences'][i],
                    'width': cc_properties['widths'][i] if 'widths' in cc_properties else 0,
                    'phase': 'CC',
                    'current': cc_current[cc_peaks[i]] if cc_current is not None else None
                })
        
        # Process CV phase
        cv_mask = (phase_filtered == 'CV')
        if np.any(cv_mask):
            cv_voltage = voltage_filtered[cv_mask]
            cv_dqdv = dqdv_filtered[cv_mask]
            cv_current = current_filtered[cv_mask] if current_filtered is not None else None
            
            # Find peaks in CV phase
            cv_peaks, cv_properties = find_peaks(cv_dqdv, prominence=prominence, width=width, height=height, distance=distance)
            
            # Get peak information for CV phase
            for i in range(len(cv_peaks)):
                peak_data.append({
                    'index': cv_peaks[i],
                    'voltage': cv_voltage[cv_peaks[i]],
                    'dqdv': cv_dqdv[cv_peaks[i]],
                    'prominence': cv_properties['prominences'][i],
                    'width': cv_properties['widths'][i] if 'widths' in cv_properties else 0,
                    'phase': 'CV',
                    'current': cv_current[cv_peaks[i]] if cv_current is not None else None
                })
    else:
        # Find peaks without phase separation
        peaks, properties = find_peaks(dqdv_filtered, prominence=prominence, width=width, height=height, distance=distance)
        
        # Get peak information
        peak_voltages = voltage_filtered[peaks]
        peak_dqdvs = dqdv_filtered[peaks]
        peak_prominences = properties['prominences']
        peak_widths = properties['widths'] if 'widths' in properties else np.zeros_like(peaks)
        peak_currents = current_filtered[peaks] if current_filtered is not None else None
        
        # Create peak data
        peak_data = []
        for i in range(len(peaks)):
            peak_data.append({
                'index': peaks[i],
                'voltage': peak_voltages[i],
                'dqdv': peak_dqdvs[i],
                'prominence': peak_prominences[i],
                'width': peak_widths[i] if i < len(peak_widths) else 0,
                'phase': None,
                'current': peak_currents[i] if peak_currents is not None else None
            })
    
    return peak_data, voltage_filtered, dqdv_filtered, current_filtered, phase_filtered

def plot_dqdv_with_peaks(file_paths, prominence=0.1, width=None, height=None, distance=None, v_min=None, v_max=None, show_current=False):
    """Plot dQ/dV curves with detected peaks, optionally showing current"""
    if show_current:
        # Two subplots: dQ/dV and current
        fig, axs = plt.subplots(2, 1, figsize=(12, 10))
    else:
        # Single plot for dQ/dV
        plt.figure(figsize=(12, 6))
        axs = None
    
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
            
            # Check if current and phase data are available
            has_current = data.get('has_current', False)
            has_phase = data.get('has_phase', False)
            current = data['Current (A)'].values if has_current else None
            phase = data['Phase'].values if has_phase else None
        else:
            voltage = data['Voltage (V)']
            dqdv = data['dQ/dV (Ah/V)']
            
            # Check if current and phase data are available
            has_current = 'has_current' in data and data['has_current']
            has_phase = 'has_phase' in data and data['has_phase']
            current = data['Current (A)'] if has_current else None
            phase = data['Phase'] if has_phase else None
        
        # Detect peaks
        peak_data, voltage_filtered, dqdv_filtered, current_filtered, phase_filtered = detect_peaks(
            voltage, dqdv, prominence, width, height, distance, v_min, v_max, current, phase
        )
        
        # Store peak data for potential CSV export
        for peak in peak_data:
            peak['file'] = file_name
        all_peak_data.extend(peak_data)
        
        # Plot dQ/dV curve
        ax = axs[0] if axs is not None else plt
        
        if has_phase:
            # Split data by phase
            cc_mask = (phase_filtered == 'CC')
            cv_mask = (phase_filtered == 'CV')
            
            if np.any(cc_mask):
                ax.plot(voltage_filtered[cc_mask], dqdv_filtered[cc_mask], 'b-', label=f'{file_name} (CC)')
            if np.any(cv_mask):
                ax.plot(voltage_filtered[cv_mask], dqdv_filtered[cv_mask], 'r-', label=f'{file_name} (CV)')
        else:
            ax.plot(voltage_filtered, dqdv_filtered, label=file_name)
        
        # Mark peaks
        cc_peaks = [peak for peak in peak_data if peak['phase'] == 'CC']
        cv_peaks = [peak for peak in peak_data if peak['phase'] == 'CV']
        other_peaks = [peak for peak in peak_data if peak['phase'] is None]
        
        if cc_peaks:
            cc_voltages = [peak['voltage'] for peak in cc_peaks]
            cc_dqdvs = [peak['dqdv'] for peak in cc_peaks]
            ax.plot(cc_voltages, cc_dqdvs, 'bo', markersize=8)
        
        if cv_peaks:
            cv_voltages = [peak['voltage'] for peak in cv_peaks]
            cv_dqdvs = [peak['dqdv'] for peak in cv_peaks]
            ax.plot(cv_voltages, cv_dqdvs, 'ro', markersize=8)
        
        if other_peaks:
            other_voltages = [peak['voltage'] for peak in other_peaks]
            other_dqdvs = [peak['dqdv'] for peak in other_peaks]
            ax.plot(other_voltages, other_dqdvs, 'go', markersize=8)
        
        # Annotate peaks
        for i, peak in enumerate(peak_data):
            ax.annotate(f"{i+1}", 
                      (peak['voltage'], peak['dqdv']),
                      xytext=(5, 5),
                      textcoords='offset points',
                      fontsize=9)
        
        # Plot current vs voltage if available and requested
        if show_current and current_filtered is not None:
            ax = axs[1]
            
            if has_phase:
                # Split data by phase
                cc_mask = (phase_filtered == 'CC')
                cv_mask = (phase_filtered == 'CV')
                
                if np.any(cc_mask):
                    ax.plot(voltage_filtered[cc_mask], current_filtered[cc_mask], 'b-', label=f'{file_name} (CC)')
                if np.any(cv_mask):
                    ax.plot(voltage_filtered[cv_mask], current_filtered[cv_mask], 'r-', label=f'{file_name} (CV)')
            else:
                ax.plot(voltage_filtered, current_filtered, label=file_name)
            
            # Mark peak positions on current plot
            if cc_peaks:
                cc_voltages = [peak['voltage'] for peak in cc_peaks]
                cc_currents = [peak['current'] for peak in cc_peaks]
                ax.plot(cc_voltages, cc_currents, 'bo', markersize=8)
            
            if cv_peaks:
                cv_voltages = [peak['voltage'] for peak in cv_peaks]
                cv_currents = [peak['current'] for peak in cv_peaks]
                ax.plot(cv_voltages, cv_currents, 'ro', markersize=8)
            
            if other_peaks and all(peak['current'] is not None for peak in other_peaks):
                other_voltages = [peak['voltage'] for peak in other_peaks]
                other_currents = [peak['current'] for peak in other_peaks]
                ax.plot(other_voltages, other_currents, 'go', markersize=8)
    
    # Set labels and title for dQ/dV plot
    ax = axs[0] if axs is not None else plt
    ax.set_xlabel('Voltage (V)')
    ax.set_ylabel('dQ/dV (Ah/V)')
    ax.set_title('dQ/dV Curves with Detected Peaks')
    ax.grid(True)
    ax.legend()
    
    # Set labels and title for current plot if shown
    if show_current:
        ax = axs[1]
        ax.set_xlabel('Voltage (V)')
        ax.set_ylabel('Current (A)')
        ax.set_title('Current vs Voltage with Peak Positions')
        ax.grid(True)
        ax.legend()
    
    plt.tight_layout()
    plt.show()
    
    return all_peak_data

def analyze_peak_current_relationship(peak_data):
    """Analyze the relationship between peak characteristics and current"""
    # Check if there's any peak data with current information
    has_current_data = False
    for peak in peak_data:
        if peak['current'] is not None:
            has_current_data = True
            break
    
    if not has_current_data:
        print("電流データが含まれるピークがありません。")
        return
    
    # Filter peaks with current data
    peaks_with_current = [peak for peak in peak_data if peak['current'] is not None]
    
    # Group peaks by phase
    cc_peaks = [peak for peak in peaks_with_current if peak['phase'] == 'CC']
    cv_peaks = [peak for peak in peaks_with_current if peak['phase'] == 'CV']
    other_peaks = [peak for peak in peaks_with_current if peak['phase'] is None]
    
    plt.figure(figsize=(15, 10))
    
    # Plot peak prominence vs current
    plt.subplot(2, 2, 1)
    
    if cc_peaks:
        cc_currents = [peak['current'] for peak in cc_peaks]
        cc_prominences = [peak['prominence'] for peak in cc_peaks]
        plt.scatter(cc_currents, cc_prominences, c='blue', label='CC Phase')
    
    if cv_peaks:
        cv_currents = [peak['current'] for peak in cv_peaks]
        cv_prominences = [peak['prominence'] for peak in cv_peaks]
        plt.scatter(cv_currents, cv_prominences, c='red', label='CV Phase')
    
    if other_peaks:
        other_currents = [peak['current'] for peak in other_peaks]
        other_prominences = [peak['prominence'] for peak in other_peaks]
        plt.scatter(other_currents, other_prominences, c='green', label='Unknown Phase')
    
    plt.xlabel('Current (A)')
    plt.ylabel('Peak Prominence')
    plt.title('Peak Prominence vs Current')
    plt.grid(True)
    plt.legend()
    
    # Plot peak width vs current
    plt.subplot(2, 2, 2)
    
    if cc_peaks:
        cc_currents = [peak['current'] for peak in cc_peaks]
        cc_widths = [peak['width'] for peak in cc_peaks]
        plt.scatter(cc_currents, cc_widths, c='blue', label='CC Phase')
    
    if cv_peaks:
        cv_currents = [peak['current'] for peak in cv_peaks]
        cv_widths = [peak['width'] for peak in cv_peaks]
        plt.scatter(cv_currents, cv_widths, c='red', label='CV Phase')
    
    if other_peaks:
        other_currents = [peak['current'] for peak in other_peaks]
        other_widths = [peak['width'] for peak in other_peaks]
        plt.scatter(other_currents, other_widths, c='green', label='Unknown Phase')
    
    plt.xlabel('Current (A)')
    plt.ylabel('Peak Width')
    plt.title('Peak Width vs Current')
    plt.grid(True)
    plt.legend()
    
    # Plot peak height (dQ/dV) vs current
    plt.subplot(2, 2, 3)
    
    if cc_peaks:
        cc_currents = [peak['current'] for peak in cc_peaks]
        cc_heights = [peak['dqdv'] for peak in cc_peaks]
        plt.scatter(cc_currents, cc_heights, c='blue', label='CC Phase')
    
    if cv_peaks:
        cv_currents = [peak['current'] for peak in cv_peaks]
        cv_heights = [peak['dqdv'] for peak in cv_peaks]
        plt.scatter(cv_currents, cv_heights, c='red', label='CV Phase')
    
    if other_peaks:
        other_currents = [peak['current'] for peak in other_peaks]
        other_heights = [peak['dqdv'] for peak in other_peaks]
        plt.scatter(other_currents, other_heights, c='green', label='Unknown Phase')
    
    plt.xlabel('Current (A)')
    plt.ylabel('Peak Height (dQ/dV)')
    plt.title('Peak Height vs Current')
    plt.grid(True)
    plt.legend()
    
    # Plot peak voltage vs current
    plt.subplot(2, 2, 4)
    
    if cc_peaks:
        cc_currents = [peak['current'] for peak in cc_peaks]
        cc_voltages = [peak['voltage'] for peak in cc_peaks]
        plt.scatter(cc_currents, cc_voltages, c='blue', label='CC Phase')
    
    if cv_peaks:
        cv_currents = [peak['current'] for peak in cv_peaks]
        cv_voltages = [peak['voltage'] for peak in cv_peaks]
        plt.scatter(cv_currents, cv_voltages, c='red', label='CV Phase')
    
    if other_peaks:
        other_currents = [peak['current'] for peak in other_peaks]
        other_voltages = [peak['voltage'] for peak in other_peaks]
        plt.scatter(other_currents, other_voltages, c='green', label='Unknown Phase')
    
    plt.xlabel('Current (A)')
    plt.ylabel('Peak Voltage (V)')
    plt.title('Peak Voltage vs Current')
    plt.grid(True)
    plt.legend()
    
    plt.tight_layout()
    plt.show()

def export_peaks_to_csv(peak_data):
    """Export peak data to CSV file, including current and phase if available"""
    if not peak_data:
        print("エクスポートするピークデータがありません。")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs('results', exist_ok=True)
    
    # Create output filename
    output_file = f"results/peaks_{timestamp}.csv"
    
    # Check if current and phase data are available
    has_current = any(peak.get('current') is not None for peak in peak_data)
    has_phase = any(peak.get('phase') is not None for peak in peak_data)
    
    # Prepare headers based on available data
    headers = ['File', 'Peak Number', 'Voltage (V)', 'dQ/dV (Ah/V)', 'Prominence', 'Width']
    if has_current:
        headers.append('Current (A)')
    if has_phase:
        headers.append('Phase')
    
    # Write data to CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        # Group peaks by file
        files = set(peak['file'] for peak in peak_data)
        for file in files:
            file_peaks = [p for p in peak_data if p['file'] == file]
            for i, peak in enumerate(file_peaks):
                row = [
                    peak['file'],
                    i+1,
                    peak['voltage'],
                    peak['dqdv'],
                    peak['prominence'],
                    peak['width']
                ]
                if has_current:
                    row.append(peak.get('current', 'N/A'))
                if has_phase:
                    row.append(peak.get('phase', 'Unknown'))
                writer.writerow(row)
    
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
            print("または LibDegradationSim03_DD_V3.py を実行して dQ/dV データを生成してください。")
            return []
        
        print("\n利用可能なファイル:")
        all_files = charge_files + discharge_files
        for i, file in enumerate(all_files):
            print(f"{i+1}. {os.path.basename(file)}")
        
        print("\n注意: 充放電ファイルを選択した場合、先に dQ/dV 計算を実行する必要があります。")
        print("このプログラムは dQ/dV データを直接解析することを推奨します。")
        
        if get_yes_no_input("LibDegradationSim03_DD_V3.py を実行して dQ/dV データを生成しますか？", True):
            print("LibDegradationSim03_DD_V3.py を実行してください。")
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
    """Main function for peak detection in dQ/dV curves with CV current tracking"""
    print("=" * 60)
    print("リチウムイオン電池シミュレーション - dQ/dV ピーク検出モード (V3)")
    print("=" * 60)
    print("このプログラムでは、dQ/dV 曲線からピークを検出して可視化します。")
    print("V3では、CV充電時の電流とピーク特性の関係を解析する機能が追加されています。")
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
    
    # Ask if user wants to see current vs voltage plot (V3 feature)
    show_current = get_yes_no_input("電流-電圧曲線も表示しますか？", True)
    
    # Detect peaks and plot
    print("\nピークを検出しています...")
    peak_data = plot_dqdv_with_peaks(
        selected_files, prominence, width, height, distance, v_min, v_max, show_current
    )
    
    # Check if there's any peak data with current information
    has_current_data = False
    for peak in peak_data:
        if peak.get('current') is not None:
            has_current_data = True
            break
    
    # If current data is available, ask if user wants to analyze peak-current relationship
    if has_current_data and get_yes_no_input("\nピーク特性と電流の関係を解析しますか？", True):
        analyze_peak_current_relationship(peak_data)
    
    # Ask if user wants to export peak data to CSV
    if peak_data and get_yes_no_input("\nピークデータをCSVファイルに保存しますか？", True):
        export_peaks_to_csv(peak_data)
    
    print("\n解析が完了しました。")

if __name__ == "__main__":
    main()