#!/usr/bin/env python3
"""
battery_nmc_graphite_curves.py with Ah capacity display and smoothing

A tool for simulating charge and discharge curves of lithium-ion batteries with NMC (Nickel Manganese Cobalt) cathode and graphite anode.
This version displays capacity in Ah instead of SOC and includes curve smoothing functionality.

Usage:
  python Test01SAh.py [options]
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

def soc_to_ah(soc, capacity_ah):
    """Convert SOC (0-1) to absolute capacity in Ah"""
    return soc * capacity_ah

def plot_results_ah(soc_charge, cap_charge, v_charge,
                   soc_dis, cap_dis, v_dis,
                   capacity_ah: float,
                   smoothing_level: int = 5,
                   show: bool = True,
                   savefig_prefix: str | None = None):
    """
    Plot voltage vs absolute capacity (Ah) curves.
    Apply smoothing to the voltage curves for better visualization.
    If savefig_prefix is specified, save as PNG files.
    """
    # Apply smoothing to voltage data
    v_charge_smooth = apply_smoothing(v_charge, smoothing_level)
    v_dis_smooth = apply_smoothing(v_dis, smoothing_level)
    
    # Convert SOC to absolute capacity (Ah)
    ah_charge = soc_to_ah(soc_charge, capacity_ah)
    ah_dis = capacity_ah - soc_to_ah(soc_dis, capacity_ah)  # Invert for discharge
    
    # Create figure for voltage vs absolute capacity
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Plot charge curve
    ax.plot(ah_charge, v_charge_smooth, label="Charge", color="tab:blue")
    
    # Plot discharge curve
    ax.plot(ah_dis, v_dis_smooth, label="Discharge", color="tab:orange", linestyle="--")
    
    # Add annotations for capacity
    ax.axvline(x=capacity_ah, color='gray', linestyle=':', alpha=0.7)
    ax.text(capacity_ah + 0.02, 3.5, f"Rated Capacity: {capacity_ah} Ah", 
            fontsize=9, rotation=90, va='bottom')
    
    # Find actual charge capacity (where charge curve ends)
    actual_charge_capacity = ah_charge[-1]
    ax.text(actual_charge_capacity - 0.1, 4.0, f"Charge: {actual_charge_capacity:.2f} Ah", 
            fontsize=9, ha='right')
    
    # Find actual discharge capacity (where discharge curve ends)
    actual_discharge_capacity = ah_dis[-1]
    ax.text(actual_discharge_capacity + 0.1, 3.2, f"Discharge: {actual_discharge_capacity:.2f} Ah", 
            fontsize=9, ha='left')
    
    # Calculate and display coulombic efficiency
    coulombic_efficiency = (actual_discharge_capacity / actual_charge_capacity) * 100
    ax.text(capacity_ah / 2, 3.3, f"Coulombic Efficiency: {coulombic_efficiency:.1f}%", 
            fontsize=10, ha='center', bbox=dict(facecolor='white', alpha=0.7))
    
    ax.set_xlabel("Capacity (Ah)")
    ax.set_ylabel("Terminal Voltage (V)")
    ax.set_title("Voltage-Capacity Curve (NMC/Graphite Cell) - Absolute Capacity")
    ax.grid(True)
    ax.legend()
    
    # Set x-axis limits to show full capacity range
    max_capacity = max(actual_charge_capacity, actual_discharge_capacity, capacity_ah) * 1.1
    ax.set_xlim(0, max_capacity)
    
    if savefig_prefix:
        fig.savefig(f"{savefig_prefix}_ah_capacity.png", dpi=300, bbox_inches="tight")
    
    # Create figure for differential capacity analysis (dQ/dV)
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    
    # Calculate differential capacity for charge
    dv_charge = np.diff(v_charge_smooth)
    dq_charge = np.diff(ah_charge)
    dqdv_charge = np.zeros_like(dv_charge)
    mask_charge = (dv_charge != 0)
    dqdv_charge[mask_charge] = dq_charge[mask_charge] / dv_charge[mask_charge]
    v_charge_mid = (v_charge_smooth[1:] + v_charge_smooth[:-1]) / 2
    
    # Calculate differential capacity for discharge
    dv_dis = np.diff(v_dis_smooth)
    dq_dis = np.diff(ah_dis)
    dqdv_dis = np.zeros_like(dv_dis)
    mask_dis = (dv_dis != 0)
    dqdv_dis[mask_dis] = dq_dis[mask_dis] / dv_dis[mask_dis]
    v_dis_mid = (v_dis_smooth[1:] + v_dis_smooth[:-1]) / 2
    
    # Apply additional smoothing to dQ/dV curves
    dqdv_charge_smooth = apply_smoothing(dqdv_charge, smoothing_level * 2)
    dqdv_dis_smooth = apply_smoothing(dqdv_dis, smoothing_level * 2)
    
    # Plot dQ/dV curves
    ax2.plot(v_charge_mid, dqdv_charge_smooth, label="Charge", color="tab:blue")
    ax2.plot(v_dis_mid, -dqdv_dis_smooth, label="Discharge", color="tab:orange", linestyle="--")
    
    ax2.set_xlabel("Voltage (V)")
    ax2.set_ylabel("Differential Capacity (Ah/V)")
    ax2.set_title("Differential Capacity Analysis (dQ/dV)")
    ax2.grid(True)
    ax2.legend()
    
    if savefig_prefix:
        fig2.savefig(f"{savefig_prefix}_dqdv.png", dpi=300, bbox_inches="tight")
    
    if show:
        plt.show()

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Simulate charge-discharge curves with absolute capacity (Ah) display")
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
    plot_results_ah(soc_chg, cap_chg, v_chg, soc_dis, cap_dis, v_dis,
                   capacity_ah=args.capacity,
                   smoothing_level=args.smoothing,
                   show=not args.no_show,
                   savefig_prefix=args.save_prefix)

if __name__ == "__main__":
    main()