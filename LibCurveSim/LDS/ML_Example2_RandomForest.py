import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, UnivariateSpline
import os
import csv
import glob
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import matplotlib.cm as cm

# Try to import pandas for easier data handling
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

def find_csv_files(directory="results", pattern="*dqdv*.csv"):
    """Find all CSV files matching the pattern in the directory"""
    return glob.glob(os.path.join(directory, pattern))

def find_capacity_files(directory="results", pattern="*capacity*.csv"):
    """Find capacity retention data files"""
    return glob.glob(os.path.join(directory, pattern))

def load_dqdv_data(file_path):
    """Load dQ/dV data from a CSV file"""
    if PANDAS_AVAILABLE:
        try:
            df = pd.read_csv(file_path)
            # Check if the file has the expected columns
            if 'Voltage' in df.columns and 'dQ/dV' in df.columns:
                return df['Voltage'].values, df['dQ/dV'].values
            else:
                print(f"Warning: File {file_path} does not have expected columns.")
                return None, None
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None, None
    else:
        # Fallback to basic CSV reading
        voltages = []
        dqdvs = []
        try:
            with open(file_path, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)
                voltage_idx = header.index('Voltage')
                dqdv_idx = header.index('dQ/dV')
                
                for row in reader:
                    try:
                        voltage = float(row[voltage_idx])
                        dqdv = float(row[dqdv_idx])
                        voltages.append(voltage)
                        dqdvs.append(dqdv)
                    except (ValueError, IndexError):
                        continue
            
            return np.array(voltages), np.array(dqdvs)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None, None

def load_capacity_data(file_path):
    """Load capacity retention data from a CSV file"""
    if PANDAS_AVAILABLE:
        try:
            df = pd.read_csv(file_path)
            # Check if the file has the expected columns
            if 'Cycle' in df.columns and 'Capacity_Retention' in df.columns:
                return df['Cycle'].values, df['Capacity_Retention'].values
            else:
                print(f"Warning: File {file_path} does not have expected columns.")
                return None, None
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None, None
    else:
        # Fallback to basic CSV reading
        cycles = []
        retentions = []
        try:
            with open(file_path, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)
                cycle_idx = header.index('Cycle')
                retention_idx = header.index('Capacity_Retention')
                
                for row in reader:
                    try:
                        cycle = int(row[cycle_idx])
                        retention = float(row[retention_idx])
                        cycles.append(cycle)
                        retentions.append(retention)
                    except (ValueError, IndexError):
                        continue
            
            return np.array(cycles), np.array(retentions)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None, None

def interpolate_to_common_grid(voltage_arrays, dqdv_arrays, v_min=3.0, v_max=4.2, num_points=100):
    """Interpolate all dQ/dV curves to a common voltage grid"""
    common_voltage = np.linspace(v_min, v_max, num_points)
    interpolated_dqdvs = []
    
    for voltage, dqdv in zip(voltage_arrays, dqdv_arrays):
        # Filter out NaN values
        valid_indices = ~np.isnan(dqdv)
        if sum(valid_indices) < 2:  # Need at least 2 points for interpolation
            continue
            
        voltage_filtered = voltage[valid_indices]
        dqdv_filtered = dqdv[valid_indices]
        
        # Sort by voltage (important for interpolation)
        sort_idx = np.argsort(voltage_filtered)
        voltage_filtered = voltage_filtered[sort_idx]
        dqdv_filtered = dqdv_filtered[sort_idx]
        
        # Limit to the voltage range we're interested in
        mask = (voltage_filtered >= v_min) & (voltage_filtered <= v_max)
        if sum(mask) < 2:  # Need at least 2 points in range
            continue
            
        voltage_filtered = voltage_filtered[mask]
        dqdv_filtered = dqdv_filtered[mask]
        
        # Create interpolation function
        interp_func = interp1d(voltage_filtered, dqdv_filtered, 
                              kind='linear', bounds_error=False, fill_value=np.nan)
        
        # Interpolate to common grid
        interpolated_dqdv = interp_func(common_voltage)
        
        # Replace any remaining NaNs with zeros
        interpolated_dqdv = np.nan_to_num(interpolated_dqdv, nan=0.0)
        
        interpolated_dqdvs.append(interpolated_dqdv)
    
    return common_voltage, np.array(interpolated_dqdvs)

