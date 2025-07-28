import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, UnivariateSpline

# OCV-SOC lookup table (NMC/graphite)
soc_pts = np.array([0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0])
ocv_pts = np.array([3.0519,3.6594,3.7167,3.7611,3.7915,3.8275,
                    3.8772,3.9401,4.0128,4.0923,4.1797])
ocv_interp = interp1d(soc_pts, ocv_pts, kind='linear', fill_value='extrapolate')

def ocv_from_soc(soc):
    return float(ocv_interp(np.clip(soc,0.0,1.0)))

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
def capacity_after_cycle(n, Q0=3.0, A=0.1, B=0.005):
    return Q0 * (1 - A * (1 - np.exp(-B * n)))

def resistance_after_cycle(n, R0=0.05, C=0.005, D=1.0):
    return R0 * (1 + C * (n**D))

def run_cycles_degradation(num_cycles=50, c_rate=0.5):
    results_charge = []
    results_discharge = []
    for n in range(1, num_cycles+1):
        cap_n = capacity_after_cycle(n)
        res_n = resistance_after_cycle(n)
        soc_c, cap_c, v_c = simulate_charge(cap_n, c_rate, res_n)
        soc_d, cap_d, v_d = simulate_discharge(cap_n, c_rate, res_n)
        results_charge.append((n, cap_c, v_c))
        results_discharge.append((n, cap_d, v_d))
    return results_charge, results_discharge

def plot_degradation(results_charge, results_discharge):
    plt.figure(figsize=(10,5))

    # Discharge curves
    plt.subplot(1,2,1)
    for n, cap_d, v_d in results_discharge[::10]:
        plt.plot(cap_d, v_d, label=f'Discharge cycle {n}')
    cap_d_final, v_d_final = results_discharge[-1][1], results_discharge[-1][2]
    spl_d = UnivariateSpline(cap_d_final, v_d_final, s=0.001)
    xx_d = np.linspace(cap_d_final.min(), cap_d_final.max(), 500)
    plt.plot(xx_d, spl_d(xx_d), 'k--', lw=2, label='Smoothed final discharge')
    plt.xlabel('Capacity (Ah)')
    plt.ylabel('Voltage (V)')
    plt.title('Discharge with degradation')
    plt.legend(); plt.grid(True)

    # Charge curves
    plt.subplot(1,2,2)
    for n, cap_c, v_c in results_charge[::10]:
        plt.plot(cap_c, v_c, label=f'Charge cycle {n}')
    cap_c_final, v_c_final = results_charge[-1][1], results_charge[-1][2]
    spl_c = UnivariateSpline(cap_c_final, v_c_final, s=0.05)
    xx_c = np.linspace(cap_c_final.min(), cap_c_final.max(), 500)
    plt.plot(xx_c, spl_c(xx_c), 'k--', lw=2, label='Smoothed final charge')
    plt.xlabel('Capacity (Ah)')
    plt.ylabel('Voltage (V)')
    plt.title('Charge with degradation')
    plt.legend(); plt.grid(True)

    plt.tight_layout()
    plt.show()
if __name__ == '__main__':
    ch, dis = run_cycles_degradation(num_cycles=100, c_rate=0.5)
    plot_degradation(ch, dis)
