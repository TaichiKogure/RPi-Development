import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, UnivariateSpline
import os
import csv
from datetime import datetime

# Note: This program can use pandas for easier data handling if available
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# OCV-SOC table from literature
soc_pts = np.linspace(0, 1, 11)
ocv_pts = np.array([3.0519,3.6594,3.7167,3.7611,3.7915,3.8275,
                    3.8772,3.9401,4.0128,4.0923,4.1797])
ocv_interp = interp1d(soc_pts, ocv_pts, kind='linear', fill_value='extrapolate')

def ocv_from_soc(soc):
    """Get OCV from SOC using interpolation"""
    return float(ocv_interp(np.clip(soc, 0.0, 1.0)))

def simulate_charge(cap_ah, c_rate, resistance, v_max=4.1797, end_current_ratio=0.05, dt=1.0):
    """
    Simulate battery charging with CC-CV protocol, tracking current during CV phase
    
    Returns:
    - soc_hist: SOC history
    - cap_hist: Capacity history
    - v_hist: Voltage history
    - i_hist: Current history
    - t_hist: Time history
    - phase_hist: Phase history ('CC' or 'CV')
    - cv_start_time: Time when CV phase starts
    - cv_start_cap: Capacity when CV phase starts
    - cv_start_soc: SOC when CV phase starts
    """
    dt_h = dt / 3600.0
    I0 = c_rate * cap_ah
    soc = 0.0
    charged = 0.0
    time = 0.0
    
    soc_hist, cap_hist, v_hist = [soc], [0.0], [ocv_from_soc(soc)]
    i_hist, t_hist, phase_hist = [I0], [0.0], ['CC']
    
    I = I0
    
    # CC phase
    while soc < 1.0:
        V_oc = ocv_from_soc(soc)
        V_term = V_oc + I * resistance
        if V_term >= v_max:
            break
        
        soc += (I * dt_h) / cap_ah
        charged += I * dt_h
        time += dt
        
        soc_hist.append(soc)
        cap_hist.append(charged)
        v_hist.append(V_term)
        i_hist.append(I)
        t_hist.append(time)
        phase_hist.append('CC')
    
    # Record CV phase start
    cv_start_time = time
    cv_start_cap = charged
    cv_start_soc = soc
    
    # CV phase
    while soc < 1.0:
        V_oc = ocv_from_soc(soc)
        I = max((v_max - V_oc) / resistance, 0.0)
        if I <= end_current_ratio * I0:
            break
        
        soc += (I * dt_h) / cap_ah
        charged += I * dt_h
        time += dt
        
        soc_hist.append(soc)
        cap_hist.append(charged)
        v_hist.append(v_max)
        i_hist.append(I)
        t_hist.append(time)
        phase_hist.append('CV')
    
    return (np.array(soc_hist), np.array(cap_hist), np.array(v_hist), 
            np.array(i_hist), np.array(t_hist), np.array(phase_hist),
            cv_start_time, cv_start_cap, cv_start_soc)

def simulate_discharge(cap_ah, c_rate, resistance, v_min=3.0519, dt=1.0):
    """
    Simulate battery discharging
    
    Returns:
    - soc_hist: SOC history
    - cap_hist: Capacity history
    - v_hist: Voltage history
    - i_hist: Current history
    """
    dt_h = dt / 3600.0
    I = c_rate * cap_ah
    soc = 1.0
    discharged = 0.0
    
    soc_hist, cap_hist, v_hist = [soc], [0.0], [ocv_from_soc(soc)]
    i_hist = [I]
    
    while soc > 0.0:
        V_oc = ocv_from_soc(soc)
        V_term = V_oc - I * resistance
        if V_term <= v_min:
            break
        
        soc -= (I * dt_h) / cap_ah
        discharged += I * dt_h
        
        soc_hist.append(soc)
        cap_hist.append(discharged)
        v_hist.append(V_term)
        i_hist.append(I)
    
    return np.array(soc_hist), np.array(cap_hist), np.array(v_hist), np.array(i_hist)

# Degradation models
def capacity_after_cycle(n, Q0=3.0, A=0.1, B=0.05):
    """Calculate capacity after n cycles"""
    return Q0 * (1 - A * (1 - np.exp(-B * n)))

def resistance_after_cycle(n, R0=0.05, C=0.05, D=1.0):
    """Calculate resistance after n cycles"""
    return R0 * (1 + C * (n**D))

