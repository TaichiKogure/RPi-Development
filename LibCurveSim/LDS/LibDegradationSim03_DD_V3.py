import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, UnivariateSpline
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

def find_csv_files(directory="results", pattern="*charge*.csv"):
    """Find CSV files matching the pattern in the directory"""
    files = glob.glob(os.path.join(directory, pattern))
    return sorted(files)

def load_csv_file(file_path):
    """Load data from a CSV file, including current and phase data if available"""
    if PANDAS_AVAILABLE:
        try:
            df = pd.read_csv(file_path)
            # Check if the required columns exist
            if 'Capacity (Ah)' in df.columns and 'Voltage (V)' in df.columns:
                # Check for additional columns for V3 features
                has_current = 'Current (A)' in df.columns
                has_phase = 'Phase' in df.columns
                has_time = 'Time (s)' in df.columns
                
                return df, has_current, has_phase, has_time
            else:
                print(f"警告: ファイル {file_path} に必要な列がありません。")
                return None, False, False, False
        except Exception as e:
            print(f"エラー: ファイル {file_path} の読み込みに失敗しました: {e}")
            return None, False, False, False
    else:
        # Fallback to basic CSV processing without pandas
        try:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)  # Read header row
                
                # Check if required columns exist
                capacity_idx = None
                voltage_idx = None
                current_idx = None
                phase_idx = None
                time_idx = None
                
                for i, header in enumerate(headers):
                    if header == 'Capacity (Ah)':
                        capacity_idx = i
                    elif header == 'Voltage (V)':
                        voltage_idx = i
                    elif header == 'Current (A)':
                        current_idx = i
                    elif header == 'Phase':
                        phase_idx = i
                    elif header == 'Time (s)':
                        time_idx = i
                
                if capacity_idx is None or voltage_idx is None:
                    print(f"警告: ファイル {file_path} に必要な列がありません。")
                    return None, False, False, False
                
                # Read data
                capacity = []
                voltage = []
                current = [] if current_idx is not None else None
                phase = [] if phase_idx is not None else None
                time = [] if time_idx is not None else None
                
                for row in reader:
                    if len(row) > max(capacity_idx, voltage_idx):
                        try:
                            cap = float(row[capacity_idx])
                            vol = float(row[voltage_idx])
                            capacity.append(cap)
                            voltage.append(vol)
                            
                            if current_idx is not None and len(row) > current_idx:
                                current.append(float(row[current_idx]))
                            if phase_idx is not None and len(row) > phase_idx:
                                phase.append(row[phase_idx])
                            if time_idx is not None and len(row) > time_idx:
                                time.append(float(row[time_idx]))
                        except ValueError:
                            # Skip rows with non-numeric values
                            continue
                
                # Create a simple dictionary to mimic pandas DataFrame
                result = {
                    'Capacity (Ah)': np.array(capacity),
                    'Voltage (V)': np.array(voltage),
                    'columns': headers
                }
                
                has_current = current is not None
                has_phase = phase is not None
                has_time = time is not None
                
                if has_current:
                    result['Current (A)'] = np.array(current)
                if has_phase:
                    result['Phase'] = np.array(phase)
                if has_time:
                    result['Time (s)'] = np.array(time)
                
                return result, has_current, has_phase, has_time
        except Exception as e:
            print(f"エラー: ファイル {file_path} の読み込みに失敗しました: {e}")
            return None, False, False, False

def calculate_dqdv(capacity, voltage, smoothing_factor=0.01):
    """Calculate dQ/dV using spline interpolation for smoothing"""
    # Sort data by voltage (important for monotonic interpolation)
    idx = np.argsort(voltage)
    voltage_sorted = voltage[idx]
    capacity_sorted = capacity[idx]
    
    # Remove duplicates in voltage (required for interpolation)
    unique_idx = np.concatenate(([True], np.diff(voltage_sorted) > 0))
    voltage_unique = voltage_sorted[unique_idx]
    capacity_unique = capacity_sorted[unique_idx]
    
    if len(voltage_unique) < 4:  # Need at least 4 points for cubic spline
        print("警告: 十分なデータポイントがありません。")
        return None, None
    
    # Create a smoothed spline of capacity vs voltage
    spl = UnivariateSpline(voltage_unique, capacity_unique, s=smoothing_factor)
    
    # Create a fine voltage grid for evaluation
    v_fine = np.linspace(voltage_unique.min(), voltage_unique.max(), 1000)
    
    # Calculate dQ/dV as the derivative of the spline
    dqdv = spl.derivative()(v_fine)
    
    return v_fine, dqdv

