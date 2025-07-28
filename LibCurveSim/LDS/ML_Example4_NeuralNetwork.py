import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, UnivariateSpline
import os
import csv
import glob
from datetime import datetime
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
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

def build_neural_network(input_dim, hidden_layers=[64, 32], dropout_rate=0.2, learning_rate=0.001):
    """Build a neural network model for capacity prediction"""
    model = Sequential()
    
    # Input layer
    model.add(Dense(hidden_layers[0], activation='relu', input_shape=(input_dim,)))
    model.add(Dropout(dropout_rate))
    
    # Hidden layers
    for units in hidden_layers[1:]:
        model.add(Dense(units, activation='relu'))
        model.add(Dropout(dropout_rate))
    
    # Output layer (single neuron for regression)
    model.add(Dense(1, activation='linear'))
    
    # Compile model
    optimizer = Adam(learning_rate=learning_rate)
    model.compile(loss='mean_squared_error', optimizer=optimizer, metrics=['mae'])
    
    return model

def train_neural_network(X, y, hidden_layers=[64, 32], dropout_rate=0.2, learning_rate=0.001, 
                        batch_size=16, epochs=100, validation_split=0.2, patience=20, 
                        model_path='best_model.h5'):
    """Train a neural network model for capacity prediction"""
    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Standardize features
    scaler_X = StandardScaler()
    X_train_scaled = scaler_X.fit_transform(X_train)
    X_test_scaled = scaler_X.transform(X_test)
    
    # Scale target (optional, but can help with training)
    scaler_y = MinMaxScaler()
    y_train_scaled = scaler_y.fit_transform(y_train.reshape(-1, 1)).flatten()
    y_test_scaled = scaler_y.transform(y_test.reshape(-1, 1)).flatten()
    
    # Build model
    model = build_neural_network(
        input_dim=X_train.shape[1],
        hidden_layers=hidden_layers,
        dropout_rate=dropout_rate,
        learning_rate=learning_rate
    )
    
    # Callbacks for early stopping and model checkpoint
    callbacks = [
        EarlyStopping(monitor='val_loss', patience=patience, restore_best_weights=True),
        ModelCheckpoint(model_path, monitor='val_loss', save_best_only=True)
    ]
    
    # Train model
    history = model.fit(
        X_train_scaled, y_train_scaled,
        batch_size=batch_size,
        epochs=epochs,
        validation_split=validation_split,
        callbacks=callbacks,
        verbose=1
    )
    
    # Evaluate model
    y_pred_scaled = model.predict(X_test_scaled).flatten()
    y_pred = scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()
    
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)
    
    return model, history, (X_train_scaled, X_test_scaled, y_train_scaled, y_test_scaled), (scaler_X, scaler_y), (mae, rmse, r2), y_pred

def plot_training_history(history):
    """Plot training history"""
    plt.figure(figsize=(12, 5))
    
    # Plot training & validation loss
    plt.subplot(1, 2, 1)
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('Model Loss')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='upper right')
    plt.grid(True)
    
    # Plot training & validation mean absolute error
    plt.subplot(1, 2, 2)
    plt.plot(history.history['mae'])
    plt.plot(history.history['val_mae'])
    plt.title('Model Mean Absolute Error')
    plt.ylabel('MAE')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='upper right')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

def plot_prediction_results(y_test, y_pred, metrics):
    """Plot prediction results"""
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

def plot_feature_importance(model, voltage_grid, scaler_X):
    """Plot feature importance based on neural network weights"""
    # Get weights from the first layer
    weights = model.layers[0].get_weights()[0]
    
    # Calculate feature importance as the absolute sum of weights for each feature
    importance = np.sum(np.abs(weights), axis=1)
    
    # Normalize importance
    importance = importance / np.sum(importance)
    
    plt.figure(figsize=(12, 6))
    
    # Plot feature importance as a function of voltage
    plt.subplot(1, 2, 1)
    plt.plot(voltage_grid, importance, 'b-', linewidth=2)
    plt.xlabel('Voltage (V)')
    plt.ylabel('Feature Importance')
    plt.title('Neural Network Feature Importance vs. Voltage')
    plt.grid(True)
    
    # Plot top 20 most important features
    n_top = min(20, len(importance))
    plt.subplot(1, 2, 2)
    indices = np.argsort(importance)[-n_top:]
    plt.barh(range(n_top), importance[indices])
    plt.yticks(range(n_top), [f"{voltage_grid[i]:.2f}V" for i in indices])
    plt.xlabel('Feature Importance')
    plt.ylabel('Voltage (V)')
    plt.title(f'Top {n_top} Most Important Voltage Points')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

