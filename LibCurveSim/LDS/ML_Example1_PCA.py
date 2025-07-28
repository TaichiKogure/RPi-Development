import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, UnivariateSpline
import os
import csv
import glob
from datetime import datetime
from sklearn.decomposition import PCA
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

def interpolate_to_common_grid(voltage_arrays, dqdv_arrays, v_min=3.0, v_max=4.2, num_points=500):
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

def perform_pca_analysis(dqdv_matrix, n_components=3):
    """Perform PCA on the dQ/dV curves"""
    # Standardize the data
    scaler = StandardScaler()
    dqdv_scaled = scaler.fit_transform(dqdv_matrix)
    
    # Apply PCA
    pca = PCA(n_components=n_components)
    principal_components = pca.fit_transform(dqdv_scaled)
    
    # Get the explained variance ratio
    explained_variance = pca.explained_variance_ratio_
    
    return pca, principal_components, explained_variance

def plot_pca_results(voltage, pca, principal_components, cycle_numbers, explained_variance):
    """Plot PCA results including components and variance explained"""
    n_components = pca.n_components_
    
    plt.figure(figsize=(15, 10))
    
    # Plot the principal components (loadings)
    plt.subplot(2, 2, 1)
    for i in range(n_components):
        plt.plot(voltage, pca.components_[i], label=f'PC{i+1}')
    plt.xlabel('Voltage (V)')
    plt.ylabel('Loading')
    plt.title('Principal Components (Loadings)')
    plt.legend()
    plt.grid(True)
    
    # Plot the explained variance
    plt.subplot(2, 2, 2)
    plt.bar(range(1, n_components+1), explained_variance)
    plt.xlabel('Principal Component')
    plt.ylabel('Explained Variance Ratio')
    plt.title('Explained Variance by Component')
    plt.xticks(range(1, n_components+1))
    plt.grid(True)
    
    # Plot the first two principal components as a scatter plot
    plt.subplot(2, 2, 3)
    scatter = plt.scatter(principal_components[:, 0], principal_components[:, 1], 
                         c=cycle_numbers, cmap=cm.viridis, s=50)
    plt.colorbar(scatter, label='Cycle Number')
    plt.xlabel('Principal Component 1')
    plt.ylabel('Principal Component 2')
    plt.title('PC1 vs PC2 Colored by Cycle Number')
    plt.grid(True)
    
    # If we have at least 3 components, plot PC3 vs PC1
    if n_components >= 3:
        plt.subplot(2, 2, 4)
        scatter = plt.scatter(principal_components[:, 0], principal_components[:, 2], 
                             c=cycle_numbers, cmap=cm.viridis, s=50)
        plt.colorbar(scatter, label='Cycle Number')
        plt.xlabel('Principal Component 1')
        plt.ylabel('Principal Component 3')
        plt.title('PC1 vs PC3 Colored by Cycle Number')
        plt.grid(True)
    
    plt.tight_layout()
    plt.show()

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

def main():
    print("===== dQ/dV Curve Feature Extraction using PCA =====")
    print("This program analyzes dQ/dV curves from multiple cycles using Principal Component Analysis.")
    
    # Find dQ/dV files
    print("\nSearching for dQ/dV data files...")
    dqdv_files = find_csv_files()
    
    if not dqdv_files:
        print("No dQ/dV files found. Please run LibDegradationSim03_DD.py first to generate dQ/dV data.")
        return
    
    print(f"Found {len(dqdv_files)} dQ/dV files.")
    
    # Load dQ/dV data
    voltage_arrays = []
    dqdv_arrays = []
    cycle_numbers = []
    
    for file_path in dqdv_files:
        voltage, dqdv = load_dqdv_data(file_path)
        if voltage is not None and dqdv is not None:
            voltage_arrays.append(voltage)
            dqdv_arrays.append(dqdv)
            cycle_numbers.append(extract_cycle_number(file_path))
            print(f"Loaded data from {os.path.basename(file_path)}")
    
    if not voltage_arrays:
        print("Failed to load any valid dQ/dV data.")
        return
    
    # Interpolate to common voltage grid
    print("\nInterpolating dQ/dV curves to common voltage grid...")
    common_voltage, dqdv_matrix = interpolate_to_common_grid(voltage_arrays, dqdv_arrays)
    
    if dqdv_matrix.shape[0] == 0:
        print("Failed to interpolate dQ/dV curves.")
        return
    
    print(f"Successfully interpolated {dqdv_matrix.shape[0]} dQ/dV curves.")
    
    # Perform PCA
    print("\nPerforming Principal Component Analysis...")
    n_components = min(3, dqdv_matrix.shape[0])  # Use at most 3 components
    pca, principal_components, explained_variance = perform_pca_analysis(dqdv_matrix, n_components)
    
    # Print explained variance
    print("\nExplained variance by principal component:")
    for i, var in enumerate(explained_variance):
        print(f"PC{i+1}: {var:.4f} ({var*100:.2f}%)")
    print(f"Total variance explained: {sum(explained_variance)*100:.2f}%")
    
    # Plot results
    print("\nPlotting PCA results...")
    plot_pca_results(common_voltage, pca, cycle_numbers, explained_variance)
    
    # Save PCA model and results
    print("\nSaving PCA results...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = "ml_results"
    os.makedirs(results_dir, exist_ok=True)
    
    # Save principal components
    pc_file = os.path.join(results_dir, f"pca_components_{timestamp}.csv")
    with open(pc_file, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['Voltage'] + [f'PC{i+1}' for i in range(n_components)]
        writer.writerow(header)
        for i, v in enumerate(common_voltage):
            row = [v] + [pca.components_[j][i] for j in range(n_components)]
            writer.writerow(row)
    
    # Save transformed data
    transformed_file = os.path.join(results_dir, f"pca_transformed_{timestamp}.csv")
    with open(transformed_file, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['Cycle'] + [f'PC{i+1}' for i in range(n_components)]
        writer.writerow(header)
        for i, cycle in enumerate(cycle_numbers):
            row = [cycle] + [principal_components[i][j] for j in range(n_components)]
            writer.writerow(row)
    
    print(f"PCA components saved to {pc_file}")
    print(f"Transformed data saved to {transformed_file}")
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()