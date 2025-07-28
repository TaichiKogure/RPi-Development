import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, UnivariateSpline
import os
import csv
from datetime import datetime

# OCV-SOC table from literature
soc_pts = np.linspace(0, 1, 11)
ocv_pts = np.array([3.0519,3.6594,3.7167,3.7611,3.7915,3.8275,
                    3.8772,3.9401,4.0128,4.0923,4.1797])
ocv_interp = interp1d(soc_pts, ocv_pts, kind='linear', fill_value='extrapolate')

def ocv_from_soc(soc):
    return float(ocv_interp(np.clip(soc, 0.0, 1.0)))

def simulate_charge(cap_ah, c_rate, resistance, v_max=4.1797, end_current_ratio=0.05, dt=1.0):
    dt_h = dt / 3600.0
    I0 = c_rate * cap_ah
    soc = 0.0
    charged = 0.0
    soc_hist, cap_hist, v_hist = [soc], [0.0], [ocv_from_soc(soc)]
    I = I0
    # CC phase
    while soc < 1.0:
        V_oc = ocv_from_soc(soc)
        V_term = V_oc + I * resistance
        if V_term >= v_max: break
        soc += (I * dt_h) / cap_ah
        charged += I * dt_h
        soc_hist.append(soc); cap_hist.append(charged); v_hist.append(V_term)
    # CV phase
    while soc < 1.0:
        V_oc = ocv_from_soc(soc)
        I = max((v_max - V_oc) / resistance, 0.0)
        if I <= end_current_ratio * I0: break
        soc += (I * dt_h) / cap_ah
        charged += I * dt_h
        soc_hist.append(soc); cap_hist.append(charged); v_hist.append(V_oc + I * resistance)
    return np.array(soc_hist), np.array(cap_hist), np.array(v_hist)

def simulate_discharge(cap_ah, c_rate, resistance, v_min=3.0519, dt=1.0):
    dt_h = dt / 3600.0
    I = c_rate * cap_ah
    soc = 1.0
    discharged = 0.0
    soc_hist, cap_hist, v_hist = [soc], [0.0], [ocv_from_soc(soc)]
    while soc > 0.0:
        V_oc = ocv_from_soc(soc)
        V_term = V_oc - I * resistance
        if V_term <= v_min: break
        soc -= (I * dt_h) / cap_ah
        discharged += I * dt_h
        soc_hist.append(soc); cap_hist.append(discharged); v_hist.append(V_term)
    return np.array(soc_hist), np.array(cap_hist), np.array(v_hist)

# degradation models
def capacity_after_cycle(n, Q0=3.0, A=0.1, B=0.05):
    return Q0 * (1 - A * (1 - np.exp(-B * n)))

def resistance_after_cycle(n, R0=0.05, C=0.05, D=1.0):
    return R0 * (1 + C * (n**D))

def run_all_cycles(num_cycles=50, c_rate=0.5, Q0=3.0, A=0.1, B=0.05, R0=0.05, C=0.05, D=1.0, 
                  v_max=4.1797, v_min=3.0519, end_current_ratio=0.05, dt=1.0):
    results = []
    first_discharge_capacity = None
    
    for n in range(1, num_cycles+1):
        cap_n = capacity_after_cycle(n, Q0, A, B)
        res_n = resistance_after_cycle(n, R0, C, D)
        
        # Simulate charge and discharge
        soc_c, cap_c, v_c = simulate_charge(cap_n, c_rate, res_n, v_max, end_current_ratio, dt)
        soc_d, cap_d, v_d = simulate_discharge(cap_n, c_rate, res_n, v_min, dt)
        
        # Calculate discharged capacity (maximum value in cap_d)
        discharged_capacity = cap_d[-1] if len(cap_d) > 0 else 0
        
        # Store first cycle discharge capacity for retention calculation
        if n == 1:
            first_discharge_capacity = discharged_capacity
        
        # Calculate capacity retention as percentage of first cycle
        retention = 100.0 * discharged_capacity / first_discharge_capacity if first_discharge_capacity else 0
        
        results.append((n, cap_n, res_n, discharged_capacity, retention, soc_c, cap_c, v_c, soc_d, cap_d, v_d))
    
    return results

def plot_all_with_retention(results, smoothing_s=0.001):
    """Plot charge/discharge curves and capacity retention"""
    plt.figure(figsize=(15, 10))
    
    # Extract cycle numbers and retention values
    cycles = [r[0] for r in results]
    capacities = [r[3] for r in results]  # Discharged capacities
    retentions = [r[4] for r in results]  # Retention percentages
    
    # Charge curves (top left)
    plt.subplot(2, 2, 1)
    for n, _, _, _, _, _, cap_c, v_c, _, _, _ in results:
        spl = UnivariateSpline(cap_c, v_c, s=smoothing_s)
        xs = np.linspace(cap_c.min(), cap_c.max(), 400)
        plt.plot(xs, spl(xs), label=f'Ch {n}', lw=1)
    plt.xlabel('Capacity (Ah)')
    plt.ylabel('Voltage (V)')
    plt.title('Smoothed Charge Curves (all cycles)')
    plt.grid(True)

    # Discharge curves (top right)
    plt.subplot(2, 2, 2)
    for n, _, _, _, _, _, _, _, _, cap_d, v_d in results:
        spl = UnivariateSpline(cap_d, v_d, s=smoothing_s)
        xs = np.linspace(cap_d.min(), cap_d.max(), 400)
        plt.plot(xs, spl(xs), label=f'Dis {n}', lw=1)
    plt.xlabel('Discharged Capacity (Ah)')
    plt.ylabel('Voltage (V)')
    plt.title('Smoothed Discharge Curves (all cycles)')
    plt.grid(True)
    
    # Capacity vs Cycle (bottom left)
    plt.subplot(2, 2, 3)
    plt.plot(cycles, capacities, 'o-', color='blue')
    plt.xlabel('Cycle Number')
    plt.ylabel('Discharged Capacity (Ah)')
    plt.title('Discharged Capacity vs Cycle Number')
    plt.grid(True)
    
    # Retention vs Cycle (bottom right)
    plt.subplot(2, 2, 4)
    plt.plot(cycles, retentions, 'o-', color='red')
    plt.xlabel('Cycle Number')
    plt.ylabel('Capacity Retention (%)')
    plt.title('Capacity Retention vs Cycle Number')
    plt.ylim(0, 105)  # Set y-axis from 0 to 105%
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

