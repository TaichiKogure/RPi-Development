"""
Calculation Module for Data Processing

This module contains functions for calculating derived values from sensor data.
"""

import math
import logging

# Configure logging
logger = logging.getLogger(__name__)

def calculate_absolute_humidity(temperature, humidity):
    """
    Calculate absolute humidity from temperature and relative humidity.
    
    Args:
        temperature (float): Temperature in Celsius
        humidity (float): Relative humidity as a percentage (0-100)
        
    Returns:
        float: Absolute humidity in g/m³, rounded to 2 decimal places
    """
    try:
        # Validate inputs
        if temperature is None or humidity is None:
            return None
            
        # Convert to float if they're strings
        if isinstance(temperature, str):
            temperature = float(temperature)
        if isinstance(humidity, str):
            humidity = float(humidity)
            
        # Check for valid ranges
        if temperature < -273.15 or humidity < 0 or humidity > 100:
            logger.warning(f"Invalid values for absolute humidity calculation: temp={temperature}, humidity={humidity}")
            return None
            
        # Calculate saturation vapor pressure
        # Magnus formula: https://en.wikipedia.org/wiki/Clausius%E2%80%93Clapeyron_relation#Meteorology_and_climatology
        saturation_vapor_pressure = 6.112 * math.exp((17.67 * temperature) / (temperature + 243.5))
        
        # Calculate vapor pressure
        vapor_pressure = saturation_vapor_pressure * (humidity / 100.0)
        
        # Calculate absolute humidity
        # Formula: https://carnotcycle.wordpress.com/2012/08/04/how-to-convert-relative-humidity-to-absolute-humidity/
        absolute_humidity = (vapor_pressure * 18.02) / ((273.15 + temperature) * 0.08314)
        
        # Round to 2 decimal places
        return round(absolute_humidity, 2)
        
    except Exception as e:
        logger.error(f"Error calculating absolute humidity: {e}")
        return None