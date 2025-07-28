import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, UnivariateSpline

# OCV-SOC lookup from literature (NMC/graphite)
soc_pts = np.array([0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0])
ocv_pts = np.array([3.0519,3.6594,3.7167,3.7611,3.7915,3.8275,
                    3.8772,3.9401,4.0128,4.0923,4.1797])
ocv_interp = interp1d(soc_pts, ocv_pts, kind='linear', fill_value='extrapolate')

def ocv_from_soc(soc):
    return float(ocv_interp(np.clip(soc,0.0,1.0)))

def simulate_charge(cap_ah, c_rate, resistance, v_max=4.1797, end_current_ratio=0.05, dt=1.0):
    dt_h = dt/3600.0
    I0 = c_rate * cap_ah
    soc = 0.0
    charged = 0.0
    soc_hist, cap_hist, v_hist = [soc], [0.0], [ocv_from_soc(soc)]
    I = I0
    while soc<1.0:
        V_oc = ocv_from_soc(soc)
        V_term = V_oc + I * resistance
        if V_term >= v_max: break
        soc += (I * dt_h)/cap_ah
        charged += I * dt_h
        soc_hist.append(soc); cap_hist.append(charged); v_hist.append(V_term)
    while soc<1.0:
        V_oc = ocv_from_soc(soc)
        I = max((v_max - V_oc)/resistance, 0.0)
        if I <= end_current_ratio * I0: break
        soc += (I * dt_h)/cap_ah
        charged += I * dt_h
        soc_hist.append(soc); cap_hist.append(charged); v_hist.append(V_oc + I*resistance)
    return np.array(soc_hist), np.array(cap_hist), np.array(v_hist)

def simulate_discharge(cap_ah, c_rate, resistance, v_min=3.0519, dt=1.0):
    dt_h = dt/3600.0
    I = c_rate * cap_ah
    soc = 1.0
    discharged = 0.0
    soc_hist, cap_hist, v_hist = [soc], [0.0], [ocv_from_soc(soc)]
    while soc>0.0:
        V_oc = ocv_from_soc(soc)
        V_term = V_oc - I * resistance
        if V_term <= v_min: break
        soc -= (I * dt_h)/cap_ah
        discharged += I * dt_h
        soc_hist.append(soc); cap_hist.append(discharged); v_hist.append(V_term)
    return np.array(soc_hist), np.array(cap_hist), np.array(v_hist)

# degradation models
def capacity_after_cycle(n, Q0=3.0, A=0.1, B=0.005):
    return Q0 * (1 - A * (1 - np.exp(-B * n)))

def resistance_after_cycle(n, R0=0.05, C=0.005, D=1.0):
    return R0 * (1 + C * (n**D))

def run_degradation_cycles(num_cycles=50, c_rate=0.5):
    results = []
    for n in range(1, num_cycles+1):
        Qn = capacity_after_cycle(n)
        Rn = resistance_after_cycle(n)
        soc_d, cap_d, v_d = simulate_discharge(Qn, c_rate, Rn)
        results.append((n, cap_d, v_d))
    return results

def plot_degradation(results):
    plt.figure(figsize=(8,5))
    for n, cap_d, v_d in results[::10]:
        plt.plot(cap_d, v_d, label=f'Cycle {n}')
    # smooth final cycle
    cap_final, v_final = results[-1][1], results[-1][2]
    spl = UnivariateSpline(cap_final, v_final, s=0.001)
    xx = np.linspace(cap_final.min(), cap_final.max(), 500)
    plt.plot(xx, spl(xx), 'k--', lw=2, label='Smoothed final')
    plt.xlabel('Discharged Capacity (Ah)')
    plt.ylabel('Terminal Voltage (V)')
    plt.title('Discharge curves with capacity fade & resistance growth')
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__=='__main__':
    res = run_degradation_cycles(num_cycles=100, c_rate=0.5)
    plot_degradation(res)