def extract_cycle_number(filename):
    """Extract cycle number from filename"""
    try:
        # Try to find a pattern like "cycle_10" or "cycle10" in the filename
        basename = os.path.basename(filename)
        parts = basename.split('_')
        for part in parts:
            if part.startswith('cycle'):
                return int(part[5:])
            if part.isdigit():
                return int(part)
        
        # If no pattern found, return a default value
        return 0
    except:
        return 0

def train_random_forest(X, y, n_estimators=100, max_depth=None, random_state=42):
    """Train a Random Forest model for capacity retention prediction"""
    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )
    
    # Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest model
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state
    )
    model.fit(X_train_scaled, y_train)
    
    # Evaluate model
    y_pred = model.predict(X_test_scaled)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)
    
    # Get feature importances
    importances = model.feature_importances_
    
    return model, scaler, importances, (X_train, X_test, y_train, y_test), (mae, rmse, r2)

def plot_feature_importance(voltage_grid, importances, n_top=20):
    """Plot feature importances from Random Forest model"""
    plt.figure(figsize=(12, 6))
    
    # Plot feature importances as a function of voltage
    plt.subplot(1, 2, 1)
    plt.plot(voltage_grid, importances, 'b-', linewidth=2)
    plt.xlabel('Voltage (V)')
    plt.ylabel('Feature Importance')
    plt.title('Feature Importance vs. Voltage')
    plt.grid(True)
    
    # Plot top N most important features
    if len(importances) > n_top:
        plt.subplot(1, 2, 2)
        indices = np.argsort(importances)[-n_top:]
        plt.barh(range(n_top), importances[indices])
        plt.yticks(range(n_top), [f"{voltage_grid[i]:.2f}V" for i in indices])
        plt.xlabel('Feature Importance')
        plt.ylabel('Voltage (V)')
        plt.title(f'Top {n_top} Most Important Voltage Points')
        plt.grid(True)
    
    plt.tight_layout()
    plt.show()

