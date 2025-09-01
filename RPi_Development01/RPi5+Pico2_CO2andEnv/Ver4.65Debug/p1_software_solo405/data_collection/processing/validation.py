"""
Validation Module for Data Processing

This module contains functions for validating sensor data.
"""

import logging
import datetime

# Configure logging
logger = logging.getLogger(__name__)

def validate_data(data):
    """
    Validate the data received from a sensor node.
    
    Args:
        data (dict): The data to validate
        
    Returns:
        tuple: (is_valid, validated_data, error_message)
            - is_valid (bool): True if the data is valid, False otherwise
            - validated_data (dict): The validated data with any necessary conversions
            - error_message (str): Error message if validation fails, None otherwise
    """
    try:
        # Check if data is a dictionary
        if not isinstance(data, dict):
            return False, None, "Data is not a dictionary"
            
        # Check for required fields
        required_fields = ["device_id", "timestamp"]
        for field in required_fields:
            if field not in data:
                return False, None, f"Missing required field: {field}"
                
        # Check device_id
        if data["device_id"] not in ["P2", "P3"]:
            return False, None, f"Invalid device_id: {data['device_id']}"
            
        # Create a copy of the data for validation
        validated_data = data.copy()
        
        # Validate timestamp
        try:
            # If timestamp is a string, convert to datetime
            if isinstance(data["timestamp"], str):
                # Try to parse the timestamp
                timestamp = datetime.datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
                # Convert back to string in the standard format
                validated_data["timestamp"] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            # If timestamp is already a datetime object, convert to string
            elif isinstance(data["timestamp"], datetime.datetime):
                validated_data["timestamp"] = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            # If timestamp is a number (unix timestamp), convert to datetime then string
            elif isinstance(data["timestamp"], (int, float)):
                timestamp = datetime.datetime.fromtimestamp(data["timestamp"])
                validated_data["timestamp"] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                return False, None, f"Invalid timestamp format: {data['timestamp']}"
        except Exception as e:
            return False, None, f"Error parsing timestamp: {e}"
            
        # Validate sensor data fields
        sensor_fields = ["temperature", "humidity", "pressure", "gas_resistance", "co2"]
        for field in sensor_fields:
            if field in data:
                try:
                    # Convert to float if it's a string
                    if isinstance(data[field], str):
                        validated_data[field] = float(data[field])
                    # Keep as is if it's already a number
                    elif isinstance(data[field], (int, float)):
                        validated_data[field] = float(data[field])
                    else:
                        return False, None, f"Invalid {field} format: {data[field]}"
                        
                    # Check for valid ranges
                    if field == "temperature" and (validated_data[field] < -50 or validated_data[field] > 100):
                        logger.warning(f"Temperature out of normal range: {validated_data[field]}")
                    elif field == "humidity" and (validated_data[field] < 0 or validated_data[field] > 100):
                        logger.warning(f"Humidity out of normal range: {validated_data[field]}")
                    elif field == "pressure" and (validated_data[field] < 800 or validated_data[field] > 1200):
                        logger.warning(f"Pressure out of normal range: {validated_data[field]}")
                    elif field == "co2" and (validated_data[field] < 0 or validated_data[field] > 10000):
                        logger.warning(f"CO2 out of normal range: {validated_data[field]}")
                        
                except Exception as e:
                    return False, None, f"Error validating {field}: {e}"
                    
        # All validation passed
        return True, validated_data, None
        
    except Exception as e:
        logger.error(f"Error validating data: {e}")
        return False, None, f"Validation error: {e}"