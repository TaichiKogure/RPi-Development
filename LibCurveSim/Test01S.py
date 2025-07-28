#!/usr/bin/env python3
"""
battery_nmc_graphite_curves.py with smoothing functionality

A tool for simulating charge and discharge curves of lithium-ion batteries with NMC (Nickel Manganese Cobalt) cathode and graphite anode.
The OCV-SOC table uses values published in the literature referenced as contentReference[oaicite:1]{index=1}.
This version includes curve smoothing functionality for better visualization.

Usage:
  python Test01S.py [options]
Main options:
  --capacity        Battery capacity [Ah] (default: 3.0)
  --charge_c_rate   Charge C-rate (default: 0.5)
  --discharge_c_rate Discharge C-rate (default: 0.5)
  --resistance      Internal resistance [Ω] (default: 0.05)
  --dt              Simulation time step [seconds] (default: 1)
  --smoothing       Smoothing level (default: 5, higher = smoother)
  --save_prefix     Prefix for saving results as PNG files
  --no_show         Save results without displaying graphs
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter

# OCV-SOC table (SOC-OCV values from Table 2:contentReference[oaicite:2]{index=2})
_soc_points = np.array([0.0, 0.1, 0.2, 0.3, 0.4,
                        0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
_ocv_points = np.array([3.0519, 3.6594, 3.7167, 3.7611, 3.7915,
                        3.8275, 3.8772, 3.9401, 4.0128, 4.0923, 4.1797])
_ocv_interp = interp1d(_soc_points, _ocv_points, kind="linear",
                      fill_value="extrapolate")

def ocv_from_soc(soc: float) -> float:
    """Calculate open circuit voltage from SOC. SOC is limited to the range 0-1."""
    return float(_ocv_interp(np.clip(soc, 0.0, 1.0)))

def simulate_charge(capacity_ah: float = 3.0,
                    c_rate: float = 0.5,
                    resistance: float = 0.05,
                    v_max: float = 4.1797,
                    end_current_ratio: float = 0.05,
                    dt_seconds: float = 1.0):
    """
    Simulate constant current/constant voltage charging.
    Constant current charging until v_max is reached, then constant voltage
    charging until the terminal current drops below end_current_ratio times
    the initial current.

    Returns: SOC array, charged capacity array (Ah), voltage array (V)
    """
    dt_hours = dt_seconds / 3600.0
    I0 = c_rate * capacity_ah
    soc = 0.0
    delivered_capacity = 0.0
    soc_history = [soc]
    cap_history = [delivered_capacity]
    volt_history = [ocv_from_soc(soc)]

    # Constant current phase
    I = I0
    while soc < 1.0:
        ocv = ocv_from_soc(soc)
        terminal_v = ocv + I * resistance
        if terminal_v >= v_max:
            break
        soc += (I * dt_hours) / capacity_ah
        delivered_capacity += I * dt_hours
        soc_history.append(soc)
        cap_history.append(delivered_capacity)
        volt_history.append(terminal_v)

    # Constant voltage phase
    while soc < 1.0:
        ocv = ocv_from_soc(soc)
        I = max((v_max - ocv) / resistance, 0.0)
        if I <= end_current_ratio * I0:
            break
        soc += (I * dt_hours) / capacity_ah
        delivered_capacity += I * dt_hours
        soc_history.append(soc)
        cap_history.append(delivered_capacity)
        volt_history.append(v_max)
    return np.array(soc_history), np.array(cap_history), np.array(volt_history)

def simulate_discharge(capacity_ah: float = 3.0,
                       c_rate: float = 0.5,
                       resistance: float = 0.05,
                       v_min: float = 3.0519,
                       dt_seconds: float = 1.0):
    """
    Simulate constant current discharge.
    Starting from SOC=1.0, discharge continues until terminal voltage
    falls below v_min or SOC reaches 0.

    Returns: SOC array, discharged capacity array (Ah), voltage array (V)
    """
    dt_hours = dt_seconds / 3600.0
    I = c_rate * capacity_ah
    soc = 1.0
    delivered_capacity = 0.0
    soc_history = [soc]
    cap_history = [delivered_capacity]
    volt_history = [ocv_from_soc(soc)]
    while soc > 0.0:
        ocv = ocv_from_soc(soc)
        terminal_v = ocv - I * resistance
        if terminal_v <= v_min:
            break
        soc -= (I * dt_hours) / capacity_ah
        delivered_capacity += I * dt_hours
        soc_history.append(soc)
        cap_history.append(delivered_capacity)
        volt_history.append(terminal_v)
        if soc <= 0.0:
            break
    return np.array(soc_history), np.array(cap_history), np.array(volt_history)

def apply_smoothing(data, smoothing_level=5):
    """
    Apply Savitzky-Golay filter to smooth the data.
    
    Parameters:
    - data: Array of data to smooth
    - smoothing_level: Controls smoothing intensity (higher = smoother)
                      Must be odd and >= 3
    
    Returns: Smoothed data array
    """
    if len(data) < 10:  # Not enough data points for smoothing
        return data
    
    # Ensure smoothing_level is odd and at least 3
    smoothing_level = max(3, smoothing_level)
    if smoothing_level % 2 == 0:
        smoothing_level += 1
    
    # Window length must be less than data length
    window_length = min(len(data) - 1, smoothing_level * 2 + 1)
    if window_length % 2 == 0:  # Window length must be odd
        window_length -= 1
    
    if window_length < 3:  # Not enough points for smoothing
        return data
    
    # Apply Savitzky-Golay filter
    # polynomial order = 2 (quadratic)
    return savgol_filter(data, window_length, 2)

def plot_results(soc_charge, cap_charge, v_charge,
                 soc_dis, cap_dis, v_dis,
                 capacity_ah: float,
                 smoothing_level: int = 5,
                 show: bool = True,
                 savefig_prefix: str | None = None):
    """
    Plot two types of graphs: voltage vs capacity and voltage vs SOC.
    Apply smoothing to the voltage curves for better visualization.
    If savefig_prefix is specified, save as PNG files.
    """
    # Apply smoothing to voltage data
    v_charge_smooth = apply_smoothing(v_charge, smoothing_level)
    v_dis_smooth = apply_smoothing(v_dis, smoothing_level)
    
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(cap_charge, v_charge_smooth, label="Charge", color="tab:blue")
    ax1.plot(cap_dis, v_dis_smooth, label="Discharge", color="tab:orange", linestyle="--")
    ax1.set_xlabel("Capacity (Ah)")
    ax1.set_ylabel("Terminal Voltage (V)")
    ax1.set_title("Voltage-Capacity Curve (NMC/Graphite Cell) - Smoothed")
    ax1.grid(True)
    ax1.legend()
    if savefig_prefix:
        fig1.savefig(f"{savefig_prefix}_capacity_smooth.png", dpi=300, bbox_inches="tight")

    fig2, ax2 = plt.subplots(figsize=(8, 4))
    ax2.plot(soc_charge, v_charge_smooth, label="Charge", color="tab:blue")
    ax2.plot(soc_dis, v_dis_smooth, label="Discharge", color="tab:orange", linestyle="--")
    ax2.set_xlabel("SOC (State of Charge)")
    ax2.set_ylabel("Terminal Voltage (V)")
    ax2.set_title("Voltage-SOC Curve (NMC/Graphite Cell) - Smoothed")
    ax2.grid(True)
    ax2.legend()
    if savefig_prefix:
        fig2.savefig(f"{savefig_prefix}_soc_smooth.png", dpi=300, bbox_inches="tight")
    if show:
        plt.show()

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Simulate charge-discharge curves for NMC/Graphite cells with smoothing")
    parser.add_argument("--capacity", type=float, default=3.0, help="Battery capacity [Ah]")
    parser.add_argument("--charge_c_rate", type=float, default=0.5, help="Charge C-rate")
    parser.add_argument("--discharge_c_rate", type=float, default=0.5, help="Discharge C-rate")
    parser.add_argument("--resistance", type=float, default=0.05, help="Internal resistance [Ω]")
    parser.add_argument("--dt", type=float, default=1.0, help="Time step [seconds]")
    parser.add_argument("--smoothing", type=int, default=5, help="Smoothing level (higher = smoother)")
    parser.add_argument("--no_show", action="store_true", help="Save without displaying")
    parser.add_argument("--save_prefix", type=str, default=None, help="Prefix for result files")
    args = parser.parse_args()

    soc_chg, cap_chg, v_chg = simulate_charge(
        capacity_ah=args.capacity,
        c_rate=args.charge_c_rate,
        resistance=args.resistance,
        dt_seconds=args.dt,
    )
    soc_dis, cap_dis, v_dis = simulate_discharge(
        capacity_ah=args.capacity,
        c_rate=args.discharge_c_rate,
        resistance=args.resistance,
        dt_seconds=args.dt,
    )
    plot_results(soc_chg, cap_chg, v_chg, soc_dis, cap_dis, v_dis,
                 capacity_ah=args.capacity,
                 smoothing_level=args.smoothing,
                 show=not args.no_show,
                 savefig_prefix=args.save_prefix)

if __name__ == "__main__":
    main()