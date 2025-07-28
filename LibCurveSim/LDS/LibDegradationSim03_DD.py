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
    """Load data from a CSV file"""
    if PANDAS_AVAILABLE:
        try:
            df = pd.read_csv(file_path)
            # Check if the required columns exist
            if 'Capacity (Ah)' in df.columns and 'Voltage (V)' in df.columns:
                return df
            elif 'SOC' in df.columns and 'Capacity (Ah)' in df.columns and 'Voltage (V)' in df.columns:
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
                capacity_idx = None
                voltage_idx = None
                
                for i, header in enumerate(headers):
                    if header == 'Capacity (Ah)':
                        capacity_idx = i
                    elif header == 'Voltage (V)':
                        voltage_idx = i
                
                if capacity_idx is None or voltage_idx is None:
                    print(f"警告: ファイル {file_path} に必要な列がありません。")
                    return None
                
                # Read data
                capacity = []
                voltage = []
                
                for row in reader:
                    if len(row) > max(capacity_idx, voltage_idx):
                        try:
                            cap = float(row[capacity_idx])
                            vol = float(row[voltage_idx])
                            capacity.append(cap)
                            voltage.append(vol)
                        except ValueError:
                            # Skip rows with non-numeric values
                            continue
                
                # Create a simple dictionary to mimic pandas DataFrame
                return {
                    'Capacity (Ah)': np.array(capacity),
                    'Voltage (V)': np.array(voltage),
                    'columns': headers
                }
        except Exception as e:
            print(f"エラー: ファイル {file_path} の読み込みに失敗しました: {e}")
            return None

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

def plot_dqdv_curves(file_paths, smoothing_factor=0.01, show_capacity=False):
    """Plot dQ/dV curves for the given files"""
    plt.figure(figsize=(12, 8))
    
    # If show_capacity is True, create a subplot for capacity vs voltage
    if show_capacity:
        plt.subplot(2, 1, 1)
    
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
        df = load_csv_file(file_path)
        if df is None:
            continue
        
        # Extract capacity and voltage data
        capacity = df['Capacity (Ah)'].values
        voltage = df['Voltage (V)'].values
        
        # If show_capacity is True, plot capacity vs voltage
        if show_capacity:
            plt.plot(voltage, capacity, label=f"{cycle_type} {cycle_num}")
        
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
            'dqdv': dqdv
        })
        
        # If show_capacity is True, use the second subplot for dQ/dV
        if show_capacity:
            plt.subplot(2, 1, 2)
        
        # Plot dQ/dV
        plt.plot(v_fine, dqdv, label=f"{cycle_type} {cycle_num}")
    
    # Set labels and title for capacity vs voltage plot if shown
    if show_capacity:
        plt.subplot(2, 1, 1)
        plt.xlabel('Voltage (V)')
        plt.ylabel('Capacity (Ah)')
        plt.title('Capacity vs Voltage')
        plt.grid(True)
        plt.legend()
        
        plt.subplot(2, 1, 2)
    
    # Set labels and title for dQ/dV plot
    plt.xlabel('Voltage (V)')
    plt.ylabel('dQ/dV (Ah/V)')
    plt.title('dQ/dV vs Voltage')
    plt.grid(True)
    plt.legend()
    
    plt.tight_layout()
    plt.show()
    
    return dqdv_data

def export_dqdv_to_csv(dqdv_data):
    """Export dQ/dV data to CSV files"""
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
        
        # Write data to CSV
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Voltage (V)', 'dQ/dV (Ah/V)'])
            for v, dqdv in zip(data['voltage'], data['dqdv']):
                writer.writerow([v, dqdv])
        
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
    print("リチウムイオン電池シミュレーション - dQ/dV解析モード")
    print("=" * 60)
    print("このプログラムでは、充放電曲線からdQ/dV曲線を計算して可視化します。")
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
    
    # Calculate and plot dQ/dV curves
    dqdv_data = plot_dqdv_curves(selected_files, smoothing_factor, show_capacity)
    
    # Ask if user wants to export dQ/dV data to CSV
    if dqdv_data and get_yes_no_input("\ndQ/dVデータをCSVファイルに保存しますか？", True):
        export_dqdv_to_csv(dqdv_data)
    
    print("\n解析が完了しました。")

if __name__ == "__main__":
    main()