def plot_dqdv_curves(file_paths, smoothing_factor=0.01, show_capacity=False, show_current=False):
    """Plot dQ/dV curves for the given files, optionally showing current profiles"""
    if show_capacity and show_current:
        # Three subplots: capacity vs voltage, dQ/dV, and current vs voltage
        fig, axs = plt.subplots(3, 1, figsize=(12, 15))
    elif show_capacity or show_current:
        # Two subplots: either capacity vs voltage and dQ/dV, or dQ/dV and current vs voltage
        fig, axs = plt.subplots(2, 1, figsize=(12, 10))
    else:
        # Single plot for dQ/dV
        plt.figure(figsize=(12, 6))
        axs = None
    
    dqdv_data = []
    
    for file_path in file_paths:
        # Extract cycle number and charge/discharge info from filename
        file_name = os.path.basename(file_path)
        cycle_info = file_name.split('_')
        cycle_type = "Unknown"
        cycle_num = "Unknown"
        
        for i, part in enumerate(cycle_info):
            if part.startswith("cycle"):
                cycle_num = part.replace("cycle", "")
                if i+1 < len(cycle_info):
                    if "charge" in cycle_info[i+1]:
                        cycle_type = "Charge"
                    elif "discharge" in cycle_info[i+1]:
                        cycle_type = "Discharge"
        
        # Load data
        data, has_current, has_phase, has_time = load_csv_file(file_path)
        if data is None:
            continue
        
        # Extract capacity and voltage data
        if PANDAS_AVAILABLE:
            capacity = data['Capacity (Ah)'].values
            voltage = data['Voltage (V)'].values
            current = data['Current (A)'].values if has_current else None
            phase = data['Phase'].values if has_phase else None
        else:
            capacity = data['Capacity (Ah)']
            voltage = data['Voltage (V)']
            current = data['Current (A)'] if has_current else None
            phase = data['Phase'] if has_phase else None
        
        # If show_capacity is True, plot capacity vs voltage
        if show_capacity:
            ax = axs[0]
            
            if has_phase:
                # Split data by phase
                cc_mask = (phase == 'CC')
                cv_mask = (phase == 'CV')
                
                if np.any(cc_mask):
                    ax.plot(voltage[cc_mask], capacity[cc_mask], 'b-', label=f"{cycle_type} {cycle_num} (CC)")
                if np.any(cv_mask):
                    ax.plot(voltage[cv_mask], capacity[cv_mask], 'r-', label=f"{cycle_type} {cycle_num} (CV)")
            else:
                ax.plot(voltage, capacity, label=f"{cycle_type} {cycle_num}")
        
        # Calculate dQ/dV
        v_fine, dqdv = calculate_dqdv(capacity, voltage, smoothing_factor)
        if v_fine is None or dqdv is None:
            continue
        
        # Store data for potential CSV export
        dqdv_data.append({
            'file': file_name,
            'cycle_type': cycle_type,
            'cycle_num': cycle_num,
            'voltage': v_fine,
            'dqdv': dqdv,
            'has_current': has_current,
            'has_phase': has_phase,
            'current': current,
            'phase': phase
        })
        
        # Plot dQ/dV
        if show_capacity and show_current:
            ax = axs[1]
        elif show_capacity:
            ax = axs[1]
        elif show_current:
            ax = axs[0]
        else:
            ax = plt
        
        # Plot dQ/dV curve
        if has_phase:
            # We can't directly split dQ/dV by phase since it's calculated on a new voltage grid
            # Instead, we'll mark the transition point on the plot
            
            # Find the voltage at which phase changes from CC to CV
            if np.any(phase == 'CC') and np.any(phase == 'CV'):
                cc_voltages = voltage[phase == 'CC']
                cv_voltages = voltage[phase == 'CV']
                transition_voltage = cv_voltages.min() if len(cv_voltages) > 0 else None
                
                if transition_voltage is not None:
                    # Plot dQ/dV curve with a vertical line at the transition
                    ax.plot(v_fine, dqdv, label=f"{cycle_type} {cycle_num}")
                    ax.axvline(x=transition_voltage, color='k', linestyle='--', 
                              label=f"CC-CV Transition ({transition_voltage:.3f}V)")
                else:
                    ax.plot(v_fine, dqdv, label=f"{cycle_type} {cycle_num}")
            else:
                ax.plot(v_fine, dqdv, label=f"{cycle_type} {cycle_num}")
        else:
            ax.plot(v_fine, dqdv, label=f"{cycle_type} {cycle_num}")
        
        # If show_current is True and current data is available, plot current vs voltage
        if show_current and has_current:
            if show_capacity and show_current:
                ax = axs[2]
            elif show_current:
                ax = axs[1]
            
            if has_phase:
                # Split data by phase
                cc_mask = (phase == 'CC')
                cv_mask = (phase == 'CV')
                
                if np.any(cc_mask):
                    ax.plot(voltage[cc_mask], current[cc_mask], 'b-', label=f"{cycle_type} {cycle_num} (CC)")
                if np.any(cv_mask):
                    ax.plot(voltage[cv_mask], current[cv_mask], 'r-', label=f"{cycle_type} {cycle_num} (CV)")
            else:
                ax.plot(voltage, current, label=f"{cycle_type} {cycle_num}")
    
    # Set labels and title for capacity vs voltage plot if shown
    if show_capacity:
        ax = axs[0]
        ax.set_xlabel('Voltage (V)')
        ax.set_ylabel('Capacity (Ah)')
        ax.set_title('Capacity vs Voltage')
        ax.grid(True)
        ax.legend()
    
    # Set labels and title for dQ/dV plot
    if show_capacity and show_current:
        ax = axs[1]
    elif show_capacity:
        ax = axs[1]
    elif show_current:
        ax = axs[0]
    else:
        ax = plt
    
    ax.set_xlabel('Voltage (V)')
    ax.set_ylabel('dQ/dV (Ah/V)')
    ax.set_title('dQ/dV vs Voltage')
    ax.grid(True)
    ax.legend()
    
    # Set labels and title for current vs voltage plot if shown
    if show_current:
        if show_capacity and show_current:
            ax = axs[2]
        elif show_current:
            ax = axs[1]
        
        ax.set_xlabel('Voltage (V)')
        ax.set_ylabel('Current (A)')
        ax.set_title('Current vs Voltage')
        ax.grid(True)
        ax.legend()
    
    plt.tight_layout()
    plt.show()
    
    return dqdv_data

