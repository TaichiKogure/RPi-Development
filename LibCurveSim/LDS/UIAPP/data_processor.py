"""
Data Processor Module

This module provides data processing functionality for the battery simulation and analysis tool.
It implements dQ/dV curve calculation and peak detection.
"""

import numpy as np
from scipy.interpolate import UnivariateSpline
from scipy.signal import find_peaks, savgol_filter


class DataProcessor:
    """
    Class for data processing.
    """
    
    def __init__(self):
        """Initialize the data processor."""
        pass
    
    def calculate_dqdv(self, voltage, capacity, smoothing=0.001, filter_window=None):
        """
        Calculate dQ/dV curve from voltage and capacity data.
        
        Args:
            voltage: Voltage array
            capacity: Capacity array
            smoothing: Smoothing parameter for spline
            filter_window: Window size for Savitzky-Golay filter (None for no filtering)
            
        Returns:
            Dictionary with voltage and dQ/dV arrays
        """
        # Sort data by voltage (important for discharge curves where voltage decreases)
        sort_idx = np.argsort(voltage)
        voltage_sorted = voltage[sort_idx]
        capacity_sorted = capacity[sort_idx]
        
        # Remove duplicate voltage points (can cause issues with spline)
        unique_idx = np.concatenate(([True], np.diff(voltage_sorted) != 0))
        voltage_unique = voltage_sorted[unique_idx]
        capacity_unique = capacity_sorted[unique_idx]
        
        # Create a spline of capacity vs voltage
        spl = UnivariateSpline(voltage_unique, capacity_unique, s=smoothing)
        
        # Create a fine voltage grid
        v_min, v_max = voltage_unique.min(), voltage_unique.max()
        v_grid = np.linspace(v_min, v_max, 1000)
        
        # Calculate derivative (dQ/dV)
        dqdv = spl.derivative()(v_grid)
        
        # Apply Savitzky-Golay filter if requested
        if filter_window is not None:
            # Window size must be odd and greater than 2
            window_size = max(3, filter_window if filter_window % 2 == 1 else filter_window + 1)
            dqdv = savgol_filter(dqdv, window_size, 2)
        
        return {
            'voltage': v_grid,
            'dqdv': dqdv
        }
    
    def detect_peaks(self, voltage, dqdv, prominence=0.1, width=None, height=None, 
                    distance=None, voltage_range=None):
        """
        Detect peaks in dQ/dV curve.
        
        Args:
            voltage: Voltage array
            dqdv: dQ/dV array
            prominence: Minimum peak prominence
            width: Minimum peak width
            height: Minimum peak height
            distance: Minimum distance between peaks
            voltage_range: Tuple of (min_voltage, max_voltage) to limit peak detection
            
        Returns:
            Dictionary with peak information
        """
        # Apply voltage range filter if specified
        if voltage_range is not None:
            v_min, v_max = voltage_range
            mask = (voltage >= v_min) & (voltage <= v_max)
            voltage_filtered = voltage[mask]
            dqdv_filtered = dqdv[mask]
        else:
            voltage_filtered = voltage
            dqdv_filtered = dqdv
        
        # Find peaks
        peaks, properties = find_peaks(
            dqdv_filtered,
            prominence=prominence,
            width=width,
            height=height,
            distance=distance
        )
        
        # Extract peak information
        peak_voltages = voltage_filtered[peaks] if len(peaks) > 0 else np.array([])
        peak_dqdvs = dqdv_filtered[peaks] if len(peaks) > 0 else np.array([])
        prominences = properties['prominences'] if len(peaks) > 0 else np.array([])
        widths = properties['widths'] if len(peaks) > 0 else np.array([])
        
        return {
            'peak_indices': peaks,
            'peak_voltages': peak_voltages,
            'peak_dqdvs': peak_dqdvs,
            'prominences': prominences,
            'widths': widths
        }
    
    def interpolate_to_grid(self, voltage, dqdv, voltage_grid):
        """
        Interpolate dQ/dV data to a common voltage grid.
        
        Args:
            voltage: Voltage array
            dqdv: dQ/dV array
            voltage_grid: Target voltage grid
            
        Returns:
            Interpolated dQ/dV array
        """
        # Interpolate dQ/dV to the voltage grid
        dqdv_interp = np.interp(
            voltage_grid,
            voltage,
            dqdv,
            left=0,
            right=0
        )
        
        return dqdv_interp
    
    def normalize_data(self, data):
        """
        Normalize data to [0, 1] range.
        
        Args:
            data: Data array
            
        Returns:
            Normalized data array
        """
        data_min = np.min(data)
        data_max = np.max(data)
        
        if data_max > data_min:
            return (data - data_min) / (data_max - data_min)
        else:
            return np.zeros_like(data)
    
    def standardize_data(self, data):
        """
        Standardize data to zero mean and unit variance.
        
        Args:
            data: Data array
            
        Returns:
            Standardized data array
        """
        data_mean = np.mean(data)
        data_std = np.std(data)
        
        if data_std > 0:
            return (data - data_mean) / data_std
        else:
            return np.zeros_like(data)
    
    def calculate_absolute_humidity(self, temperature, relative_humidity):
        """
        Calculate absolute humidity from temperature and relative humidity.
        
        Args:
            temperature: Temperature in Celsius
            relative_humidity: Relative humidity in percentage (0-100)
            
        Returns:
            Absolute humidity in g/m³
        """
        # Convert relative humidity to fraction
        rh_fraction = relative_humidity / 100.0
        
        # Calculate saturation vapor pressure (hPa)
        # Magnus formula
        svp = 6.1078 * 10**((7.5 * temperature) / (237.3 + temperature))
        
        # Calculate vapor pressure (hPa)
        vp = svp * rh_fraction
        
        # Calculate absolute humidity (g/m³)
        # Formula: AH = 216.7 * VP / (273.15 + T)
        abs_humidity = 216.7 * vp / (273.15 + temperature)
        
        return abs_humidity
    
    def calculate_capacity_retention(self, capacities, initial_capacity=None):
        """
        Calculate capacity retention from capacity data.
        
        Args:
            capacities: Array of capacities
            initial_capacity: Initial capacity (if None, use the first capacity)
            
        Returns:
            Array of capacity retention values
        """
        if initial_capacity is None and len(capacities) > 0:
            initial_capacity = capacities[0]
        
        if initial_capacity is not None and initial_capacity > 0:
            return capacities / initial_capacity
        else:
            return np.ones_like(capacities)
    
    def calculate_degradation_rate(self, capacity_retention, cycles):
        """
        Calculate degradation rate from capacity retention data.
        
        Args:
            capacity_retention: Array of capacity retention values
            cycles: Array of cycle numbers
            
        Returns:
            Array of degradation rates (% per cycle)
        """
        if len(capacity_retention) < 2 or len(cycles) < 2:
            return np.zeros_like(capacity_retention)
        
        # Calculate degradation rate (% per cycle)
        degradation_rate = np.zeros_like(capacity_retention)
        
        for i in range(1, len(capacity_retention)):
            delta_capacity = capacity_retention[i-1] - capacity_retention[i]
            delta_cycles = cycles[i] - cycles[i-1]
            
            if delta_cycles > 0:
                degradation_rate[i] = (delta_capacity / capacity_retention[i-1]) * 100 / delta_cycles
            else:
                degradation_rate[i] = 0
        
        return degradation_rate