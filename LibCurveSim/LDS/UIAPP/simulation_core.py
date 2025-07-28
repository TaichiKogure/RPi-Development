"""
Simulation Core Module

This module provides the core simulation functionality for the battery simulation and analysis tool.
It implements the simulation of battery charge/discharge cycles and degradation.
"""

import numpy as np
from scipy.interpolate import interp1d, UnivariateSpline

# OCV-SOC table from literature (same as in LibDegradationSim03.py)
SOC_POINTS = np.linspace(0, 1, 11)
OCV_POINTS = np.array([3.0519, 3.6594, 3.7167, 3.7611, 3.7915, 3.8275,
                       3.8772, 3.9401, 4.0128, 4.0923, 4.1797])


class SimulationCore:
    """
    Core class for battery simulation.
    """
    
    def __init__(self):
        """Initialize the simulation core."""
        # Initialize OCV-SOC interpolation
        self.ocv_interp = interp1d(SOC_POINTS, OCV_POINTS, kind='linear', fill_value='extrapolate')
        
        # Initialize parameters with default values
        self.initial_capacity = 3.0  # Ah
        self.c_rate = 0.5  # C
        self.initial_resistance = 0.05  # Ohm
        
        self.capacity_degradation_a = 0.1
        self.capacity_degradation_b = 0.05
        self.resistance_increase_c = 0.05
        self.resistance_increase_d = 1.0
        
        self.num_cycles = 50
        self.time_step = 1.0  # seconds
        self.v_max = 4.1797  # V
        self.v_min = 3.0519  # V
        self.end_current_ratio = 0.05
    
    def set_battery_params(self, initial_capacity, c_rate, initial_resistance):
        """
        Set battery parameters.
        
        Args:
            initial_capacity: Initial capacity in Ah
            c_rate: C-rate for charge/discharge
            initial_resistance: Initial internal resistance in Ohm
        """
        self.initial_capacity = initial_capacity
        self.c_rate = c_rate
        self.initial_resistance = initial_resistance
    
    def set_degradation_params(self, capacity_degradation_a, capacity_degradation_b,
                              resistance_increase_c, resistance_increase_d):
        """
        Set degradation parameters.
        
        Args:
            capacity_degradation_a: Capacity degradation parameter A
            capacity_degradation_b: Capacity degradation parameter B
            resistance_increase_c: Resistance increase parameter C
            resistance_increase_d: Resistance increase parameter D
        """
        self.capacity_degradation_a = capacity_degradation_a
        self.capacity_degradation_b = capacity_degradation_b
        self.resistance_increase_c = resistance_increase_c
        self.resistance_increase_d = resistance_increase_d
    
    def set_simulation_params(self, num_cycles, time_step=1.0, v_max=4.1797, v_min=3.0519,
                             end_current_ratio=0.05):
        """
        Set simulation parameters.
        
        Args:
            num_cycles: Number of cycles to simulate
            time_step: Time step in seconds
            v_max: Maximum voltage
            v_min: Minimum voltage
            end_current_ratio: End current ratio for CV phase
        """
        self.num_cycles = num_cycles
        self.time_step = time_step
        self.v_max = v_max
        self.v_min = v_min
        self.end_current_ratio = end_current_ratio
    
    def ocv_from_soc(self, soc):
        """
        Get OCV from SOC.
        
        Args:
            soc: State of charge (0-1)
            
        Returns:
            Open circuit voltage
        """
        return float(self.ocv_interp(np.clip(soc, 0.0, 1.0)))
    
    def simulate_charge(self, capacity, resistance):
        """
        Simulate charging process.
        
        Args:
            capacity: Current capacity in Ah
            resistance: Current internal resistance in Ohm
            
        Returns:
            Tuple of (SOC history, capacity history, voltage history)
        """
        dt_h = self.time_step / 3600.0
        I0 = self.c_rate * capacity
        soc = 0.0
        charged = 0.0
        soc_hist, cap_hist, v_hist = [soc], [0.0], [self.ocv_from_soc(soc)]
        I = I0
        
        # CC phase
        while soc < 1.0:
            V_oc = self.ocv_from_soc(soc)
            V_term = V_oc + I * resistance
            if V_term >= self.v_max:
                break
            soc += (I * dt_h) / capacity
            charged += I * dt_h
            soc_hist.append(soc)
            cap_hist.append(charged)
            v_hist.append(V_term)
        
        # CV phase
        while soc < 1.0:
            V_oc = self.ocv_from_soc(soc)
            I = max((self.v_max - V_oc) / resistance, 0.0)
            if I <= self.end_current_ratio * I0:
                break
            soc += (I * dt_h) / capacity
            charged += I * dt_h
            soc_hist.append(soc)
            cap_hist.append(charged)
            v_hist.append(V_oc + I * resistance)
        
        return np.array(soc_hist), np.array(cap_hist), np.array(v_hist)
    
    def simulate_discharge(self, capacity, resistance):
        """
        Simulate discharging process.
        
        Args:
            capacity: Current capacity in Ah
            resistance: Current internal resistance in Ohm
            
        Returns:
            Tuple of (SOC history, capacity history, voltage history)
        """
        dt_h = self.time_step / 3600.0
        I = self.c_rate * capacity
        soc = 1.0
        discharged = 0.0
        soc_hist, cap_hist, v_hist = [soc], [0.0], [self.ocv_from_soc(soc)]
        
        while soc > 0.0:
            V_oc = self.ocv_from_soc(soc)
            V_term = V_oc - I * resistance
            if V_term <= self.v_min:
                break
            soc -= (I * dt_h) / capacity
            discharged += I * dt_h
            soc_hist.append(soc)
            cap_hist.append(discharged)
            v_hist.append(V_term)
        
        return np.array(soc_hist), np.array(cap_hist), np.array(v_hist)
    
    def capacity_after_cycle(self, n):
        """
        Calculate capacity after n cycles.
        
        Args:
            n: Cycle number
            
        Returns:
            Capacity in Ah
        """
        return self.initial_capacity * (1 - self.capacity_degradation_a * 
                                       (1 - np.exp(-self.capacity_degradation_b * n)))
    
    def resistance_after_cycle(self, n):
        """
        Calculate resistance after n cycles.
        
        Args:
            n: Cycle number
            
        Returns:
            Resistance in Ohm
        """
        return self.initial_resistance * (1 + self.resistance_increase_c * (n**self.resistance_increase_d))
    
    def run_simulation(self):
        """
        Run the simulation for the specified number of cycles.
        
        Returns:
            List of simulation results for each cycle
        """
        results = []
        
        for n in range(1, self.num_cycles + 1):
            # Calculate capacity and resistance for this cycle
            capacity = self.capacity_after_cycle(n)
            resistance = self.resistance_after_cycle(n)
            
            # Simulate charge and discharge
            soc_c, cap_c, v_c = self.simulate_charge(capacity, resistance)
            soc_d, cap_d, v_d = self.simulate_discharge(capacity, resistance)
            
            # Calculate capacity retention
            capacity_retention = capacity / self.initial_capacity
            
            # Store results
            results.append({
                'cycle': n,
                'capacity': capacity,
                'resistance': resistance,
                'capacity_retention': capacity_retention,
                'charge': {
                    'soc': soc_c,
                    'capacity': cap_c,
                    'voltage': v_c
                },
                'discharge': {
                    'soc': soc_d,
                    'capacity': cap_d,
                    'voltage': v_d
                }
            })
        
        return results
    
    def smooth_curve(self, capacity, voltage, smoothing=0.001):
        """
        Smooth a capacity-voltage curve.
        
        Args:
            capacity: Capacity array
            voltage: Voltage array
            smoothing: Smoothing parameter
            
        Returns:
            Tuple of (smoothed capacity, smoothed voltage)
        """
        spl = UnivariateSpline(capacity, voltage, s=smoothing)
        xs = np.linspace(capacity.min(), capacity.max(), 400)
        ys = spl(xs)
        return xs, ys