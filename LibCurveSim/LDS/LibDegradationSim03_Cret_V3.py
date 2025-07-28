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
        
        # Simulate charge and discharge with enhanced data
        soc_c, cap_c, v_c, i_c, t_c, phase_c, cv_start_time, cv_start_cap, cv_start_soc = simulate_charge(
            cap_n, c_rate, res_n, v_max, end_current_ratio, dt
        )
        soc_d, cap_d, v_d, t_d = simulate_discharge(cap_n, c_rate, res_n, v_min, dt)
        
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
        
        # Store enhanced results including current, time, and phase data
        results.append((n, cap_n, res_n, discharged_capacity, retention, 
                       capacity_degradation_rates[-1], resistance_increase_rates[-1], 
                       retention_degradation_rates[-1], soc_c, cap_c, v_c, i_c, t_c, phase_c,
                       cv_start_time, cv_start_cap, cv_start_soc, soc_d, cap_d, v_d, t_d))
    
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
    for n, _, _, _, _, _, _, _, _, cap_c, v_c, _, _, _, _, _, _, _, _, _, _ in results:
        spl = UnivariateSpline(cap_c, v_c, s=smoothing_s)
        xs = np.linspace(cap_c.min(), cap_c.max(), 400)
        plt.plot(xs, spl(xs), label=f'Ch {n}', lw=1)
    plt.xlabel('Capacity (Ah)')
    plt.ylabel('Voltage (V)')
    plt.title('Smoothed Charge Curves (all cycles)')
    plt.grid(True)

    # Discharge curves (top middle)
    plt.subplot(2, 3, 2)
    for n, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, cap_d, v_d, _ in results:
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