def get_float_input(prompt, default=None, min_val=None, max_val=None):
    """Get float input from user with validation"""
    default_str = f" [{default}]" if default is not None else ""
    while True:
        try:
            value_str = input(f"{prompt}{default_str}: ").strip()
            if not value_str and default is not None:
                return default
            value = float(value_str)
            if min_val is not None and value < min_val:
                print(f"値は {min_val} 以上である必要があります。")
                continue
            if max_val is not None and value > max_val:
                print(f"値は {max_val} 以下である必要があります。")
                continue
            return value
        except ValueError:
            print("有効な数値を入力してください。")

def get_int_input(prompt, default=None, min_val=None, max_val=None):
    """Get integer input from user with validation"""
    default_str = f" [{default}]" if default is not None else ""
    while True:
        try:
            value_str = input(f"{prompt}{default_str}: ").strip()
            if not value_str and default is not None:
                return default
            value = int(value_str)
            if min_val is not None and value < min_val:
                print(f"値は {min_val} 以上である必要があります。")
                continue
            if max_val is not None and value > max_val:
                print(f"値は {max_val} 以下である必要があります。")
                continue
            return value
        except ValueError:
            print("有効な整数を入力してください。")

def get_parameter_range(param_name, default_min, default_max, default_count, min_val=None, max_val=None):
    """Get parameter range from user"""
    print(f"\n{param_name}の範囲を指定してください:")
    min_value = get_float_input(f"最小値", default_min, min_val=min_val)
    max_value = get_float_input(f"最大値", default_max, min_val=min_value, max_val=max_val)
    count = get_int_input(f"分割数", default_count, min_val=2)
    
    return np.linspace(min_value, max_value, count).tolist()

def get_yes_no_input(prompt, default=None):
    """Get yes/no input from user"""
    default_str = ""
    if default is not None:
        default_str = " [y]" if default else " [n]"
    
    while True:
        response = input(f"{prompt}{default_str}: ").strip().lower()
        if not response and default is not None:
            return default
        if response in ['y', 'yes', 'はい']:
            return True
        if response in ['n', 'no', 'いいえ']:
            return False
        print("'y' または 'n' で回答してください。")

def ensure_directory(directory):
    """Ensure directory exists"""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def export_to_csv(data, filename, directory="results"):
    """Export data to CSV file"""
    ensure_directory(directory)
    filepath = os.path.join(directory, filename)
    
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data['headers'])
        for row in data['rows']:
            writer.writerow(row)
    
    print(f"データを {filepath} に保存しました。")
    return filepath

