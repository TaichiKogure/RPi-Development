#!/usr/bin/env python3
"""
battery_nmc_graphite_curves.py with resistance comparison (Interactive Version)

A tool for simulating charge and discharge curves of lithium-ion batteries with NMC (Nickel Manganese Cobalt) cathode and graphite anode.
This version demonstrates the effects of increased internal resistance on battery performance.

This interactive version is designed for use in IDEs and Jupyter Notebooks.
Instead of command-line arguments, parameters are set through interactive prompts.

Usage:
  Simply run the script and follow the prompts to input parameters.
  In Jupyter Notebook, you can run the script cell by cell.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter

# OCV-SOC table (SOC-OCV values from literature)
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

def plot_resistance_comparison(soc_charge_normal, cap_charge_normal, v_charge_normal,
                              soc_dis_normal, cap_dis_normal, v_dis_normal,
                              soc_charge_high, cap_charge_high, v_charge_high,
                              soc_dis_high, cap_dis_high, v_dis_high,
                              capacity_ah: float,
                              resistance_normal: float,
                              resistance_high: float,
                              smoothing_level: int = 5,
                              show: bool = True,
                              savefig_prefix: str | None = None):
    """
    Plot comparison graphs showing the effects of increased internal resistance.
    Apply smoothing to the voltage curves for better visualization.
    If savefig_prefix is specified, save as PNG files.
    """
    # Apply smoothing to voltage data
    v_charge_normal_smooth = apply_smoothing(v_charge_normal, smoothing_level)
    v_dis_normal_smooth = apply_smoothing(v_dis_normal, smoothing_level)
    v_charge_high_smooth = apply_smoothing(v_charge_high, smoothing_level)
    v_dis_high_smooth = apply_smoothing(v_dis_high, smoothing_level)
    
    # Voltage vs Capacity plot
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(cap_charge_normal, v_charge_normal_smooth, 
             label=f"Charge (R={resistance_normal}Ω)", color="tab:blue")
    ax1.plot(cap_dis_normal, v_dis_normal_smooth, 
             label=f"Discharge (R={resistance_normal}Ω)", color="tab:orange", linestyle="--")
    ax1.plot(cap_charge_high, v_charge_high_smooth, 
             label=f"Charge (R={resistance_high}Ω)", color="tab:green")
    ax1.plot(cap_dis_high, v_dis_high_smooth, 
             label=f"Discharge (R={resistance_high}Ω)", color="tab:red", linestyle="--")
    ax1.set_xlabel("Capacity (Ah)")
    ax1.set_ylabel("Terminal Voltage (V)")
    ax1.set_title("Effect of Internal Resistance on Voltage-Capacity Curves")
    ax1.grid(True)
    ax1.legend()
    if savefig_prefix:
        fig1.savefig(f"{savefig_prefix}_resistance_capacity.png", dpi=300, bbox_inches="tight")

    # Voltage vs SOC plot
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    ax2.plot(soc_charge_normal, v_charge_normal_smooth, 
             label=f"Charge (R={resistance_normal}Ω)", color="tab:blue")
    ax2.plot(soc_dis_normal, v_dis_normal_smooth, 
             label=f"Discharge (R={resistance_normal}Ω)", color="tab:orange", linestyle="--")
    ax2.plot(soc_charge_high, v_charge_high_smooth, 
             label=f"Charge (R={resistance_high}Ω)", color="tab:green")
    ax2.plot(soc_dis_high, v_dis_high_smooth, 
             label=f"Discharge (R={resistance_high}Ω)", color="tab:red", linestyle="--")
    ax2.set_xlabel("SOC (State of Charge)")
    ax2.set_ylabel("Terminal Voltage (V)")
    ax2.set_title("Effect of Internal Resistance on Voltage-SOC Curves")
    ax2.grid(True)
    ax2.legend()
    if savefig_prefix:
        fig2.savefig(f"{savefig_prefix}_resistance_soc.png", dpi=300, bbox_inches="tight")
    
    # Highlight the difference in usable capacity
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    ax3.plot(cap_dis_normal, v_dis_normal_smooth, 
             label=f"Discharge (R={resistance_normal}Ω)", color="tab:orange", linewidth=2)
    ax3.plot(cap_dis_high, v_dis_high_smooth, 
             label=f"Discharge (R={resistance_high}Ω)", color="tab:red", linewidth=2)
    
    # Add horizontal line at cutoff voltage
    v_min = 3.0519  # Minimum voltage
    ax3.axhline(y=v_min, color='gray', linestyle='--', alpha=0.7)
    ax3.text(0.02, v_min + 0.02, f"Cutoff voltage: {v_min}V", fontsize=9)
    
    # Find capacity at cutoff voltage
    cap_normal_at_cutoff = cap_dis_normal[np.argmin(np.abs(v_dis_normal_smooth - v_min))]
    cap_high_at_cutoff = cap_dis_high[np.argmin(np.abs(v_dis_high_smooth - v_min))]
    
    # Add vertical lines at cutoff capacities
    ax3.axvline(x=cap_normal_at_cutoff, color='tab:orange', linestyle=':', alpha=0.7)
    ax3.axvline(x=cap_high_at_cutoff, color='tab:red', linestyle=':', alpha=0.7)
    
    # Add capacity values
    ax3.text(cap_normal_at_cutoff + 0.02, 3.2, f"{cap_normal_at_cutoff:.2f} Ah", 
             color='tab:orange', fontsize=9)
    ax3.text(cap_high_at_cutoff + 0.02, 3.1, f"{cap_high_at_cutoff:.2f} Ah", 
             color='tab:red', fontsize=9)
    
    # Add capacity loss text
    capacity_loss = cap_normal_at_cutoff - cap_high_at_cutoff
    capacity_loss_percent = (capacity_loss / cap_normal_at_cutoff) * 100
    ax3.text(0.5, 3.4, f"Capacity loss due to increased resistance: {capacity_loss:.2f} Ah ({capacity_loss_percent:.1f}%)", 
             fontsize=10, ha='center', bbox=dict(facecolor='white', alpha=0.7))
    
    ax3.set_xlabel("Discharge Capacity (Ah)")
    ax3.set_ylabel("Terminal Voltage (V)")
    ax3.set_title("Impact of Internal Resistance on Usable Capacity")
    ax3.grid(True)
    ax3.legend()
    if savefig_prefix:
        fig3.savefig(f"{savefig_prefix}_capacity_loss.png", dpi=300, bbox_inches="tight")
    
    if show:
        plt.show()

def get_float_input(prompt, default_value, min_value=None, max_value=None):
    """Helper function to get float input with validation"""
    while True:
        try:
            user_input = input(f"{prompt} [{default_value}]: ").strip()
            if user_input == "":
                return default_value
            value = float(user_input)
            
            if min_value is not None and value < min_value:
                print(f"Value must be at least {min_value}. Using default: {default_value}")
                return default_value
            if max_value is not None and value > max_value:
                print(f"Value must be at most {max_value}. Using default: {default_value}")
                return default_value
                
            return value
        except ValueError:
            print(f"Invalid input. Please enter a number. Using default: {default_value}")
            return default_value

def get_int_input(prompt, default_value, min_value=None, max_value=None):
    """Helper function to get integer input with validation"""
    while True:
        try:
            user_input = input(f"{prompt} [{default_value}]: ").strip()
            if user_input == "":
                return default_value
            value = int(user_input)
            
            if min_value is not None and value < min_value:
                print(f"Value must be at least {min_value}. Using default: {default_value}")
                return default_value
            if max_value is not None and value > max_value:
                print(f"Value must be at most {max_value}. Using default: {default_value}")
                return default_value
                
            return value
        except ValueError:
            print(f"Invalid input. Please enter an integer. Using default: {default_value}")
            return default_value

def get_yes_no_input(prompt, default_value=True):
    """Helper function to get yes/no input"""
    default_str = "Y" if default_value else "N"
    while True:
        user_input = input(f"{prompt} (Y/N) [{default_str}]: ").strip().upper()
        if user_input == "":
            return default_value
        if user_input == "Y":
            return True
        if user_input == "N":
            return False
        print("Invalid input. Please enter Y or N.")

def main() -> None:
    """Interactive main function that prompts for parameters"""
    print("=== Battery Charge-Discharge Curve Simulator with Resistance Comparison (Interactive) ===")
    print("Please enter the following parameters (or press Enter for defaults):")
    
    # Get user inputs
    capacity = get_float_input("Battery capacity [Ah]", 3.0, min_value=0.1)
    charge_c_rate = get_float_input("Charge C-rate", 0.5, min_value=0.01)
    discharge_c_rate = get_float_input("Discharge C-rate", 0.5, min_value=0.01)
    resistance = get_float_input("Base internal resistance [Ω]", 0.05, min_value=0.001)
    resistance_factor = get_float_input("Resistance increase factor", 3.0, min_value=1.0)
    dt = get_float_input("Simulation time step [seconds]", 1.0, min_value=0.1)
    
    # Calculate high resistance value
    resistance_high = resistance * resistance_factor
    
    # Get smoothing level
    smoothing_level = get_int_input("Smoothing level (higher = smoother)", 5, min_value=3)
    
    # Ask about saving results
    save_results = get_yes_no_input("Save results as PNG files?", False)
    save_prefix = None
    if save_results:
        save_prefix = input("Enter prefix for saved files: ").strip()
        if save_prefix == "":
            save_prefix = "battery_resistance_comparison"
            print(f"Using default prefix: {save_prefix}")
    
    # Show graphs?
    show_graphs = get_yes_no_input("Display graphs?", True)
    
    print("\nRunning simulation with the following parameters:")
    print(f"- Battery capacity: {capacity} Ah")
    print(f"- Charge C-rate: {charge_c_rate}")
    print(f"- Discharge C-rate: {discharge_c_rate}")
    print(f"- Base internal resistance: {resistance} Ω")
    print(f"- Increased internal resistance: {resistance_high} Ω (factor: {resistance_factor})")
    print(f"- Time step: {dt} seconds")
    print(f"- Smoothing level: {smoothing_level}")
    print(f"- Save results: {save_results}")
    if save_results:
        print(f"- Save prefix: {save_prefix}")
    print(f"- Show graphs: {show_graphs}")
    
    print("\nRunning simulations...")
    
    # Simulate with normal resistance
    print("Simulating with normal resistance...")
    soc_chg_normal, cap_chg_normal, v_chg_normal = simulate_charge(
        capacity_ah=capacity,
        c_rate=charge_c_rate,
        resistance=resistance,
        dt_seconds=dt,
    )
    soc_dis_normal, cap_dis_normal, v_dis_normal = simulate_discharge(
        capacity_ah=capacity,
        c_rate=discharge_c_rate,
        resistance=resistance,
        dt_seconds=dt,
    )
    
    # Simulate with high resistance
    print("Simulating with increased resistance...")
    soc_chg_high, cap_chg_high, v_chg_high = simulate_charge(
        capacity_ah=capacity,
        c_rate=charge_c_rate,
        resistance=resistance_high,
        dt_seconds=dt,
    )
    soc_dis_high, cap_dis_high, v_dis_high = simulate_discharge(
        capacity_ah=capacity,
        c_rate=discharge_c_rate,
        resistance=resistance_high,
        dt_seconds=dt,
    )
    
    # Plot comparison
    print("Generating comparison plots...")
    plot_resistance_comparison(
        soc_chg_normal, cap_chg_normal, v_chg_normal,
        soc_dis_normal, cap_dis_normal, v_dis_normal,
        soc_chg_high, cap_chg_high, v_chg_high,
        soc_dis_high, cap_dis_high, v_dis_high,
        capacity_ah=capacity,
        resistance_normal=resistance,
        resistance_high=resistance_high,
        smoothing_level=smoothing_level,
        show=show_graphs,
        savefig_prefix=save_prefix
    )

if __name__ == "__main__":
    main()