def plot_current_profiles(results):
    """Plot current profiles during CV charging for selected cycles"""
    plt.figure(figsize=(15, 10))
    
    # Select cycles to display (first, last, and some in between)
    num_cycles = len(results)
    if num_cycles <= 5:
        cycles_to_show = list(range(num_cycles))
    else:
        cycles_to_show = [0]  # First cycle
        step = max(1, (num_cycles - 2) // 3)
        cycles_to_show.extend(range(step, num_cycles-1, step))  # Middle cycles
        cycles_to_show.append(num_cycles-1)  # Last cycle
    
    # Current vs Time during CV phase (top left)
    plt.subplot(2, 2, 1)
    for idx in cycles_to_show:
        n, _, _, _, _, _, _, _, _, _, _, i_c, t_c, phase_c, cv_start_time, _, _, _, _, _, _ = results[idx]
        
        # Extract CV phase data
        cv_mask = (phase_c == 'CV')
        if np.any(cv_mask):
            cv_time = t_c[cv_mask] - cv_start_time  # Time relative to CV start
            cv_current = i_c[cv_mask]
            plt.plot(cv_time/60, cv_current, '-', label=f'Cycle {n}', linewidth=2)
    
    plt.xlabel('Time in CV Phase (min)')
    plt.ylabel('Current (A)')
    plt.title('Current Decay During CV Charging')
    plt.grid(True)
    plt.legend()
    
    # Current vs Capacity during CV phase (top right)
    plt.subplot(2, 2, 2)
    for idx in cycles_to_show:
        n, _, _, _, _, _, _, _, _, cap_c, _, i_c, _, phase_c, _, cv_start_cap, _, _, _, _, _ = results[idx]
        
        # Extract CV phase data
        cv_mask = (phase_c == 'CV')
        if np.any(cv_mask):
            cv_cap = cap_c[cv_mask] - cv_start_cap  # Capacity relative to CV start
            cv_current = i_c[cv_mask]
            plt.plot(cv_cap, cv_current, '-', label=f'Cycle {n}', linewidth=2)
    
    plt.xlabel('Capacity in CV Phase (Ah)')
    plt.ylabel('Current (A)')
    plt.title('Current vs Capacity During CV Charging')
    plt.grid(True)
    plt.legend()
    
    # Normalized current vs time (bottom left)
    plt.subplot(2, 2, 3)
    for idx in cycles_to_show:
        n, cap_n, _, _, _, _, _, _, _, _, _, i_c, t_c, phase_c, cv_start_time, _, _, _, _, _, _ = results[idx]
        
        # Extract CV phase data
        cv_mask = (phase_c == 'CV')
        if np.any(cv_mask):
            cv_time = t_c[cv_mask] - cv_start_time  # Time relative to CV start
            cv_current = i_c[cv_mask]
            
            # Normalize current by C-rate
            c_rate = 0.5  # This should match the c_rate used in simulation
            I0 = c_rate * cap_n
            normalized_current = cv_current / I0
            
            plt.plot(cv_time/60, normalized_current, '-', label=f'Cycle {n}', linewidth=2)
    
    plt.xlabel('Time in CV Phase (min)')
    plt.ylabel('Normalized Current (I/I0)')
    plt.title('Normalized Current Decay During CV Charging')
    plt.grid(True)
    plt.legend()
    
    # CV phase duration vs cycle number (bottom right)
    plt.subplot(2, 2, 4)
    
    cycle_numbers = []
    cv_durations = []
    cv_capacities = []
    
    for n, _, _, _, _, _, _, _, _, cap_c, _, _, t_c, phase_c, cv_start_time, cv_start_cap, _, _, _, _, _ in results:
        # Extract CV phase data
        cv_mask = (phase_c == 'CV')
        if np.any(cv_mask):
            cv_duration = (t_c[cv_mask][-1] - cv_start_time) / 60  # Duration in minutes
            cv_capacity = cap_c[cv_mask][-1] - cv_start_cap  # Capacity charged during CV
            
            cycle_numbers.append(n)
            cv_durations.append(cv_duration)
            cv_capacities.append(cv_capacity)
    
    # Plot CV duration vs cycle number
    plt.plot(cycle_numbers, cv_durations, 'o-', color='blue', label='Duration')
    plt.xlabel('Cycle Number')
    plt.ylabel('CV Phase Duration (min)')
    plt.title('CV Phase Duration vs Cycle Number')
    plt.grid(True)
    
    # Add secondary y-axis for CV capacity
    ax2 = plt.gca().twinx()
    ax2.plot(cycle_numbers, cv_capacities, 'o-', color='red', label='Capacity')
    ax2.set_ylabel('CV Phase Capacity (Ah)', color='red')
    ax2.tick_params(axis='y', labelcolor='red')
    
    # Combine legends
    lines1, labels1 = plt.gca().get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    plt.tight_layout()
    plt.show()

def export_to_csv(results, filename_prefix):
    """Export simulation results to CSV files with degradation rates and current profiles"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create directory if it doesn't exist
    os.makedirs('results', exist_ok=True)
    
    # Export cycle summary with retention and degradation rate data
    summary_filename = f"results/{filename_prefix}_summary_{timestamp}.csv"
    with open(summary_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Cycle', 'Capacity (Ah)', 'Resistance (ohm)', 'Discharged Capacity (Ah)', 
                         'Retention (%)', 'Capacity Degradation Rate (%/cycle)', 
                         'Resistance Increase Rate (%/cycle)', 'Retention Degradation Rate (%/cycle)',
                         'CV Start Time (s)', 'CV Start Capacity (Ah)', 'CV Start SOC'])
        for n, cap_n, res_n, discharged_cap, retention, cap_deg_rate, res_inc_rate, ret_deg_rate, _, _, _, _, _, _, cv_start_time, cv_start_cap, cv_start_soc, _, _, _, _ in results:
            writer.writerow([n, cap_n, res_n, discharged_cap, retention, cap_deg_rate, res_inc_rate, ret_deg_rate, 
                            cv_start_time, cv_start_cap, cv_start_soc])
    print(f"サイクル概要を保存しました: {summary_filename}")
    
    # Export detailed charge/discharge data for each cycle
    for n, _, _, _, _, _, _, _, soc_c, cap_c, v_c, i_c, t_c, phase_c, _, _, _, soc_d, cap_d, v_d, t_d in results:
        # Charge data with current and phase
        charge_filename = f"results/{filename_prefix}_cycle{n}_charge_{timestamp}.csv"
        with open(charge_filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['SOC', 'Capacity (Ah)', 'Voltage (V)', 'Current (A)', 'Time (s)', 'Phase'])
            for i in range(len(soc_c)):
                writer.writerow([soc_c[i], cap_c[i], v_c[i], i_c[i], t_c[i], phase_c[i]])
        
        # Discharge data with time
        discharge_filename = f"results/{filename_prefix}_cycle{n}_discharge_{timestamp}.csv"
        with open(discharge_filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['SOC', 'Capacity (Ah)', 'Voltage (V)', 'Time (s)'])
            for i in range(len(soc_d)):
                writer.writerow([soc_d[i], cap_d[i], v_d[i], t_d[i]])
    
    # Export retention data separately
    retention_filename = f"results/{filename_prefix}_retention_{timestamp}.csv"
    with open(retention_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Cycle', 'Discharged Capacity (Ah)', 'Retention (%)', 
                         'Capacity Degradation Rate (%/cycle)', 'Resistance Increase Rate (%/cycle)', 
                         'Retention Degradation Rate (%/cycle)'])
        for n, _, _, discharged_cap, retention, cap_deg_rate, res_inc_rate, ret_deg_rate, _, _, _, _, _, _, _, _, _, _, _, _, _ in results:
            writer.writerow([n, discharged_cap, retention, cap_deg_rate, res_inc_rate, ret_deg_rate])
    print(f"容量維持率データを保存しました: {retention_filename}")
    
    # Export degradation rate data separately
    degradation_filename = f"results/{filename_prefix}_degradation_rates_{timestamp}.csv"
    with open(degradation_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Cycle', 'Capacity Degradation Rate (%/cycle)', 
                         'Resistance Increase Rate (%/cycle)', 'Retention Degradation Rate (%/cycle)'])
        for n, _, _, _, _, cap_deg_rate, res_inc_rate, ret_deg_rate, _, _, _, _, _, _, _, _, _, _, _, _, _ in results:
            writer.writerow([n, cap_deg_rate, res_inc_rate, ret_deg_rate])
    print(f"劣化率データを保存しました: {degradation_filename}")
    
    # Export CV phase data separately
    cv_filename = f"results/{filename_prefix}_cv_phase_data_{timestamp}.csv"
    with open(cv_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Cycle', 'CV Start Time (s)', 'CV Start Capacity (Ah)', 'CV Start SOC', 
                         'CV Duration (s)', 'CV Capacity (Ah)'])
        
        for n, cap_n, _, _, _, _, _, _, _, cap_c, _, i_c, t_c, phase_c, cv_start_time, cv_start_cap, cv_start_soc, _, _, _, _ in results:
            # Extract CV phase data
            cv_mask = (phase_c == 'CV')
            if np.any(cv_mask):
                cv_duration = t_c[cv_mask][-1] - cv_start_time
                cv_capacity = cap_c[cv_mask][-1] - cv_start_cap
                writer.writerow([n, cv_start_time, cv_start_cap, cv_start_soc, cv_duration, cv_capacity])
            else:
                writer.writerow([n, cv_start_time, cv_start_cap, cv_start_soc, 0, 0])
    
    print(f"CV相データを保存しました: {cv_filename}")
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
    """Run the simulation in interactive mode with capacity retention and degradation rates"""
    print("=" * 60)
    print("リチウムイオン電池の劣化シミュレーション - 容量維持率表示モード V3")
    print("=" * 60)
    print("各パラメータの値を入力してください。デフォルト値を使用する場合は Enter キーを押してください。")
    print("V3では、CV充電時の電流推移のシミュレーションと可視化機能が追加されています。")
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
    
    # Ask if user wants to see current profiles
    if get_yes_no_input("\nCV充電時の電流プロファイルを表示しますか？", True):
        plot_current_profiles(results)
    
    # Ask if user wants to export results to CSV
    if get_yes_no_input("\nシミュレーション結果をCSVファイルに保存しますか？"):
        filename_prefix = input("ファイル名のプレフィックスを入力してください [sim]: ").strip()
        if filename_prefix == "":
            filename_prefix = "sim"
        export_to_csv(results, filename_prefix)
    
    print("\nシミュレーションが完了しました。")

if __name__=='__main__':
    interactive_mode()