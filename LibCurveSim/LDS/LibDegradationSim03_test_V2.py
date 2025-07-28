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

def main():
    """Main function to run parameter tests with custom ranges"""
    print("=" * 60)
    print("リチウムイオン電池シミュレーション - パラメータテストモード V2")
    print("=" * 60)
    print("このプログラムでは、各パラメータが電池の特性にどのような影響を与えるかを可視化します。")
    print("パラメータの範囲を任意で指定できるようになりました。")
    print("-" * 60)
    
    while True:
        print("\n以下のテストから選択してください:")
        print("1. 容量劣化パラメータ (A, B) のテスト")
        print("2. 抵抗増加パラメータ (C, D) のテスト")
        print("3. 充放電曲線パラメータ (C-レート, 内部抵抗) のテスト")
        print("0. 終了")
        
        choice = get_int_input("\n選択してください", 0, min_val=0, max_val=3)
        
        if choice == 0:
            break
        elif choice == 1:
            test_capacity_degradation()
        elif choice == 2:
            test_resistance_degradation()
        elif choice == 3:
            test_charge_discharge_curves()
    
    print("\nプログラムを終了します。")

if __name__ == "__main__":
    main()