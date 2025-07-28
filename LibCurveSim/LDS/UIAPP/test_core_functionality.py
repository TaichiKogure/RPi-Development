"""
Test script for core functionality of the battery simulation and analysis tool.

This script tests the core functionality of the application, including:
- Simulation
- Data processing (dQ/dV calculation and peak detection)
- Machine learning

Usage:
    python test_core_functionality.py
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Add the parent directory to the path to import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the core modules
from simulation_core import SimulationCore
from data_processor import DataProcessor
from ml_analyzer import MLAnalyzer

# Create a results directory if it doesn't exist
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def test_simulation():
    """Test the simulation functionality."""
    print("\n=== Testing Simulation ===")
    
    # Create a simulation core
    sim_core = SimulationCore()
    
    # Set parameters
    sim_core.set_battery_params(
        initial_capacity=3.0,  # Ah
        c_rate=0.5,            # C
        initial_resistance=0.05  # Ohm
    )
    
    sim_core.set_degradation_params(
        capacity_degradation_a=0.1,
        capacity_degradation_b=0.05,
        resistance_increase_c=0.05,
        resistance_increase_d=1.0
    )
    
    sim_core.set_simulation_params(
        num_cycles=10,
        time_step=1.0  # seconds
    )
    
    # Run simulation
    print("Running simulation...")
    results = sim_core.run_simulation()
    
    # Verify results
    print(f"Simulation completed with {len(results)} cycles")
    
    # Check if results are valid
    if len(results) != 10:
        print(f"ERROR: Expected 10 cycles, got {len(results)}")
        return False
    
    # Check if capacity decreases with cycles
    capacities = [result['charge']['capacity'][-1] for result in results]
    if not all(capacities[i] >= capacities[i+1] for i in range(len(capacities)-1)):
        print("ERROR: Capacity should decrease with cycles")
        return False
    
    # Check if resistance increases with cycles
    resistances = [result['resistance'] for result in results]
    if not all(resistances[i] <= resistances[i+1] for i in range(len(resistances)-1)):
        print("ERROR: Resistance should increase with cycles")
        return False
    
    # Plot results
    plt.figure(figsize=(12, 8))
    
    # Plot charge curves
    plt.subplot(2, 2, 1)
    for result in results:
        plt.plot(result['charge']['capacity'], result['charge']['voltage'], label=f"Cycle {result['cycle']}")
    plt.xlabel('Capacity (Ah)')
    plt.ylabel('Voltage (V)')
    plt.title('Charge Curves')
    plt.grid(True)
    
    # Plot discharge curves
    plt.subplot(2, 2, 2)
    for result in results:
        plt.plot(result['discharge']['capacity'], result['discharge']['voltage'], label=f"Cycle {result['cycle']}")
    plt.xlabel('Capacity (Ah)')
    plt.ylabel('Voltage (V)')
    plt.title('Discharge Curves')
    plt.grid(True)
    
    # Plot capacity vs cycle
    plt.subplot(2, 2, 3)
    plt.plot(range(1, len(results)+1), capacities, 'o-')
    plt.xlabel('Cycle')
    plt.ylabel('Capacity (Ah)')
    plt.title('Capacity vs Cycle')
    plt.grid(True)
    
    # Plot resistance vs cycle
    plt.subplot(2, 2, 4)
    plt.plot(range(1, len(results)+1), resistances, 'o-')
    plt.xlabel('Cycle')
    plt.ylabel('Resistance (Ohm)')
    plt.title('Resistance vs Cycle')
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "simulation_test.png"))
    
    print("Simulation test completed successfully")
    return results


def test_data_processing(simulation_results):
    """
    Test the data processing functionality.
    
    Args:
        simulation_results: Results from the simulation test
    """
    print("\n=== Testing Data Processing ===")
    
    # Create a data processor
    data_processor = DataProcessor()
    
    # Calculate dQ/dV curves
    print("Calculating dQ/dV curves...")
    dqdv_data = {}
    
    for result in simulation_results:
        cycle = result['cycle']
        
        # Get discharge data
        capacity = result['discharge']['capacity']
        voltage = result['discharge']['voltage']
        
        # Calculate dQ/dV
        dqdv_result = data_processor.calculate_dqdv(voltage, capacity, smoothing=0.01)
        
        # Store results
        dqdv_data[cycle] = {
            'voltage': dqdv_result['voltage'],
            'dqdv': dqdv_result['dqdv']
        }
    
    # Verify results
    print(f"dQ/dV calculation completed for {len(dqdv_data)} cycles")
    
    # Check if dQ/dV data is valid
    if len(dqdv_data) != len(simulation_results):
        print(f"ERROR: Expected {len(simulation_results)} dQ/dV curves, got {len(dqdv_data)}")
        return False
    
    # Detect peaks
    print("Detecting peaks...")
    peak_data = {}
    
    for cycle, data in dqdv_data.items():
        # Detect peaks
        peak_result = data_processor.detect_peaks(
            data['voltage'],
            data['dqdv'],
            prominence=0.1,
            width=3,
            height=0.1,
            distance=5
        )
        
        # Store results
        peak_data[cycle] = peak_result
    
    # Verify results
    print(f"Peak detection completed for {len(peak_data)} cycles")
    
    # Check if peak data is valid
    if len(peak_data) != len(dqdv_data):
        print(f"ERROR: Expected {len(dqdv_data)} peak data, got {len(peak_data)}")
        return False
    
    # Plot results
    plt.figure(figsize=(12, 8))
    
    # Plot dQ/dV curves
    plt.subplot(2, 1, 1)
    for cycle, data in dqdv_data.items():
        plt.plot(data['voltage'], data['dqdv'], label=f"Cycle {cycle}")
    plt.xlabel('Voltage (V)')
    plt.ylabel('dQ/dV (Ah/V)')
    plt.title('dQ/dV Curves')
    plt.grid(True)
    plt.legend()
    
    # Plot peaks
    plt.subplot(2, 1, 2)
    for cycle, data in peak_data.items():
        if len(data['peak_voltages']) > 0:
            plt.plot(data['peak_voltages'], data['peak_dqdvs'], 'o', label=f"Cycle {cycle}")
    plt.xlabel('Voltage (V)')
    plt.ylabel('dQ/dV (Ah/V)')
    plt.title('Detected Peaks')
    plt.grid(True)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "data_processing_test.png"))
    
    print("Data processing test completed successfully")
    return dqdv_data, peak_data


def test_machine_learning(dqdv_data):
    """
    Test the machine learning functionality.
    
    Args:
        dqdv_data: dQ/dV data from the data processing test
    """
    print("\n=== Testing Machine Learning ===")
    
    # Create an ML analyzer
    ml_analyzer = MLAnalyzer()
    
    # Prepare data for PCA
    print("Preparing data for PCA...")
    
    # Extract dQ/dV curves and cycle numbers
    cycles = list(dqdv_data.keys())
    
    # Create a common voltage grid
    min_voltage = min(np.min(dqdv_data[cycle]['voltage']) for cycle in cycles)
    max_voltage = max(np.max(dqdv_data[cycle]['voltage']) for cycle in cycles)
    voltage_grid = np.linspace(min_voltage, max_voltage, 100)
    
    # Interpolate dQ/dV curves to the common voltage grid
    dqdv_matrix = np.zeros((len(cycles), len(voltage_grid)))
    
    for i, cycle in enumerate(cycles):
        # Interpolate dQ/dV curve
        dqdv_interp = np.interp(
            voltage_grid,
            dqdv_data[cycle]['voltage'],
            dqdv_data[cycle]['dqdv'],
            left=0,
            right=0
        )
        
        # Store interpolated curve
        dqdv_matrix[i] = dqdv_interp
    
    # Run PCA
    print("Running PCA...")
    pca_results = ml_analyzer.run_pca(dqdv_matrix, n_components=3)
    
    # Verify results
    print(f"PCA completed with {pca_results['principal_components'].shape[1]} components")
    
    # Check if PCA results are valid
    if pca_results['principal_components'].shape != (len(cycles), 3):
        print(f"ERROR: Expected principal components shape {(len(cycles), 3)}, got {pca_results['principal_components'].shape}")
        return False
    
    # Create capacity retention data (simulated)
    capacity_retention = np.linspace(1.0, 0.8, len(cycles))
    
    # Run Random Forest
    print("Running Random Forest...")
    rf_results = ml_analyzer.run_random_forest(
        dqdv_matrix,
        capacity_retention,
        n_estimators=10,
        max_depth=3,
        test_size=0.2,
        random_state=42
    )
    
    # Verify results
    print(f"Random Forest completed with R² = {rf_results['test_r2']:.4f}")
    
    # Run clustering
    print("Running clustering...")
    clustering_results = ml_analyzer.run_clustering(
        dqdv_matrix,
        n_clusters=3,
        algorithm='kmeans'
    )
    
    # Verify results
    print(f"Clustering completed with {len(np.unique(clustering_results['labels']))} clusters")
    
    # Plot results
    plt.figure(figsize=(15, 10))
    
    # Plot PCA results
    plt.subplot(2, 2, 1)
    plt.scatter(
        pca_results['principal_components'][:, 0],
        pca_results['principal_components'][:, 1],
        c=cycles,
        cmap='viridis'
    )
    plt.colorbar(label='Cycle')
    plt.xlabel('PC1')
    plt.ylabel('PC2')
    plt.title('PCA Results')
    plt.grid(True)
    
    # Plot explained variance
    plt.subplot(2, 2, 2)
    plt.bar(range(1, len(pca_results['explained_variance_ratio'])+1), pca_results['explained_variance_ratio'])
    plt.xlabel('Principal Component')
    plt.ylabel('Explained Variance Ratio')
    plt.title('Explained Variance')
    plt.grid(True)
    
    # Plot Random Forest results
    plt.subplot(2, 2, 3)
    plt.scatter(rf_results['y_test'], rf_results['y_pred_test'])
    plt.plot([0.7, 1.0], [0.7, 1.0], 'k--')
    plt.xlabel('True Capacity Retention')
    plt.ylabel('Predicted Capacity Retention')
    plt.title(f"Random Forest (R² = {rf_results['test_r2']:.4f})")
    plt.grid(True)
    
    # Plot clustering results
    plt.subplot(2, 2, 4)
    plt.scatter(
        pca_results['principal_components'][:, 0],
        pca_results['principal_components'][:, 1],
        c=clustering_results['labels'],
        cmap='tab10'
    )
    plt.xlabel('PC1')
    plt.ylabel('PC2')
    plt.title('Clustering Results')
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "machine_learning_test.png"))
    
    print("Machine learning test completed successfully")
    return True


def main():
    """Main function to run all tests."""
    print("=== Battery Simulation and Analysis Tool - Core Functionality Test ===")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Results will be saved to: {RESULTS_DIR}")
    
    # Test simulation
    simulation_results = test_simulation()
    if not simulation_results:
        print("Simulation test failed")
        return
    
    # Test data processing
    dqdv_data, peak_data = test_data_processing(simulation_results)
    if not dqdv_data or not peak_data:
        print("Data processing test failed")
        return
    
    # Test machine learning
    ml_success = test_machine_learning(dqdv_data)
    if not ml_success:
        print("Machine learning test failed")
        return
    
    print("\n=== All tests completed successfully ===")
    print(f"Test results saved to: {RESULTS_DIR}")


if __name__ == "__main__":
    main()