def plot_model_evaluation(X_test, y_test, y_pred, metrics):
    """Plot model evaluation results"""
    mae, rmse, r2 = metrics
    
    plt.figure(figsize=(12, 5))
    
    # Plot predicted vs actual values
    plt.subplot(1, 2, 1)
    plt.scatter(y_test, y_pred, alpha=0.7)
    plt.plot([min(y_test), max(y_test)], [min(y_test), max(y_test)], 'r--')
    plt.xlabel('Actual Capacity Retention')
    plt.ylabel('Predicted Capacity Retention')
    plt.title('Predicted vs Actual Values')
    plt.grid(True)
    
    # Add metrics as text
    plt.text(0.05, 0.95, f"MAE: {mae:.4f}\nRMSE: {rmse:.4f}\nR²: {r2:.4f}",
             transform=plt.gca().transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round', alpha=0.1))
    
    # Plot residuals
    plt.subplot(1, 2, 2)
    residuals = y_test - y_pred
    plt.scatter(y_pred, residuals, alpha=0.7)
    plt.axhline(y=0, color='r', linestyle='--')
    plt.xlabel('Predicted Capacity Retention')
    plt.ylabel('Residuals')
    plt.title('Residual Plot')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

def main():
    print("===== Random Forest for Feature Importance in Battery Degradation =====")
    print("This program uses Random Forest to identify important features in dQ/dV curves for predicting capacity retention.")
    
    # Find dQ/dV files
    print("\nSearching for dQ/dV data files...")
    dqdv_files = find_csv_files()
    
    if not dqdv_files:
        print("No dQ/dV files found. Please run LibDegradationSim03_DD.py first to generate dQ/dV data.")
        return
    
    print(f"Found {len(dqdv_files)} dQ/dV files.")
    
    # Find capacity retention data
    print("\nSearching for capacity retention data...")
    capacity_files = find_capacity_files()
    
    if not capacity_files:
        print("No capacity retention files found. Please run LibDegradationSim03_Cret_V2.py first to generate capacity data.")
        return
    
    print(f"Found {len(capacity_files)} capacity files.")
    
    # Select a capacity file
    if len(capacity_files) > 1:
        print("\nMultiple capacity files found. Please select one:")
        for i, file_path in enumerate(capacity_files):
            print(f"{i+1}. {os.path.basename(file_path)}")
        
        selection = 0
        while selection < 1 or selection > len(capacity_files):
            try:
                selection = int(input("Enter file number: "))
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        capacity_file = capacity_files[selection-1]
    else:
        capacity_file = capacity_files[0]
    
    print(f"Using capacity file: {os.path.basename(capacity_file)}")
    
    # Load capacity data
    cycles, retentions = load_capacity_data(capacity_file)
    if cycles is None or retentions is None:
        print("Failed to load capacity data.")
        return
    
    print(f"Loaded capacity data for {len(cycles)} cycles.")
    
    # Load dQ/dV data
    voltage_arrays = []
    dqdv_arrays = []
    cycle_numbers = []
    
    for file_path in dqdv_files:
        voltage, dqdv = load_dqdv_data(file_path)
        if voltage is not None and dqdv is not None:
            cycle = extract_cycle_number(file_path)
            # Only use cycles that have corresponding capacity data
            if cycle in cycles:
                voltage_arrays.append(voltage)
                dqdv_arrays.append(dqdv)
                cycle_numbers.append(cycle)
                print(f"Loaded dQ/dV data for cycle {cycle}")
    
    if not voltage_arrays:
        print("Failed to load any valid dQ/dV data that matches capacity data.")
        return
    
    # Interpolate to common voltage grid
    print("\nInterpolating dQ/dV curves to common voltage grid...")
    voltage_grid, dqdv_matrix = interpolate_to_common_grid(voltage_arrays, dqdv_arrays)
    
    if dqdv_matrix.shape[0] == 0:
        print("Failed to interpolate dQ/dV curves.")
        return
    
    print(f"Successfully interpolated {dqdv_matrix.shape[0]} dQ/dV curves.")
    
    # Prepare data for Random Forest
    X = dqdv_matrix  # Features: dQ/dV values at each voltage point
    
    # Get corresponding capacity retention values
    y = np.zeros(len(cycle_numbers))
    for i, cycle in enumerate(cycle_numbers):
        idx = np.where(cycles == cycle)[0]
        if len(idx) > 0:
            y[i] = retentions[idx[0]]
    
    print(f"\nTraining Random Forest model with {X.shape[0]} samples and {X.shape[1]} features...")
    
    # Train Random Forest model
    model, scaler, importances, data_split, metrics = train_random_forest(X, y)
    X_train, X_test, y_train, y_test = data_split
    
    # Make predictions on test set
    y_pred = model.predict(scaler.transform(X_test))
    
    # Plot feature importances
    print("\nPlotting feature importances...")
    plot_feature_importance(voltage_grid, importances)
    
    # Plot model evaluation
    print("\nPlotting model evaluation...")
    plot_model_evaluation(X_test, y_test, y_pred, metrics)
    
    # Save feature importances
    print("\nSaving feature importances...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = "ml_results"
    os.makedirs(results_dir, exist_ok=True)
    
    # Save feature importances
    importance_file = os.path.join(results_dir, f"rf_feature_importance_{timestamp}.csv")
    with open(importance_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Voltage', 'Importance'])
        for i, v in enumerate(voltage_grid):
            writer.writerow([v, importances[i]])
    
    # Save model evaluation metrics
    metrics_file = os.path.join(results_dir, f"rf_model_metrics_{timestamp}.csv")
    with open(metrics_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['MAE', metrics[0]])
        writer.writerow(['RMSE', metrics[1]])
        writer.writerow(['R2', metrics[2]])
    
    print(f"Feature importances saved to {importance_file}")
    print(f"Model metrics saved to {metrics_file}")
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()