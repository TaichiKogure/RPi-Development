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

def get_parameter_range(param_name, default_min, default_max, default_points=5, min_val=None, max_val=None):
    """Get parameter range from user with validation"""
    print(f"\n{param_name}の範囲を指定してください:")
    min_value = get_float_input(f"  最小値", default_min, min_val=min_val)
    max_value = get_float_input(f"  最大値", default_max, min_val=min_value)
    num_points = get_int_input(f"  分割数", default_points, min_val=2)
    
    if num_points == 2:
        return [min_value, max_value]
    else:
        return np.linspace(min_value, max_value, num_points).tolist()

def export_to_csv(data, filename):
    """Export data to CSV file"""
    os.makedirs('results', exist_ok=True)
    with open(f"results/{filename}", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data['headers'])
        for row in data['rows']:
            writer.writerow(row)
    print(f"データを保存しました: results/{filename}")

def export_cycle_results(results, filename_prefix):
    """Export simulation results to CSV files with degradation rates"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create directory if it doesn't exist
    os.makedirs('results', exist_ok=True)
    
    # Export cycle summary with retention and degradation rate data
    summary_filename = f"results/{filename_prefix}_summary_{timestamp}.csv"
    with open(summary_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Cycle', 'Capacity (Ah)', 'Resistance (ohm)', 'Discharged Capacity (Ah)', 
                         'Retention (%)', 'Capacity Degradation Rate (%/cycle)', 
                         'Resistance Increase Rate (%/cycle)', 'Retention Degradation Rate (%/cycle)'])
        for n, cap_n, res_n, discharged_cap, retention, cap_deg_rate, res_inc_rate, ret_deg_rate, _, _, _, _, _, _ in results:
            writer.writerow([n, cap_n, res_n, discharged_cap, retention, cap_deg_rate, res_inc_rate, ret_deg_rate])
    print(f"サイクル概要を保存しました: {summary_filename}")
    
    # Export detailed charge/discharge data for each cycle
    for n, _, _, _, _, _, _, _, soc_c, cap_c, v_c, soc_d, cap_d, v_d in results:
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
        writer.writerow(['Cycle', 'Discharged Capacity (Ah)', 'Retention (%)', 
                         'Capacity Degradation Rate (%/cycle)', 'Resistance Increase Rate (%/cycle)', 
                         'Retention Degradation Rate (%/cycle)'])
        for n, _, _, discharged_cap, retention, cap_deg_rate, res_inc_rate, ret_deg_rate, _, _, _, _, _, _ in results:
            writer.writerow([n, discharged_cap, retention, cap_deg_rate, res_inc_rate, ret_deg_rate])
    print(f"容量維持率データを保存しました: {retention_filename}")
    
    # Export degradation rate data separately
    degradation_filename = f"results/{filename_prefix}_degradation_rates_{timestamp}.csv"
    with open(degradation_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Cycle', 'Capacity Degradation Rate (%/cycle)', 
                         'Resistance Increase Rate (%/cycle)', 'Retention Degradation Rate (%/cycle)'])
        for n, _, _, _, _, cap_deg_rate, res_inc_rate, ret_deg_rate, _, _, _, _, _, _ in results:
            writer.writerow([n, cap_deg_rate, res_inc_rate, ret_deg_rate])
    print(f"劣化率データを保存しました: {degradation_filename}")
    
    print(f"各サイクルの詳細データを保存しました (results/{filename_prefix}_cycle*_{timestamp}.csv)")

def run_all_cycles(num_cycles=50, c_rate=0.5, Q0=3.0, A=0.1, B=0.05, R0=0.05, C=0.05, D=1.0, 
                  v_max=4.1797, v_min=3.0519, end_current_ratio=0.05, dt=1.0):
    results = []
    first_discharge_capacity = None
    
    # Arrays to store degradation rates
    capacity_degradation_rates = []
    resistance_increase_rates = []
    retention_degradation_rates = []
    
    prev_cap = None
    prev_res = None
    prev_retention = None
    
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
            prev_cap = cap_n
            prev_res = res_n
            prev_retention = 100.0  # First cycle is 100% by definition
            
            # Add placeholder for first cycle (no degradation rate yet)
            capacity_degradation_rates.append(0.0)
            resistance_increase_rates.append(0.0)
            retention_degradation_rates.append(0.0)
        else:
            # Calculate capacity retention as percentage of first cycle
            retention = 100.0 * discharged_capacity / first_discharge_capacity if first_discharge_capacity else 0
            
            # Calculate degradation rates (per cycle)
            cap_degradation_rate = (prev_cap - cap_n) / prev_cap * 100.0 if prev_cap else 0.0
            res_increase_rate = (res_n - prev_res) / prev_res * 100.0 if prev_res else 0.0
            retention_degradation_rate = (prev_retention - retention) if prev_retention else 0.0
            
            capacity_degradation_rates.append(cap_degradation_rate)
            resistance_increase_rates.append(res_increase_rate)
            retention_degradation_rates.append(retention_degradation_rate)
            
            # Update previous values for next cycle
            prev_cap = cap_n
            prev_res = res_n
            prev_retention = retention
        
        # Calculate capacity retention as percentage of first cycle
        retention = 100.0 * discharged_capacity / first_discharge_capacity if first_discharge_capacity else 0
        
        results.append((n, cap_n, res_n, discharged_capacity, retention, 
                       capacity_degradation_rates[-1], resistance_increase_rates[-1], 
                       retention_degradation_rates[-1], soc_c, cap_c, v_c, soc_d, cap_d, v_d))
    
    return results

def plot_all_with_retention(results, smoothing_s=0.001):
    """Plot charge/discharge curves and capacity retention"""
    plt.figure(figsize=(15, 10))
    
    # Extract cycle numbers and retention values
    cycles = [r[0] for r in results]
    capacities = [r[3] for r in results]  # Discharged capacities
    retentions = [r[4] for r in results]  # Retention percentages
    cap_degradation_rates = [r[5] for r in results]  # Capacity degradation rates
    res_increase_rates = [r[6] for r in results]  # Resistance increase rates
    
    # Charge curves (top left)
    plt.subplot(2, 3, 1)
    for n, _, _, _, _, _, _, _, _, cap_c, v_c, _, _, _ in results:
        spl = UnivariateSpline(cap_c, v_c, s=smoothing_s)
        xs = np.linspace(cap_c.min(), cap_c.max(), 400)
        plt.plot(xs, spl(xs), label=f'Ch {n}', lw=1)
    plt.xlabel('Capacity (Ah)')
    plt.ylabel('Voltage (V)')
    plt.title('Smoothed Charge Curves (all cycles)')
    plt.grid(True)

    # Discharge curves (top middle)
    plt.subplot(2, 3, 2)
    for n, _, _, _, _, _, _, _, _, _, _, _, cap_d, v_d in results:
        spl = UnivariateSpline(cap_d, v_d, s=smoothing_s)
        xs = np.linspace(cap_d.min(), cap_d.max(), 400)
        plt.plot(xs, spl(xs), label=f'Dis {n}', lw=1)
    plt.xlabel('Discharged Capacity (Ah)')
    plt.ylabel('Voltage (V)')
    plt.title('Smoothed Discharge Curves (all cycles)')
    plt.grid(True)
    
    # Capacity vs Cycle (top right)
    plt.subplot(2, 3, 3)
    plt.plot(cycles, capacities, 'o-', color='blue')
    plt.xlabel('Cycle Number')
    plt.ylabel('Discharged Capacity (Ah)')
    plt.title('Discharged Capacity vs Cycle Number')
    plt.grid(True)
    
    # Retention vs Cycle (bottom left)
    plt.subplot(2, 3, 4)
    plt.plot(cycles, retentions, 'o-', color='red')
    plt.xlabel('Cycle Number')
    plt.ylabel('Capacity Retention (%)')
    plt.title('Capacity Retention vs Cycle Number')
    plt.ylim(0, 105)  # Set y-axis from 0 to 105%
    plt.grid(True)
    
    # Capacity degradation rate vs Cycle (bottom middle)
    plt.subplot(2, 3, 5)
    plt.plot(cycles[1:], cap_degradation_rates[1:], 'o-', color='purple')
    plt.xlabel('Cycle Number')
    plt.ylabel('Capacity Degradation Rate (%/cycle)')
    plt.title('Capacity Degradation Rate vs Cycle Number')
    plt.grid(True)
    
    # Resistance increase rate vs Cycle (bottom right)
    plt.subplot(2, 3, 6)
    plt.plot(cycles[1:], res_increase_rates[1:], 'o-', color='green')
    plt.xlabel('Cycle Number')
    plt.ylabel('Resistance Increase Rate (%/cycle)')
    plt.title('Resistance Increase Rate vs Cycle Number')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

def test_capacity_degradation():
    """Test the effect of capacity degradation parameters with custom ranges"""
    print("\n=== 容量劣化パラメータのテスト ===")
    
    # Get base parameters
    Q0 = get_float_input("初期容量 (Ah)", 3.0, min_val=0.1)
    num_cycles = get_int_input("シミュレーションするサイクル数", 50, min_val=10, max_val=1000)
    
    # Get custom parameter ranges
    use_custom_range = get_yes_no_input("パラメータの範囲をカスタマイズしますか？", True)
    
    if use_custom_range:
        # Test different A values (maximum degradation ratio)
        A_values = get_parameter_range("Aパラメータ（最大劣化率）", 0.05, 0.5, 5, min_val=0.0, max_val=1.0)
    else:
        # Default values
        A_values = [0.05, 0.1, 0.2, 0.3, 0.5]
    
    print(f"\nAパラメータ（最大劣化率）のテスト: {A_values}")
    
    plt.figure(figsize=(10, 6))
    
    cycles = np.arange(1, num_cycles+1)
    data = {
        'headers': ['Cycle'] + [f'A={a}' for a in A_values],
        'rows': []
    }
    
    for i, cycle in enumerate(cycles):
        row = [cycle]
        for A in A_values:
            cap = capacity_after_cycle(cycle, Q0=Q0, A=A, B=0.05)
            row.append(cap)
        data['rows'].append(row)
        
    for A in A_values:
        capacities = [capacity_after_cycle(n, Q0=Q0, A=A, B=0.05) for n in cycles]
        plt.plot(cycles, capacities, label=f'A={A}')
    
    plt.xlabel('サイクル数')
    plt.ylabel('容量 (Ah)')
    plt.title('Aパラメータ（最大劣化率）の影響')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    
    if use_custom_range:
        # Test different B values (degradation speed)
        B_values = get_parameter_range("Bパラメータ（劣化速度係数）", 0.01, 0.5, 5, min_val=0.0)
    else:
        # Default values
        B_values = [0.01, 0.05, 0.1, 0.2, 0.5]
    
    print(f"\nBパラメータ（劣化速度係数）のテスト: {B_values}")
    
    plt.figure(figsize=(10, 6))
    
    data2 = {
        'headers': ['Cycle'] + [f'B={b}' for b in B_values],
        'rows': []
    }
    
    for i, cycle in enumerate(cycles):
        row = [cycle]
        for B in B_values:
            cap = capacity_after_cycle(cycle, Q0=Q0, A=0.1, B=B)
            row.append(cap)
        data2['rows'].append(row)
        
    for B in B_values:
        capacities = [capacity_after_cycle(n, Q0=Q0, A=0.1, B=B) for n in cycles]
        plt.plot(cycles, capacities, label=f'B={B}')
    
    plt.xlabel('サイクル数')
    plt.ylabel('容量 (Ah)')
    plt.title('Bパラメータ（劣化速度係数）の影響')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    
    # Ask if user wants to export results
    if get_yes_no_input("\nテスト結果をCSVファイルに保存しますか？"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_to_csv(data, f"capacity_A_test_{timestamp}.csv")
        export_to_csv(data2, f"capacity_B_test_{timestamp}.csv")

def test_resistance_degradation():
    """Test the effect of resistance degradation parameters with custom ranges"""
    print("\n=== 抵抗増加パラメータのテスト ===")
    
    # Get base parameters
    R0 = get_float_input("初期内部抵抗 (Ω)", 0.05, min_val=0.001)
    num_cycles = get_int_input("シミュレーションするサイクル数", 50, min_val=10, max_val=1000)
    
    # Get custom parameter ranges
    use_custom_range = get_yes_no_input("パラメータの範囲をカスタマイズしますか？", True)
    
    if use_custom_range:
        # Test different C values (resistance increase coefficient)
        C_values = get_parameter_range("Cパラメータ（抵抗増加係数）", 0.01, 0.5, 5, min_val=0.0)
    else:
        # Default values
        C_values = [0.01, 0.05, 0.1, 0.2, 0.5]
    
    print(f"\nCパラメータ（抵抗増加係数）のテスト: {C_values}")
    
    plt.figure(figsize=(10, 6))
    
    cycles = np.arange(1, num_cycles+1)
    data = {
        'headers': ['Cycle'] + [f'C={c}' for c in C_values],
        'rows': []
    }
    
    for i, cycle in enumerate(cycles):
        row = [cycle]
        for C in C_values:
            res = resistance_after_cycle(cycle, R0=R0, C=C, D=1.0)
            row.append(res)
        data['rows'].append(row)
        
    for C in C_values:
        resistances = [resistance_after_cycle(n, R0=R0, C=C, D=1.0) for n in cycles]
        plt.plot(cycles, resistances, label=f'C={C}')
    
    plt.xlabel('サイクル数')
    plt.ylabel('内部抵抗 (Ω)')
    plt.title('Cパラメータ（抵抗増加係数）の影響')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    
    if use_custom_range:
        # Test different D values (resistance increase exponent)
        D_values = get_parameter_range("Dパラメータ（抵抗増加の指数）", 0.5, 1.5, 5, min_val=0.0)
    else:
        # Default values
        D_values = [0.5, 0.75, 1.0, 1.25, 1.5]
    
    print(f"\nDパラメータ（抵抗増加の指数）のテスト: {D_values}")
    
    plt.figure(figsize=(10, 6))
    
    data2 = {
        'headers': ['Cycle'] + [f'D={d}' for d in D_values],
        'rows': []
    }
    
    for i, cycle in enumerate(cycles):
        row = [cycle]
        for D in D_values:
            res = resistance_after_cycle(cycle, R0=R0, C=0.05, D=D)
            row.append(res)
        data2['rows'].append(row)
        
    for D in D_values:
        resistances = [resistance_after_cycle(n, R0=R0, C=0.05, D=D) for n in cycles]
        plt.plot(cycles, resistances, label=f'D={D}')
    
    plt.xlabel('サイクル数')
    plt.ylabel('内部抵抗 (Ω)')
    plt.title('Dパラメータ（抵抗増加の指数）の影響')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    
    # Ask if user wants to export results
    if get_yes_no_input("\nテスト結果をCSVファイルに保存しますか？"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_to_csv(data, f"resistance_C_test_{timestamp}.csv")
        export_to_csv(data2, f"resistance_D_test_{timestamp}.csv")

def test_charge_discharge_curves():
    """Test the effect of parameters on charge/discharge curves with custom ranges"""
    print("\n=== 充放電曲線パラメータのテスト ===")
    
    # Get base parameters
    cap_ah = get_float_input("電池容量 (Ah)", 3.0, min_val=0.1)
    resistance = get_float_input("内部抵抗 (Ω)", 0.05, min_val=0.001)
    
    # Get custom parameter ranges
    use_custom_range = get_yes_no_input("パラメータの範囲をカスタマイズしますか？", True)
    
    if use_custom_range:
        # Test different C-rates
        c_rates = get_parameter_range("C-レート", 0.2, 5.0, 5, min_val=0.05)
    else:
        # Default values
        c_rates = [0.2, 0.5, 1.0, 2.0, 5.0]
    
    print(f"\nC-レートのテスト: {c_rates}")
    
    plt.figure(figsize=(12, 5))
    
    # Charge curves
    plt.subplot(1, 2, 1)
    
    charge_data = {
        'headers': ['Capacity (Ah)'] + [f'C-rate={c}' for c in c_rates],
        'rows': []
    }
    
    max_points = 0
    all_cap_c = []
    all_v_c = []
    
    for c_rate in c_rates:
        _, cap_c, v_c = simulate_charge(cap_ah, c_rate, resistance)
        all_cap_c.append(cap_c)
        all_v_c.append(v_c)
        max_points = max(max_points, len(cap_c))
        
        spl = UnivariateSpline(cap_c, v_c, s=0.001)
        xs = np.linspace(cap_c.min(), cap_c.max(), 400)
        plt.plot(xs, spl(xs), label=f'C-rate={c_rate}')
    
    # Prepare data for CSV export
    for i in range(max_points):
        row = []
        for j, cap_c in enumerate(all_cap_c):
            if i < len(cap_c):
                if j == 0:  # Only add capacity once
                    row.append(cap_c[i])
                row.append(all_v_c[j][i])
            else:
                if j == 0:
                    row.append("")
                row.append("")
        charge_data['rows'].append(row)
    
    plt.xlabel('容量 (Ah)')
    plt.ylabel('電圧 (V)')
    plt.title('C-レートが充電曲線に与える影響')
    plt.legend()
    plt.grid(True)
    
    # Discharge curves
    plt.subplot(1, 2, 2)
    
    discharge_data = {
        'headers': ['Capacity (Ah)'] + [f'C-rate={c}' for c in c_rates],
        'rows': []
    }
    
    max_points = 0
    all_cap_d = []
    all_v_d = []
    
    for c_rate in c_rates:
        _, cap_d, v_d = simulate_discharge(cap_ah, c_rate, resistance)
        all_cap_d.append(cap_d)
        all_v_d.append(v_d)
        max_points = max(max_points, len(cap_d))
        
        spl = UnivariateSpline(cap_d, v_d, s=0.001)
        xs = np.linspace(cap_d.min(), cap_d.max(), 400)
        plt.plot(xs, spl(xs), label=f'C-rate={c_rate}')
    
    # Prepare data for CSV export
    for i in range(max_points):
        row = []
        for j, cap_d in enumerate(all_cap_d):
            if i < len(cap_d):
                if j == 0:  # Only add capacity once
                    row.append(cap_d[i])
                row.append(all_v_d[j][i])
            else:
                if j == 0:
                    row.append("")
                row.append("")
        discharge_data['rows'].append(row)
    
    plt.xlabel('放電容量 (Ah)')
    plt.ylabel('電圧 (V)')
    plt.title('C-レートが放電曲線に与える影響')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    if use_custom_range:
        # Test different resistance values
        resistances = get_parameter_range("内部抵抗 (Ω)", 0.01, 0.5, 5, min_val=0.001)
    else:
        # Default values
        resistances = [0.01, 0.05, 0.1, 0.2, 0.5]
    
    print(f"\n内部抵抗のテスト: {resistances}")
    
    plt.figure(figsize=(12, 5))
    
    # Charge curves
    plt.subplot(1, 2, 1)
    
    charge_data2 = {
        'headers': ['Capacity (Ah)'] + [f'R={r}' for r in resistances],
        'rows': []
    }
    
    max_points = 0
    all_cap_c = []
    all_v_c = []
    
    for r in resistances:
        _, cap_c, v_c = simulate_charge(cap_ah, 0.5, r)
        all_cap_c.append(cap_c)
        all_v_c.append(v_c)
        max_points = max(max_points, len(cap_c))
        
        spl = UnivariateSpline(cap_c, v_c, s=0.001)
        xs = np.linspace(cap_c.min(), cap_c.max(), 400)
        plt.plot(xs, spl(xs), label=f'R={r}')
    
    # Prepare data for CSV export
    for i in range(max_points):
        row = []
        for j, cap_c in enumerate(all_cap_c):
            if i < len(cap_c):
                if j == 0:  # Only add capacity once
                    row.append(cap_c[i])
                row.append(all_v_c[j][i])
            else:
                if j == 0:
                    row.append("")
                row.append("")
        charge_data2['rows'].append(row)
    
    plt.xlabel('容量 (Ah)')
    plt.ylabel('電圧 (V)')
    plt.title('内部抵抗が充電曲線に与える影響')
    plt.legend()
    plt.grid(True)
    
    # Discharge curves
    plt.subplot(1, 2, 2)
    
    discharge_data2 = {
        'headers': ['Capacity (Ah)'] + [f'R={r}' for r in resistances],
        'rows': []
    }
    
    max_points = 0
    all_cap_d = []
    all_v_d = []
    
    for r in resistances:
        _, cap_d, v_d = simulate_discharge(cap_ah, 0.5, r)
        all_cap_d.append(cap_d)
        all_v_d.append(v_d)
        max_points = max(max_points, len(cap_d))
        
        spl = UnivariateSpline(cap_d, v_d, s=0.001)
        xs = np.linspace(cap_d.min(), cap_d.max(), 400)
        plt.plot(xs, spl(xs), label=f'R={r}')
    
    # Prepare data for CSV export
    for i in range(max_points):
        row = []
        for j, cap_d in enumerate(all_cap_d):
            if i < len(cap_d):
                if j == 0:  # Only add capacity once
                    row.append(cap_d[i])
                row.append(all_v_d[j][i])
            else:
                if j == 0:
                    row.append("")
                row.append("")
        discharge_data2['rows'].append(row)
    
    plt.xlabel('放電容量 (Ah)')
    plt.ylabel('電圧 (V)')
    plt.title('内部抵抗が放電曲線に与える影響')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    # Ask if user wants to export results
    if get_yes_no_input("\nテスト結果をCSVファイルに保存しますか？"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_to_csv(charge_data, f"charge_crate_test_{timestamp}.csv")
        export_to_csv(discharge_data, f"discharge_crate_test_{timestamp}.csv")
        export_to_csv(charge_data2, f"charge_resistance_test_{timestamp}.csv")
        export_to_csv(discharge_data2, f"discharge_resistance_test_{timestamp}.csv")

def run_cycle_simulation():
    """Run the simulation in interactive mode with capacity retention and degradation rates"""
    print("\n=== サイクルシミュレーション ===")
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
    
    # Plot results with retention and degradation rates
    plot_all_with_retention(results, smoothing_s=smoothing_s)
    
    # Ask if user wants to export results to CSV
    if get_yes_no_input("\nシミュレーション結果をCSVファイルに保存しますか？"):
        filename_prefix = input("ファイル名のプレフィックスを入力してください [sim]: ").strip()
        if filename_prefix == "":
            filename_prefix = "sim"
        export_cycle_results(results, filename_prefix)
    
    print("\nシミュレーションが完了しました。")

def main():
    """Main function to run the unified interface"""
    print("=" * 60)
    print("リチウムイオン電池シミュレーション - 統合モード")
    print("=" * 60)
    print("このプログラムでは、パラメータテストと容量維持率シミュレーションの両方を実行できます。")
    print("パラメータの範囲を任意で指定でき、劣化率データもCSV出力できます。")
    print("-" * 60)
    
    while True:
        print("\n以下のモードから選択してください:")
        print("1. パラメータテストモード")
        print("2. サイクルシミュレーションモード")
        print("0. 終了")
        
        choice = get_int_input("\n選択してください", 0, min_val=0, max_val=2)
        
        if choice == 0:
            break
        elif choice == 1:
            # Parameter test mode
            while True:
                print("\n以下のテストから選択してください:")
                print("1. 容量劣化パラメータ (A, B) のテスト")
                print("2. 抵抗増加パラメータ (C, D) のテスト")
                print("3. 充放電曲線パラメータ (C-レート, 内部抵抗) のテスト")
                print("0. 前のメニューに戻る")
                
                test_choice = get_int_input("\n選択してください", 0, min_val=0, max_val=3)
                
                if test_choice == 0:
                    break
                elif test_choice == 1:
                    test_capacity_degradation()
                elif test_choice == 2:
                    test_resistance_degradation()
                elif test_choice == 3:
                    test_charge_discharge_curves()
        elif choice == 2:
            # Cycle simulation mode
            run_cycle_simulation()
    
    print("\nプログラムを終了します。")

if __name__ == "__main__":
    main()