def export_to_csv(results, filename_prefix):
    """Export simulation results to CSV files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create directory if it doesn't exist
    os.makedirs('results', exist_ok=True)
    
    # Export cycle summary with retention data
    summary_filename = f"results/{filename_prefix}_summary_{timestamp}.csv"
    with open(summary_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Cycle', 'Capacity (Ah)', 'Resistance (ohm)', 'Discharged Capacity (Ah)', 'Retention (%)'])
        for n, cap_n, res_n, discharged_cap, retention, _, _, _, _, _, _ in results:
            writer.writerow([n, cap_n, res_n, discharged_cap, retention])
    print(f"サイクル概要を保存しました: {summary_filename}")
    
    # Export detailed charge/discharge data for each cycle
    for n, _, _, _, _, soc_c, cap_c, v_c, soc_d, cap_d, v_d in results:
        # Charge data
        charge_filename = f"results/{filename_prefix}_cycle{n}_charge_{timestamp}.csv"
        with open(charge_filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['SOC', 'Capacity (Ah)', 'Voltage (V)'])
            for i in range(len(soc_c)):
                writer.writerow([soc_c[i], cap_c[i], v_c[i]])
        
        # Discharge data
        discharge_filename = f"results/{filename_prefix}_cycle{n}_discharge_{timestamp}.csv"
        with open(discharge_filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['SOC', 'Capacity (Ah)', 'Voltage (V)'])
            for i in range(len(soc_d)):
                writer.writerow([soc_d[i], cap_d[i], v_d[i]])
    
    # Export retention data separately
    retention_filename = f"results/{filename_prefix}_retention_{timestamp}.csv"
    with open(retention_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Cycle', 'Discharged Capacity (Ah)', 'Retention (%)'])
        for n, _, _, discharged_cap, retention, _, _, _, _, _, _ in results:
            writer.writerow([n, discharged_cap, retention])
    print(f"容量維持率データを保存しました: {retention_filename}")
    
    print(f"各サイクルの詳細データを保存しました (results/{filename_prefix}_cycle*_{timestamp}.csv)")

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

def interactive_mode():
    """Run the simulation in interactive mode with capacity retention"""
    print("=" * 60)
    print("リチウムイオン電池の劣化シミュレーション - 容量維持率表示モード")
    print("=" * 60)
    print("各パラメータの値を入力してください。デフォルト値を使用する場合は Enter キーを押してください。")
    print("-" * 60)
    
    # Get battery parameters
    print("\n【電池の基本パラメータ】")
    Q0 = get_float_input("初期容量 (Ah)", 3.0, min_val=0.1)
    R0 = get_float_input("初期内部抵抗 (Ω)", 0.05, min_val=0.001)
    v_max = get_float_input("最大充電電圧 (V)", 4.1797, min_val=3.5, max_val=4.5)
    v_min = get_float_input("最小放電電圧 (V)", 3.0519, min_val=2.0, max_val=3.5)
    
    # Get degradation parameters
    print("\n【劣化モデルのパラメータ】")
    A = get_float_input("容量劣化の最大割合 (0-1)", 0.1, min_val=0, max_val=1)
    B = get_float_input("容量劣化の速度係数", 0.05, min_val=0)
    C = get_float_input("抵抗増加の係数", 0.05, min_val=0)
    D = get_float_input("抵抗増加の指数", 1.0, min_val=0)
    
    # Get simulation parameters
    print("\n【シミュレーションのパラメータ】")
    num_cycles = get_int_input("シミュレーションするサイクル数", 20, min_val=1, max_val=1000)
    c_rate = get_float_input("充放電のC-レート", 0.5, min_val=0.05, max_val=10)
    end_current_ratio = get_float_input("CV充電終了の電流比率 (0-1)", 0.05, min_val=0.01, max_val=0.5)
    dt = get_float_input("シミュレーションの時間ステップ (秒)", 1.0, min_val=0.1)
    smoothing_s = get_float_input("グラフの平滑化係数", 0.05, min_val=0)
    
    # Run simulation
    print("\nシミュレーションを実行中...")
    results = run_all_cycles(
        num_cycles=num_cycles, 
        c_rate=c_rate, 
        Q0=Q0, 
        A=A, 
        B=B, 
        R0=R0, 
        C=C, 
        D=D, 
        v_max=v_max, 
        v_min=v_min, 
        end_current_ratio=end_current_ratio, 
        dt=dt
    )
    
    # Plot results with retention
    plot_all_with_retention(results, smoothing_s=smoothing_s)
    
    # Ask if user wants to export results to CSV
    if get_yes_no_input("\nシミュレーション結果をCSVファイルに保存しますか？"):
        filename_prefix = input("ファイル名のプレフィックスを入力してください [sim]: ").strip()
        if filename_prefix == "":
            filename_prefix = "sim"
        export_to_csv(results, filename_prefix)
    
    print("\nシミュレーションが完了しました。")

if __name__=='__main__':
    interactive_mode()