def main():
    print("===== Neural Network for Capacity Prediction from dQ/dV Curves =====")
    print("This program uses neural networks to predict battery capacity retention from dQ/dV curves.")
    
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
    file_names = []
    
    for file_path in dqdv_files:
        voltage, dqdv = load_dqdv_data(file_path)
        if voltage is not None and dqdv is not None:
            cycle = extract_cycle_number(file_path)
            # Only use cycles that have corresponding capacity data
            if cycle in cycles:
                voltage_arrays.append(voltage)
                dqdv_arrays.append(dqdv)
                cycle_numbers.append(cycle)
                file_names.append(os.path.basename(file_path))
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
    
    # Prepare data for neural network
    X = dqdv_matrix  # Features: dQ/dV values at each voltage point
    
    # Get corresponding capacity retention values
    y = np.zeros(len(cycle_numbers))
    for i, cycle in enumerate(cycle_numbers):
        idx = np.where(cycles == cycle)[0]
        if len(idx) > 0:
            y[i] = retentions[idx[0]]
    
    print(f"\nTraining neural network with {X.shape[0]} samples and {X.shape[1]} features...")
    
    # Set neural network hyperparameters
    hidden_layers = [64, 32]
    dropout_rate = 0.2
    learning_rate = 0.001
    batch_size = 16
    epochs = 200
    patience = 30
    
    # Create results directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = "ml_results"
    os.makedirs(results_dir, exist_ok=True)
    model_path = os.path.join(results_dir, f"nn_model_{timestamp}.h5")
    
    # Train neural network
    model, history, data_split, scalers, metrics, y_pred = train_neural_network(
        X, y,
        hidden_layers=hidden_layers,
        dropout_rate=dropout_rate,
        learning_rate=learning_rate,
        batch_size=batch_size,
        epochs=epochs,
        patience=patience,
        model_path=model_path
    )
    
    X_train_scaled, X_test_scaled, y_train_scaled, y_test_scaled = data_split
    scaler_X, scaler_y = scalers
    mae, rmse, r2 = metrics
    
    # Print evaluation metrics
    print("\nModel evaluation:")
    print(f"Mean Absolute Error (MAE): {mae:.4f}")
    print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")
    print(f"R-squared (R²): {r2:.4f}")
    
    # Plot training history
    print("\nPlotting training history...")
    plot_training_history(history)
    
    # Plot prediction results
    print("\nPlotting prediction results...")
    _, _, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    plot_prediction_results(y_test, y_pred, metrics)
    
    # Plot feature importance
    print("\nPlotting feature importance...")
    plot_feature_importance(model, voltage_grid, scaler_X)
    
    # Save model summary and results
    print("\nSaving model summary and results...")
    
    # Save model summary
    summary_file = os.path.join(results_dir, f"nn_summary_{timestamp}.txt")
    with open(summary_file, 'w') as f:
        # Redirect model.summary() output to file
        # Save model architecture
        f.write("Model Architecture:\n")
        for layer in model.layers:
            f.write(f"{layer.name}: {layer.output_shape}\n")
        
        # Save hyperparameters
        f.write("\nHyperparameters:\n")
        f.write(f"Hidden Layers: {hidden_layers}\n")
        f.write(f"Dropout Rate: {dropout_rate}\n")
        f.write(f"Learning Rate: {learning_rate}\n")
        f.write(f"Batch Size: {batch_size}\n")
        f.write(f"Max Epochs: {epochs}\n")
        f.write(f"Early Stopping Patience: {patience}\n")
        
        # Save evaluation metrics
        f.write("\nEvaluation Metrics:\n")
        f.write(f"Mean Absolute Error (MAE): {mae:.4f}\n")
        f.write(f"Root Mean Squared Error (RMSE): {rmse:.4f}\n")
        f.write(f"R-squared (R²): {r2:.4f}\n")
    
    # Save predictions
    predictions_file = os.path.join(results_dir, f"nn_predictions_{timestamp}.csv")
    with open(predictions_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Cycle', 'Actual_Retention', 'Predicted_Retention'])
        
        _, _, _, y_test = train_test_split(X, cycle_numbers, test_size=0.2, random_state=42)
        for cycle, actual, predicted in zip(y_test, y_test, y_pred):
            writer.writerow([cycle, actual, predicted])
    
    print(f"Model saved to {model_path}")
    print(f"Model summary saved to {summary_file}")
    print(f"Predictions saved to {predictions_file}")
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()