def test_capacity_degradation():
    """Test the effect of capacity degradation parameters with custom ranges"""
    print("\n=== 容量劣化パラメータのテスト ===")
    
    # Get base parameters
    Q0 = get_float_input("初期容量 (Ah)", 3.0, min_val=0.1)
    
    # Get custom parameter ranges
    use_custom_range = get_yes_no_input("パラメータの範囲をカスタマイズしますか？", True)
    
    if use_custom_range:
        # Test different A values
        A_values = get_parameter_range("パラメータA", 0.05, 0.5, 5, min_val=0.01, max_val=1.0)
        
        # Test different B values
        B_values = get_parameter_range("パラメータB", 0.01, 0.2, 5, min_val=0.001, max_val=1.0)
    else:
        # Default values
        A_values = [0.05, 0.1, 0.2, 0.3, 0.5]
        B_values = [0.01, 0.05, 0.1, 0.15, 0.2]
    
    print(f"\nパラメータAのテスト: {A_values}")
    
    plt.figure(figsize=(12, 5))
    
    # Test A parameter
    plt.subplot(1, 2, 1)
    
    data = {
        'headers': ['Cycle'] + [f'A={a}' for a in A_values],
        'rows': []
    }
    
    cycles = np.arange(1, 101)
    
    for cycle in cycles:
        row = [cycle]
        for A in A_values:
            capacity = capacity_after_cycle(cycle, Q0=Q0, A=A, B=0.05)
            row.append(capacity)
        data['rows'].append(row)
    
    for A in A_values:
        capacities = [capacity_after_cycle(n, Q0=Q0, A=A, B=0.05) for n in cycles]
        plt.plot(cycles, capacities, label=f'A={A}')
    
    plt.xlabel('サイクル数')
    plt.ylabel('容量 (Ah)')
    plt.title('パラメータAが容量劣化に与える影響')
    plt.legend()
    plt.grid(True)
    
    # Test B parameter
    plt.subplot(1, 2, 2)
    
    data2 = {
        'headers': ['Cycle'] + [f'B={b}' for b in B_values],
        'rows': []
    }
    
    for cycle in cycles:
        row = [cycle]
        for B in B_values:
            capacity = capacity_after_cycle(cycle, Q0=Q0, A=0.1, B=B)
            row.append(capacity)
        data2['rows'].append(row)
    
    for B in B_values:
        capacities = [capacity_after_cycle(n, Q0=Q0, A=0.1, B=B) for n in cycles]
        plt.plot(cycles, capacities, label=f'B={B}')
    
    plt.xlabel('サイクル数')
    plt.ylabel('容量 (Ah)')
    plt.title('パラメータBが容量劣化に与える影響')
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
    R0 = get_float_input("初期抵抗 (Ω)", 0.05, min_val=0.001)
    
    # Get custom parameter ranges
    use_custom_range = get_yes_no_input("パラメータの範囲をカスタマイズしますか？", True)
    
    if use_custom_range:
        # Test different C values
        C_values = get_parameter_range("パラメータC", 0.01, 0.2, 5, min_val=0.001, max_val=1.0)
        
        # Test different D values
        D_values = get_parameter_range("パラメータD", 0.5, 2.0, 5, min_val=0.1, max_val=5.0)
    else:
        # Default values
        C_values = [0.01, 0.05, 0.1, 0.15, 0.2]
        D_values = [0.5, 0.75, 1.0, 1.5, 2.0]
    
    print(f"\nパラメータCのテスト: {C_values}")
    
    plt.figure(figsize=(12, 5))
    
    # Test C parameter
    plt.subplot(1, 2, 1)
    
    data = {
        'headers': ['Cycle'] + [f'C={c}' for c in C_values],
        'rows': []
    }
    
    cycles = np.arange(1, 101)
    
    for cycle in cycles:
        row = [cycle]
        for C in C_values:
            resistance = resistance_after_cycle(cycle, R0=R0, C=C, D=1.0)
            row.append(resistance)
        data['rows'].append(row)
    
    for C in C_values:
        resistances = [resistance_after_cycle(n, R0=R0, C=C, D=1.0) for n in cycles]
        plt.plot(cycles, resistances, label=f'C={C}')
    
    plt.xlabel('サイクル数')
    plt.ylabel('抵抗 (Ω)')
    plt.title('パラメータCが抵抗増加に与える影響')
    plt.legend()
    plt.grid(True)
    
    # Test D parameter
    plt.subplot(1, 2, 2)
    
    data2 = {
        'headers': ['Cycle'] + [f'D={d}' for d in D_values],
        'rows': []
    }
    
    for cycle in cycles:
        row = [cycle]
        for D in D_values:
            resistance = resistance_after_cycle(cycle, R0=R0, C=0.05, D=D)
            row.append(resistance)
        data2['rows'].append(row)
    
    for D in D_values:
        resistances = [resistance_after_cycle(n, R0=R0, C=0.05, D=D) for n in cycles]
        plt.plot(cycles, resistances, label=f'D={D}')
    
    plt.xlabel('サイクル数')
    plt.ylabel('抵抗 (Ω)')
    plt.title('パラメータDが抵抗増加に与える影響')
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
        # Use the enhanced simulate_charge function
        soc_c, cap_c, v_c, i_c, t_c, phase_c, _, _, _ = simulate_charge(cap_ah, c_rate, resistance)
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
        _, cap_d, v_d, _ = simulate_discharge(cap_ah, c_rate, resistance)
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
        resistance_values = get_parameter_range("内部抵抗", 0.01, 0.2, 5, min_val=0.001)
    else:
        # Default values
        resistance_values = [0.01, 0.05, 0.1, 0.15, 0.2]
    
    print(f"\n内部抵抗のテスト: {resistance_values}")
    
    plt.figure(figsize=(12, 5))
    
    # Charge curves with different resistance values
    plt.subplot(1, 2, 1)
    
    charge_data_r = {
        'headers': ['Capacity (Ah)'] + [f'R={r}' for r in resistance_values],
        'rows': []
    }
    
    max_points = 0
    all_cap_c = []
    all_v_c = []
    
    for r in resistance_values:
        # Use the enhanced simulate_charge function
        soc_c, cap_c, v_c, i_c, t_c, phase_c, _, _, _ = simulate_charge(cap_ah, 0.5, r)
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
        charge_data_r['rows'].append(row)
    
    plt.xlabel('容量 (Ah)')
    plt.ylabel('電圧 (V)')
    plt.title('内部抵抗が充電曲線に与える影響')
    plt.legend()
    plt.grid(True)
    
    # Discharge curves with different resistance values
    plt.subplot(1, 2, 2)
    
    discharge_data_r = {
        'headers': ['Capacity (Ah)'] + [f'R={r}' for r in resistance_values],
        'rows': []
    }
    
    max_points = 0
    all_cap_d = []
    all_v_d = []
    
    for r in resistance_values:
        _, cap_d, v_d, _ = simulate_discharge(cap_ah, 0.5, r)
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
        discharge_data_r['rows'].append(row)
    
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
        export_to_csv(charge_data, f"charge_c_rate_test_{timestamp}.csv")
        export_to_csv(discharge_data, f"discharge_c_rate_test_{timestamp}.csv")
        export_to_csv(charge_data_r, f"charge_resistance_test_{timestamp}.csv")
        export_to_csv(discharge_data_r, f"discharge_resistance_test_{timestamp}.csv")

