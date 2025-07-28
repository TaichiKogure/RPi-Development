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
    time = 0.0
    
    # Initialize histories with initial values
    soc_hist = [soc]
    cap_hist = [0.0]
    v_hist = [ocv_from_soc(soc)]
    i_hist = [I0]  # Add current history
    t_hist = [0.0]  # Add time history
    phase_hist = ['CC']  # Add charging phase history
    
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
    
    # CV phase
    cv_start_time = time
    cv_start_cap = charged
    cv_start_soc = soc
    
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
        v_hist.append(v_max)  # In CV phase, voltage is constant at v_max
        i_hist.append(I)
        t_hist.append(time)
        phase_hist.append('CV')
    
    # Convert lists to numpy arrays
    return (np.array(soc_hist), np.array(cap_hist), np.array(v_hist), 
            np.array(i_hist), np.array(t_hist), np.array(phase_hist),
            cv_start_time, cv_start_cap, cv_start_soc)

def simulate_discharge(cap_ah, c_rate, resistance, v_min=3.0519, dt=1.0):
    dt_h = dt / 3600.0
    I = c_rate * cap_ah
    soc = 1.0
    discharged = 0.0
    time = 0.0
    
    # Initialize histories with initial values
    soc_hist = [soc]
    cap_hist = [0.0]
    v_hist = [ocv_from_soc(soc)]
    t_hist = [0.0]  # Add time history
    
    while soc > 0.0:
        V_oc = ocv_from_soc(soc)
        V_term = V_oc - I * resistance
        if V_term <= v_min: 
            break
        
        soc -= (I * dt_h) / cap_ah
        discharged += I * dt_h
        time += dt
        
        soc_hist.append(soc)
        cap_hist.append(discharged)
        v_hist.append(V_term)
        t_hist.append(time)
    
    # Convert lists to numpy arrays
    return np.array(soc_hist), np.array(cap_hist), np.array(v_hist), np.array(t_hist)

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
            if not value_str:
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

def get_int_input(prompt, default, min_val=None, max_val=None):
    """Get integer input from user with validation"""
    while True:
        try:
            value_str = input(f"{prompt} [{default}]: ").strip()
            if not value_str:
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

def get_yes_no_input(prompt, default=True):
    """Get yes/no input from user"""
    default_str = "Y/n" if default else "y/N"
    while True:
        response = input(f"{prompt} [{default_str}]: ").strip().lower()
        if not response:
            return default
        if response in ['y', 'yes']:
            return True
        if response in ['n', 'no']:
            return False
        print("'y' または 'n' を入力してください。")

def get_parameter_range(param_name, default_min, default_max, default_points=5, min_val=None, max_val=None):
    """Get parameter range from user"""
    print(f"\n{param_name}の範囲を設定します:")
    min_value = get_float_input(f"最小値", default_min, min_val=min_val)
    max_value = get_float_input(f"最大値", default_max, min_val=min_value)
    num_points = get_int_input(f"分割数", default_points, min_val=2)
    
    return np.linspace(min_value, max_value, num_points)

def export_to_csv(data, filename):
    """Export data to CSV file"""
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data['headers'])
        for row in data['rows']:
            writer.writerow(row)
    print(f"データを {filename} に保存しました。")

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

def main():
    """Main function to run the tests"""
    print("===== リチウムイオン電池シミュレーションテスト (V3) =====")
    print("このプログラムは、リチウムイオン電池の劣化モデルと充放電曲線をテストします。")
    print("V3では、CV充電時の電流推移のシミュレーションと可視化機能が追加されています。")
    
    while True:
        print("\n以下のテストから選択してください:")
        print("1. 容量劣化パラメータのテスト")
        print("2. 抵抗増加パラメータのテスト")
        print("3. 充放電曲線パラメータのテスト")
        print("4. CV充電電流プロファイルのテスト (新機能)")
        print("0. 終了")
        
        choice = get_int_input("選択", 0, min_val=0, max_val=4)
        
        if choice == 0:
            break
        elif choice == 1:
            test_capacity_degradation()
        elif choice == 2:
            test_resistance_degradation()
        elif choice == 3:
            test_charge_discharge_curves()
        elif choice == 4:
            test_cv_charging_current()
    
    print("\nプログラムを終了します。")

if __name__ == "__main__":
    main()