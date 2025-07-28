import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, UnivariateSpline

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

# degradation models
def capacity_after_cycle(n, Q0=3.0, A=0.1, B=0.05):
    """Calculate capacity after n cycles"""
    return Q0 * (1 - A * (1 - np.exp(-B * n)))

def resistance_after_cycle(n, R0=0.05, C=0.05, D=1.0):
    """Calculate resistance after n cycles"""
    return R0 * (1 + C * (n**D))

def run_all_cycles(num_cycles=50, c_rate=0.5, end_current_ratio=0.05):
    """
    Run simulation for all cycles with enhanced CV current tracking
    
    Returns:
    - List of tuples containing cycle data:
      (cycle_number, charge_capacity, charge_voltage, charge_current, charge_time, charge_phase,
       discharge_capacity, discharge_voltage, discharge_current,
       cv_start_time, cv_start_cap, cv_start_soc)
    """
    results = []
    for n in range(1, num_cycles+1):
        cap_n = capacity_after_cycle(n)
        res_n = resistance_after_cycle(n)
        
        # Simulate charge with enhanced CV current tracking
        soc_c, cap_c, v_c, i_c, t_c, phase_c, cv_start_time, cv_start_cap, cv_start_soc = simulate_charge(
            cap_n, c_rate, res_n, end_current_ratio=end_current_ratio
        )
        
        # Simulate discharge
        soc_d, cap_d, v_d, i_d = simulate_discharge(cap_n, c_rate, res_n)
        
        results.append((n, cap_c, v_c, i_c, t_c, phase_c, cap_d, v_d, i_d, 
                        cv_start_time, cv_start_cap, cv_start_soc))
    
    return results

def plot_all_smoothed(results, smoothing_s=0.001):
    """Plot smoothed charge and discharge curves for all cycles"""
    plt.figure(figsize=(12, 5))
    
    # Charge side
    plt.subplot(1, 2, 1)
    for n, cap_c, v_c, _, _, _, _, _, _, _, _, _ in results:
        spl = UnivariateSpline(cap_c, v_c, s=smoothing_s)
        xs = np.linspace(cap_c.min(), cap_c.max(), 400)
        plt.plot(xs, spl(xs), label=f'Ch {n}', lw=1)
    
    plt.xlabel('Capacity (Ah)')
    plt.ylabel('Voltage (V)')
    plt.title('Smoothed Charge Curves (all cycles)')
    plt.grid(True)
    
    # Discharge side
    plt.subplot(1, 2, 2)
    for n, _, _, _, _, _, cap_d, v_d, _, _, _, _ in results:
        spl = UnivariateSpline(cap_d, v_d, s=smoothing_s)
        xs = np.linspace(cap_d.min(), cap_d.max(), 400)
        plt.plot(xs, spl(xs), label=f'Dis {n}', lw=1)
    
    plt.xlabel('Discharged Capacity (Ah)')
    plt.ylabel('Voltage (V)')
    plt.title('Smoothed Discharge Curves (all cycles)')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def plot_cv_current_profiles(results, selected_cycles=None):
    """Plot CV current profiles for selected cycles"""
    if selected_cycles is None:
        # Default: first, middle, and last cycle
        num_cycles = len(results)
        selected_cycles = [1, num_cycles // 2, num_cycles]
    
    plt.figure(figsize=(15, 10))
    
    # Current vs. Time
    plt.subplot(2, 2, 1)
    for n, _, _, i_c, t_c, phase_c, _, _, _, cv_start_time, _, _ in results:
        if n in selected_cycles:
            # Find CV phase
            cv_mask = (phase_c == 'CV')
            if np.any(cv_mask):
                cv_time = t_c[cv_mask] - cv_start_time
                cv_current = i_c[cv_mask]
                plt.plot(cv_time/60, cv_current, label=f'Cycle {n}')
    
    plt.xlabel('CV Phase Time (min)')
    plt.ylabel('Current (A)')
    plt.title('CV Current vs. Time')
    plt.legend()
    plt.grid(True)
    
    # Current vs. Capacity
    plt.subplot(2, 2, 2)
    for n, cap_c, _, i_c, _, phase_c, _, _, _, _, cv_start_cap, _ in results:
        if n in selected_cycles:
            # Find CV phase
            cv_mask = (phase_c == 'CV')
            if np.any(cv_mask):
                cv_cap = cap_c[cv_mask]
                cv_current = i_c[cv_mask]
                plt.plot(cv_cap, cv_current, label=f'Cycle {n}')
    
    plt.xlabel('Capacity (Ah)')
    plt.ylabel('Current (A)')
    plt.title('CV Current vs. Capacity')
    plt.legend()
    plt.grid(True)
    
    # Current vs. SOC
    plt.subplot(2, 2, 3)
    for n, _, _, i_c, _, phase_c, _, _, _, _, _, cv_start_soc in results:
        if n in selected_cycles:
            # Find CV phase
            cv_mask = (phase_c == 'CV')
            if np.any(cv_mask):
                soc_c = np.array([cv_start_soc + i for i in range(sum(cv_mask))])
                cv_current = i_c[cv_mask]
                plt.plot(soc_c, cv_current, label=f'Cycle {n}')
    
    plt.xlabel('SOC')
    plt.ylabel('Current (A)')
    plt.title('CV Current vs. SOC')
    plt.legend()
    plt.grid(True)
    
    # Current Decay Rate
    plt.subplot(2, 2, 4)
    for n, _, _, i_c, t_c, phase_c, _, _, _, cv_start_time, _, _ in results:
        if n in selected_cycles:
            # Find CV phase
            cv_mask = (phase_c == 'CV')
            if np.any(cv_mask) and sum(cv_mask) > 1:
                cv_time = t_c[cv_mask] - cv_start_time
                cv_current = i_c[cv_mask]
                
                # Calculate decay rate (dI/dt)
                decay_rate = np.diff(cv_current) / np.diff(cv_time)
                plt.plot(cv_time[:-1]/60, decay_rate, label=f'Cycle {n}')
    
    plt.xlabel('CV Phase Time (min)')
    plt.ylabel('Current Decay Rate (A/s)')
    plt.title('CV Current Decay Rate')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

if __name__=='__main__':
    # Run simulation with enhanced CV current tracking
    print("Running simulation with enhanced CV current tracking...")
    res = run_all_cycles(num_cycles=20, c_rate=0.5, end_current_ratio=0.05)
    
    # Plot charge and discharge curves
    plot_all_smoothed(res, smoothing_s=0.05)
    
    # Plot CV current profiles
    plot_cv_current_profiles(res, selected_cycles=[1, 5, 10, 15, 20])
    
    print("Simulation complete.")