def export_dqdv_to_csv(dqdv_data):
    """Export dQ/dV data to CSV files, including current and phase data if available"""
    if not dqdv_data:
        print("エクスポートするデータがありません。")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs('results', exist_ok=True)
    
    for data in dqdv_data:
        file_name = data['file']
        cycle_type = data['cycle_type']
        cycle_num = data['cycle_num']
        
        # Create output filename
        output_file = f"results/dqdv_{cycle_type}_{cycle_num}_{timestamp}.csv"
        
        # Check if current and phase data are available
        has_current = data.get('has_current', False)
        has_phase = data.get('has_phase', False)
        
        # Prepare headers based on available data
        headers = ['Voltage (V)', 'dQ/dV (Ah/V)']
        if has_current:
            headers.append('Current (A)')
        if has_phase:
            headers.append('Phase')
        
        # Write data to CSV
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            # For current and phase, we need to interpolate to the new voltage grid
            if has_current or has_phase:
                # Get original data
                voltage_orig = data['voltage']
                dqdv_orig = data['dqdv']
                
                if has_current:
                    # Interpolate current to the new voltage grid
                    current_orig = data['current']
                    voltage_current = np.array([v for v, c in zip(data['voltage'], current_orig) if not np.isnan(c)])
                    current_valid = np.array([c for v, c in zip(data['voltage'], current_orig) if not np.isnan(c)])
                    
                    if len(voltage_current) > 1:
                        current_interp = interp1d(voltage_current, current_valid, 
                                                 kind='linear', bounds_error=False, fill_value=np.nan)(voltage_orig)
                    else:
                        current_interp = np.full_like(voltage_orig, np.nan)
                
                if has_phase:
                    # For phase, we'll use the nearest phase value
                    phase_orig = data['phase']
                    phase_interp = np.full_like(voltage_orig, '', dtype=object)
                    
                    for i, v in enumerate(voltage_orig):
                        # Find the closest voltage in the original data
                        idx = np.abs(data['voltage'] - v).argmin()
                        if idx < len(phase_orig):
                            phase_interp[i] = phase_orig[idx]
                
                # Write data with interpolated values
                for i, (v, dq) in enumerate(zip(voltage_orig, dqdv_orig)):
                    row = [v, dq]
                    if has_current:
                        row.append(current_interp[i] if not np.isnan(current_interp[i]) else '')
                    if has_phase:
                        row.append(phase_interp[i])
                    writer.writerow(row)
            else:
                # Write data without current or phase
                for v, dq in zip(data['voltage'], data['dqdv']):
                    writer.writerow([v, dq])
        
        print(f"dQ/dVデータを保存しました: {output_file}")