def test_cv_charging_current():
    """Test and visualize the current profiles during CV charging phase"""
    print("\n=== CV充電電流プロファイルのテスト ===")
    
    # Get base parameters
    cap_ah = get_float_input("電池容量 (Ah)", 3.0, min_val=0.1)
    resistance = get_float_input("内部抵抗 (Ω)", 0.05, min_val=0.001)
    c_rate = get_float_input("C-レート", 0.5, min_val=0.05)
    end_current_ratio = get_float_input("終止電流比率 (C-rateの割合)", 0.05, min_val=0.01, max_val=0.5)
    
    # Simulate charge with current tracking
    print("\n充電シミュレーションを実行中...")
    soc_c, cap_c, v_c, i_c, t_c, phase_c, cv_start_time, cv_start_cap, cv_start_soc = simulate_charge(
        cap_ah, c_rate, resistance, end_current_ratio=end_current_ratio
    )
    
    # Find CC and CV phases
    cc_mask = (phase_c == 'CC')
    cv_mask = (phase_c == 'CV')
    
    # Check if CV phase exists
    if not np.any(cv_mask):
        print("CV相が検出されませんでした。パラメータを調整して再試行してください。")
        return
    
    print(f"CC相の時間: {cv_start_time/60:.2f} 分")
    print(f"CV相の時間: {(t_c[-1] - cv_start_time)/60:.2f} 分")
    print(f"CC相の容量: {cv_start_cap:.4f} Ah ({cv_start_cap/cap_ah*100:.1f}%)")
    print(f"CV相の容量: {cap_c[-1] - cv_start_cap:.4f} Ah ({(cap_c[-1] - cv_start_cap)/cap_ah*100:.1f}%)")
    print(f"CC相の終了SOC: {cv_start_soc:.4f}")
    print(f"CV相の終了SOC: {soc_c[-1]:.4f}")
    
    # Create figure for current profiles
    plt.figure(figsize=(15, 10))
    
    # Current vs. Capacity
    plt.subplot(2, 2, 1)
    plt.plot(cap_c[cc_mask], i_c[cc_mask], 'b-', label='CC相', linewidth=2)
    plt.plot(cap_c[cv_mask], i_c[cv_mask], 'r-', label='CV相', linewidth=2)
    plt.axvline(x=cv_start_cap, color='k', linestyle='--', label='CV相開始')
    plt.xlabel('容量 (Ah)')
    plt.ylabel('電流 (A)')
    plt.title('充電中の電流 vs. 容量')
    plt.legend()
    plt.grid(True)
    
    # Current vs. Time
    plt.subplot(2, 2, 2)
    plt.plot(t_c[cc_mask]/60, i_c[cc_mask], 'b-', label='CC相', linewidth=2)
    plt.plot(t_c[cv_mask]/60, i_c[cv_mask], 'r-', label='CV相', linewidth=2)
    plt.axvline(x=cv_start_time/60, color='k', linestyle='--', label='CV相開始')
    plt.xlabel('時間 (分)')
    plt.ylabel('電流 (A)')
    plt.title('充電中の電流 vs. 時間')
    plt.legend()
    plt.grid(True)
    
    # Current vs. SOC
    plt.subplot(2, 2, 3)
    plt.plot(soc_c[cc_mask], i_c[cc_mask], 'b-', label='CC相', linewidth=2)
    plt.plot(soc_c[cv_mask], i_c[cv_mask], 'r-', label='CV相', linewidth=2)
    plt.axvline(x=cv_start_soc, color='k', linestyle='--', label='CV相開始')
    plt.xlabel('SOC')
    plt.ylabel('電流 (A)')
    plt.title('充電中の電流 vs. SOC')
    plt.legend()
    plt.grid(True)
    
    # CV Phase Current Decay
    plt.subplot(2, 2, 4)
    cv_time = t_c[cv_mask] - cv_start_time
    cv_current = i_c[cv_mask]
    plt.plot(cv_time/60, cv_current, 'r-', linewidth=2)
    plt.axhline(y=c_rate*cap_ah*end_current_ratio, color='k', linestyle='--', 
                label=f'終止電流 ({end_current_ratio*100:.1f}% of C-rate)')
    plt.xlabel('CV相の時間 (分)')
    plt.ylabel('電流 (A)')
    plt.title('CV相での電流減衰')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    # Create figure for voltage profiles
    plt.figure(figsize=(15, 5))
    
    # Voltage vs. Capacity
    plt.subplot(1, 2, 1)
    plt.plot(cap_c[cc_mask], v_c[cc_mask], 'b-', label='CC相', linewidth=2)
    plt.plot(cap_c[cv_mask], v_c[cv_mask], 'r-', label='CV相', linewidth=2)
    plt.axvline(x=cv_start_cap, color='k', linestyle='--', label='CV相開始')
    plt.xlabel('容量 (Ah)')
    plt.ylabel('電圧 (V)')
    plt.title('充電中の電圧 vs. 容量')
    plt.legend()
    plt.grid(True)
    
    # Voltage vs. Time
    plt.subplot(1, 2, 2)
    plt.plot(t_c[cc_mask]/60, v_c[cc_mask], 'b-', label='CC相', linewidth=2)
    plt.plot(t_c[cv_mask]/60, v_c[cv_mask], 'r-', label='CV相', linewidth=2)
    plt.axvline(x=cv_start_time/60, color='k', linestyle='--', label='CV相開始')
    plt.xlabel('時間 (分)')
    plt.ylabel('電圧 (V)')
    plt.title('充電中の電圧 vs. 時間')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    # Ask if user wants to export results
    if get_yes_no_input("\nテスト結果をCSVファイルに保存しますか？"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Prepare data for CSV export
        cv_data = {
            'headers': ['Time (s)', 'Capacity (Ah)', 'Voltage (V)', 'Current (A)', 'SOC', 'Phase'],
            'rows': []
        }
        
        for i in range(len(t_c)):
            cv_data['rows'].append([t_c[i], cap_c[i], v_c[i], i_c[i], soc_c[i], phase_c[i]])
        
        export_to_csv(cv_data, f"cv_charging_profile_{timestamp}.csv")

def run_capacity_retention_simulation():
    """Run the capacity retention simulation with enhanced CV current tracking"""
    print("\n===== リチウムイオン電池の容量維持率シミュレーション (V3) =====")
    print("このプログラムは、リチウムイオン電池のサイクル数に対する容量維持率をシミュレーションします。")
    print("V3では、CV充電時の電流推移のシミュレーションと可視化機能が追加されています。")
    
    # Get battery parameters
    print("\n--- 電池の基本パラメータ ---")
    Q0 = get_float_input("初期容量 (Ah)", 3.0, min_val=0.1)
    R0 = get_float_input("初期内部抵抗 (Ω)", 0.05, min_val=0.001)
    
    # Get degradation model parameters
    print("\n--- 劣化モデルのパラメータ ---")
    A = get_float_input("容量劣化パラメータA", 0.1, min_val=0.01, max_val=1.0)
    B = get_float_input("容量劣化パラメータB", 0.05, min_val=0.001, max_val=1.0)
    C = get_float_input("抵抗増加パラメータC", 0.05, min_val=0.001, max_val=1.0)
    D = get_float_input("抵抗増加パラメータD", 1.0, min_val=0.1, max_val=5.0)
    
    # Get simulation parameters
    print("\n--- シミュレーションのパラメータ ---")
    num_cycles = get_int_input("シミュレーションするサイクル数", 50, min_val=1)
    c_rate = get_float_input("C-レート", 0.5, min_val=0.05)
    end_current_ratio = get_float_input("終止電流比率 (C-rateの割合)", 0.05, min_val=0.01, max_val=0.5)
    
    # Run simulation
    print("\nシミュレーションを実行中...")
    
    # Initialize arrays to store results
    cycles = np.arange(1, num_cycles + 1)
    capacities = np.zeros(num_cycles)
    resistances = np.zeros(num_cycles)
    retention_rates = np.zeros(num_cycles)
    
    # Store charge/discharge curves for selected cycles
    selected_cycles = [1, num_cycles // 4, num_cycles // 2, num_cycles * 3 // 4, num_cycles]
    selected_cycles = [c for c in selected_cycles if c <= num_cycles]
    selected_cycles = sorted(list(set(selected_cycles)))  # Remove duplicates
    
    charge_curves = {}
    discharge_curves = {}
    cv_current_profiles = {}
    
    # Run simulation for each cycle
    for n in cycles:
        # Calculate degraded parameters
        cap_n = capacity_after_cycle(n, Q0=Q0, A=A, B=B)
        res_n = resistance_after_cycle(n, R0=R0, C=C, D=D)
        
        # Store results
        capacities[n-1] = cap_n
        resistances[n-1] = res_n
        retention_rates[n-1] = cap_n / Q0
        
        # Store charge/discharge curves for selected cycles
        if n in selected_cycles:
            # Simulate charge with enhanced CV current tracking
            soc_c, cap_c, v_c, i_c, t_c, phase_c, cv_start_time, cv_start_cap, cv_start_soc = simulate_charge(
                cap_n, c_rate, res_n, end_current_ratio=end_current_ratio
            )
            
            # Simulate discharge
            soc_d, cap_d, v_d, i_d = simulate_discharge(cap_n, c_rate, res_n)
            
            # Store curves
            charge_curves[n] = {
                'soc': soc_c, 'cap': cap_c, 'voltage': v_c, 'current': i_c, 
                'time': t_c, 'phase': phase_c, 'cv_start_time': cv_start_time,
                'cv_start_cap': cv_start_cap, 'cv_start_soc': cv_start_soc
            }
            discharge_curves[n] = {'soc': soc_d, 'cap': cap_d, 'voltage': v_d, 'current': i_d}
            
            # Extract CV current profile
            cv_mask = (phase_c == 'CV')
            if np.any(cv_mask):
                cv_current_profiles[n] = {
                    'time': t_c[cv_mask] - cv_start_time,
                    'current': i_c[cv_mask],
                    'capacity': cap_c[cv_mask],
                    'voltage': v_c[cv_mask],
                    'soc': soc_c[cv_mask]
                }
    
    # Calculate degradation rates
    capacity_degradation_rates = np.zeros(num_cycles - 1)
    resistance_increase_rates = np.zeros(num_cycles - 1)
    retention_degradation_rates = np.zeros(num_cycles - 1)
    
    for i in range(num_cycles - 1):
        capacity_degradation_rates[i] = (capacities[i] - capacities[i+1]) / capacities[i] * 100
        resistance_increase_rates[i] = (resistances[i+1] - resistances[i]) / resistances[i] * 100
        retention_degradation_rates[i] = (retention_rates[i] - retention_rates[i+1]) / retention_rates[i] * 100
    
    # Plot results
    plt.figure(figsize=(15, 10))
    
    # Plot 1: Charge curves
    plt.subplot(2, 3, 1)
    for n in selected_cycles:
        spl = UnivariateSpline(charge_curves[n]['cap'], charge_curves[n]['voltage'], s=0.001)
        xs = np.linspace(charge_curves[n]['cap'].min(), charge_curves[n]['cap'].max(), 400)
        plt.plot(xs, spl(xs), label=f'サイクル {n}')
    
    plt.xlabel('容量 (Ah)')
    plt.ylabel('電圧 (V)')
    plt.title('充電曲線')
    plt.legend()
    plt.grid(True)
    
    # Plot 2: Discharge curves
    plt.subplot(2, 3, 2)
    for n in selected_cycles:
        spl = UnivariateSpline(discharge_curves[n]['cap'], discharge_curves[n]['voltage'], s=0.001)
        xs = np.linspace(discharge_curves[n]['cap'].min(), discharge_curves[n]['cap'].max(), 400)
        plt.plot(xs, spl(xs), label=f'サイクル {n}')
    
    plt.xlabel('放電容量 (Ah)')
    plt.ylabel('電圧 (V)')
    plt.title('放電曲線')
    plt.legend()
    plt.grid(True)
    
    # Plot 3: Capacity and resistance vs. cycle
    plt.subplot(2, 3, 3)
    plt.plot(cycles, capacities, 'b-', label='容量')
    plt.xlabel('サイクル数')
    plt.ylabel('容量 (Ah)', color='b')
    plt.tick_params(axis='y', labelcolor='b')
    plt.grid(True)
    
    ax2 = plt.twinx()
    ax2.plot(cycles, resistances, 'r-', label='内部抵抗')
    ax2.set_ylabel('内部抵抗 (Ω)', color='r')
    ax2.tick_params(axis='y', labelcolor='r')
    
    plt.title('容量と内部抵抗の推移')
    
    # Plot 4: Retention rate vs. cycle
    plt.subplot(2, 3, 4)
    plt.plot(cycles, retention_rates * 100, 'g-')
    plt.xlabel('サイクル数')
    plt.ylabel('容量維持率 (%)')
    plt.title('容量維持率の推移')
    plt.grid(True)
    
    # Plot 5: Degradation rates vs. cycle
    plt.subplot(2, 3, 5)
    plt.plot(cycles[:-1], capacity_degradation_rates, 'b-', label='容量劣化率')
    plt.plot(cycles[:-1], resistance_increase_rates, 'r-', label='抵抗増加率')
    plt.plot(cycles[:-1], retention_degradation_rates, 'g-', label='維持率劣化率')
    plt.xlabel('サイクル数')
    plt.ylabel('変化率 (%/サイクル)')
    plt.title('劣化率の推移')
    plt.legend()
    plt.grid(True)
    
    # Plot 6: CV current profiles for selected cycles
    plt.subplot(2, 3, 6)
    for n in selected_cycles:
        if n in cv_current_profiles:
            cv_data = cv_current_profiles[n]
            plt.plot(cv_data['time']/60, cv_data['current'], label=f'サイクル {n}')
    
    plt.xlabel('CV相の時間 (分)')
    plt.ylabel('電流 (A)')
    plt.title('CV相での電流減衰')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    # Ask if user wants to see detailed CV phase analysis
    if get_yes_no_input("\nCV相の詳細分析を表示しますか？"):
        for n in selected_cycles:
            if n in cv_current_profiles:
                plt.figure(figsize=(15, 10))
                plt.suptitle(f'サイクル {n} のCV相詳細分析', fontsize=16)
                
                # Get data
                charge_data = charge_curves[n]
                cv_data = cv_current_profiles[n]
                
                # Find CC and CV phases
                cc_mask = (charge_data['phase'] == 'CC')
                cv_mask = (charge_data['phase'] == 'CV')
                
                # Current vs. Capacity
                plt.subplot(2, 2, 1)
                plt.plot(charge_data['cap'][cc_mask], charge_data['current'][cc_mask], 'b-', label='CC相', linewidth=2)
                plt.plot(charge_data['cap'][cv_mask], charge_data['current'][cv_mask], 'r-', label='CV相', linewidth=2)
                plt.axvline(x=charge_data['cv_start_cap'], color='k', linestyle='--', label='CV相開始')
                plt.xlabel('容量 (Ah)')
                plt.ylabel('電流 (A)')
                plt.title('充電中の電流 vs. 容量')
                plt.legend()
                plt.grid(True)
                
                # Current vs. Time
                plt.subplot(2, 2, 2)
                plt.plot(charge_data['time'][cc_mask]/60, charge_data['current'][cc_mask], 'b-', label='CC相', linewidth=2)
                plt.plot(charge_data['time'][cv_mask]/60, charge_data['current'][cv_mask], 'r-', label='CV相', linewidth=2)
                plt.axvline(x=charge_data['cv_start_time']/60, color='k', linestyle='--', label='CV相開始')
                plt.xlabel('時間 (分)')
                plt.ylabel('電流 (A)')
                plt.title('充電中の電流 vs. 時間')
                plt.legend()
                plt.grid(True)
                
                # Current vs. SOC
                plt.subplot(2, 2, 3)
                plt.plot(charge_data['soc'][cc_mask], charge_data['current'][cc_mask], 'b-', label='CC相', linewidth=2)
                plt.plot(charge_data['soc'][cv_mask], charge_data['current'][cv_mask], 'r-', label='CV相', linewidth=2)
                plt.axvline(x=charge_data['cv_start_soc'], color='k', linestyle='--', label='CV相開始')
                plt.xlabel('SOC')
                plt.ylabel('電流 (A)')
                plt.title('充電中の電流 vs. SOC')
                plt.legend()
                plt.grid(True)
                
                # CV Phase Current Decay
                plt.subplot(2, 2, 4)
                plt.plot(cv_data['time']/60, cv_data['current'], 'r-', linewidth=2)
                plt.axhline(y=c_rate*capacities[n-1]*end_current_ratio, color='k', linestyle='--', 
                            label=f'終止電流 ({end_current_ratio*100:.1f}% of C-rate)')
                plt.xlabel('CV相の時間 (分)')
                plt.ylabel('電流 (A)')
                plt.title('CV相での電流減衰')
                plt.legend()
                plt.grid(True)
                
                plt.tight_layout()
                plt.show()
    
    # Ask if user wants to export results
    if get_yes_no_input("\n結果をCSVファイルに保存しますか？"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export capacity and resistance data
        capacity_data = {
            'headers': ['Cycle', 'Capacity (Ah)', 'Resistance (Ω)', 'Retention Rate (%)'],
            'rows': []
        }
        
        for i in range(num_cycles):
            capacity_data['rows'].append([
                cycles[i], capacities[i], resistances[i], retention_rates[i] * 100
            ])
        
        export_to_csv(capacity_data, f"capacity_retention_{timestamp}.csv")
        
        # Export degradation rate data
        degradation_data = {
            'headers': ['Cycle', 'Capacity Degradation Rate (%)', 'Resistance Increase Rate (%)', 'Retention Degradation Rate (%)'],
            'rows': []
        }
        
        for i in range(num_cycles - 1):
            degradation_data['rows'].append([
                cycles[i], capacity_degradation_rates[i], resistance_increase_rates[i], retention_degradation_rates[i]
            ])
        
        export_to_csv(degradation_data, f"degradation_rates_{timestamp}.csv")
        
        # Export CV current profiles for selected cycles
        for n in selected_cycles:
            if n in cv_current_profiles:
                cv_data = cv_current_profiles[n]
                cv_profile_data = {
                    'headers': ['Time (s)', 'Time from CV start (s)', 'Current (A)', 'Capacity (Ah)', 'Voltage (V)', 'SOC'],
                    'rows': []
                }
                
                for i in range(len(cv_data['time'])):
                    cv_profile_data['rows'].append([
                        cv_data['time'][i] + charge_curves[n]['cv_start_time'],
                        cv_data['time'][i],
                        cv_data['current'][i],
                        cv_data['capacity'][i],
                        cv_data['voltage'][i],
                        cv_data['soc'][i]
                    ])
                
                export_to_csv(cv_profile_data, f"cv_current_profile_cycle{n}_{timestamp}.csv")

def main():
    """Main function to run the integrated test and capacity retention simulation"""
    print("===== リチウムイオン電池シミュレーション統合ツール (V3) =====")
    print("このプログラムは、リチウムイオン電池の劣化モデルと充放電曲線をテストし、")
    print("容量維持率のシミュレーションを行います。")
    print("V3では、CV充電時の電流推移のシミュレーションと可視化機能が追加されています。")
    
    while True:
        print("\n以下のモードから選択してください:")
        print("1. パラメータテストモード")
        print("2. サイクルシミュレーションモード")
        print("0. 終了")
        
        choice = get_int_input("選択", 0, min_val=0, max_val=2)
        
        if choice == 0:
            break
        elif choice == 1:
            # Parameter test mode
            while True:
                print("\n以下のテストから選択してください:")
                print("1. 容量劣化パラメータのテスト")
                print("2. 抵抗増加パラメータのテスト")
                print("3. 充放電曲線パラメータのテスト")
                print("4. CV充電電流プロファイルのテスト")
                print("0. 戻る")
                
                test_choice = get_int_input("選択", 0, min_val=0, max_val=4)
                
                if test_choice == 0:
                    break
                elif test_choice == 1:
                    test_capacity_degradation()
                elif test_choice == 2:
                    test_resistance_degradation()
                elif test_choice == 3:
                    test_charge_discharge_curves()
                elif test_choice == 4:
                    test_cv_charging_current()
        elif choice == 2:
            # Cycle simulation mode
            run_capacity_retention_simulation()
    
    print("\nプログラムを終了します。")

if __name__ == "__main__":
    main()