def select_files_for_analysis():
    """Let the user select files for analysis"""
    # Find charge and discharge files
    charge_files = find_csv_files(pattern="*charge*.csv")
    discharge_files = find_csv_files(pattern="*discharge*.csv")
    
    if not charge_files and not discharge_files:
        print("解析するCSVファイルが見つかりません。")
        print("先にシミュレーションを実行してCSVファイルを生成してください。")
        return []
    
    print("\n利用可能なファイル:")
    all_files = charge_files + discharge_files
    for i, file in enumerate(all_files):
        print(f"{i+1}. {os.path.basename(file)}")
    
    # Ask user to select files
    selected_indices = input("\n解析するファイルの番号をカンマ区切りで入力してください (例: 1,3,5): ").strip()
    if not selected_indices:
        return []
    
    try:
        indices = [int(idx.strip()) - 1 for idx in selected_indices.split(',')]
        selected_files = [all_files[idx] for idx in indices if 0 <= idx < len(all_files)]
        return selected_files
    except Exception as e:
        print(f"ファイル選択エラー: {e}")
        return []

def main():
    """Main function for dQ/dV analysis"""
    print("=" * 60)
    print("リチウムイオン電池シミュレーション - dQ/dV解析モード (V3)")
    print("=" * 60)
    print("このプログラムでは、充放電曲線からdQ/dV曲線を計算して可視化します。")
    print("V3では、CV充電時の電流プロファイルも同時に表示できる機能が追加されています。")
    print("-" * 60)
    
    # Let user select files for analysis
    selected_files = select_files_for_analysis()
    if not selected_files:
        print("ファイルが選択されていないため、プログラムを終了します。")
        return
    
    # Get smoothing factor
    smoothing_factor = get_float_input("スムージング係数", 0.01, min_val=0.0)
    
    # Ask if user wants to see capacity vs voltage plot
    show_capacity = get_yes_no_input("容量-電圧曲線も表示しますか？", True)
    
    # Ask if user wants to see current vs voltage plot (V3 feature)
    show_current = get_yes_no_input("電流-電圧曲線も表示しますか？", True)
    
    # Calculate and plot dQ/dV curves
    dqdv_data = plot_dqdv_curves(selected_files, smoothing_factor, show_capacity, show_current)
    
    # Ask if user wants to export dQ/dV data to CSV
    if dqdv_data and get_yes_no_input("\ndQ/dVデータをCSVファイルに保存しますか？", True):
        export_dqdv_to_csv(dqdv_data)
    
    print("\n解析が完了しました。")

if __name__ == "__main__":
    main()