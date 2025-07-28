import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, UnivariateSpline
import os
import csv
import glob
from datetime import datetime
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
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

def perform_kmeans_clustering(data, n_clusters=3, random_state=42):
    """Perform K-means clustering on the data"""
    # Standardize the data
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)
    
    # Apply K-means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state)
    cluster_labels = kmeans.fit_predict(data_scaled)
    
    # Calculate silhouette score
    silhouette_avg = silhouette_score(data_scaled, cluster_labels)
    
    return kmeans, cluster_labels, silhouette_avg

def perform_dbscan_clustering(data, eps=0.5, min_samples=5):
    """Perform DBSCAN clustering on the data"""
    # Standardize the data
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)
    
    # Apply DBSCAN clustering
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    cluster_labels = dbscan.fit_predict(data_scaled)
    
    # Calculate silhouette score if there are at least 2 clusters and no noise points (-1)
    if len(set(cluster_labels)) >= 2 and -1 not in cluster_labels:
        silhouette_avg = silhouette_score(data_scaled, cluster_labels)
    else:
        silhouette_avg = None
    
    return dbscan, cluster_labels, silhouette_avg

def perform_hierarchical_clustering(data, n_clusters=3, linkage='ward'):
    """Perform hierarchical clustering on the data"""
    # Standardize the data
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)
    
    # Apply hierarchical clustering
    hc = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage)
    cluster_labels = hc.fit_predict(data_scaled)
    
    # Calculate silhouette score
    silhouette_avg = silhouette_score(data_scaled, cluster_labels)
    
    return hc, cluster_labels, silhouette_avg

def find_optimal_k(data, max_k=10):
    """Find the optimal number of clusters using the elbow method and silhouette score"""
    # Standardize the data
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)
    
    # Calculate inertia and silhouette score for different values of k
    inertias = []
    silhouette_scores = []
    
    for k in range(2, max_k + 1):
        kmeans = KMeans(n_clusters=k, random_state=42)
        cluster_labels = kmeans.fit_predict(data_scaled)
        inertias.append(kmeans.inertia_)
        silhouette_scores.append(silhouette_score(data_scaled, cluster_labels))
    
    return list(range(2, max_k + 1)), inertias, silhouette_scores

def plot_clustering_results(voltage, dqdv_matrix, cluster_labels, cycle_numbers, method_name):
    """Plot clustering results"""
    # Get unique clusters
    unique_clusters = np.unique(cluster_labels)
    n_clusters = len(unique_clusters)
    
    # Create a colormap
    cmap = cm.get_cmap('viridis', n_clusters)
    
    plt.figure(figsize=(15, 10))
    
    # Plot dQ/dV curves colored by cluster
    plt.subplot(2, 2, 1)
    for i, curve in enumerate(dqdv_matrix):
        cluster = cluster_labels[i]
        color = cmap(cluster / max(1, n_clusters - 1))
        plt.plot(voltage, curve, color=color, alpha=0.7, linewidth=1)
    
    plt.xlabel('Voltage (V)')
    plt.ylabel('dQ/dV')
    plt.title(f'dQ/dV Curves Colored by {method_name} Cluster')
    plt.grid(True)
    
    # Plot cluster assignment vs cycle number
    plt.subplot(2, 2, 2)
    plt.scatter(cycle_numbers, cluster_labels, c=cluster_labels, cmap=cmap, s=50)
    plt.xlabel('Cycle Number')
    plt.ylabel('Cluster')
    plt.title('Cluster Assignment vs Cycle Number')
    plt.grid(True)
    
    # Apply PCA for visualization
    if dqdv_matrix.shape[0] > 1:  # Need at least 2 samples for PCA
        pca = PCA(n_components=2)
        dqdv_pca = pca.fit_transform(dqdv_matrix)
        
        # Plot PCA results colored by cluster
        plt.subplot(2, 2, 3)
        for cluster in unique_clusters:
            mask = cluster_labels == cluster
            plt.scatter(dqdv_pca[mask, 0], dqdv_pca[mask, 1], 
                       label=f'Cluster {cluster}', s=50)
        
        plt.xlabel('Principal Component 1')
        plt.ylabel('Principal Component 2')
        plt.title('PCA of dQ/dV Curves Colored by Cluster')
        plt.legend()
        plt.grid(True)
        
        # Plot cluster centroids in original space (for K-means)
        if method_name == 'K-means':
            plt.subplot(2, 2, 4)
            # Transform centroids back to original space
            scaler = StandardScaler()
            scaler.fit(dqdv_matrix)
            centroids_original = scaler.inverse_transform(kmeans.cluster_centers_)
            
            for i, centroid in enumerate(centroids_original):
                plt.plot(voltage, centroid, label=f'Centroid {i}', linewidth=2)
            
            plt.xlabel('Voltage (V)')
            plt.ylabel('dQ/dV')
            plt.title('Cluster Centroids')
            plt.legend()
            plt.grid(True)
    
    plt.tight_layout()
    plt.show()

def plot_optimal_k(k_values, inertias, silhouette_scores):
    """Plot results for finding optimal k"""
    plt.figure(figsize=(12, 5))
    
    # Plot elbow method
    plt.subplot(1, 2, 1)
    plt.plot(k_values, inertias, 'bo-')
    plt.xlabel('Number of Clusters (k)')
    plt.ylabel('Inertia')
    plt.title('Elbow Method for Optimal k')
    plt.grid(True)
    
    # Plot silhouette scores
    plt.subplot(1, 2, 2)
    plt.plot(k_values, silhouette_scores, 'ro-')
    plt.xlabel('Number of Clusters (k)')
    plt.ylabel('Silhouette Score')
    plt.title('Silhouette Score for Optimal k')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

def main():
    print("===== Clustering Analysis of Battery Degradation Patterns =====")
    print("This program applies clustering algorithms to identify patterns in dQ/dV curves across different cycles.")
    
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
    file_names = []
    
    for file_path in dqdv_files:
        voltage, dqdv = load_dqdv_data(file_path)
        if voltage is not None and dqdv is not None:
            voltage_arrays.append(voltage)
            dqdv_arrays.append(dqdv)
            cycle = extract_cycle_number(file_path)
            cycle_numbers.append(cycle)
            file_names.append(os.path.basename(file_path))
            print(f"Loaded data from {os.path.basename(file_path)}")
    
    if not voltage_arrays:
        print("Failed to load any valid dQ/dV data.")
        return
    
    # Interpolate to common voltage grid
    print("\nInterpolating dQ/dV curves to common voltage grid...")
    voltage_grid, dqdv_matrix = interpolate_to_common_grid(voltage_arrays, dqdv_arrays)
    
    if dqdv_matrix.shape[0] == 0:
        print("Failed to interpolate dQ/dV curves.")
        return
    
    print(f"Successfully interpolated {dqdv_matrix.shape[0]} dQ/dV curves.")
    
    # Sort by cycle number
    sort_idx = np.argsort(cycle_numbers)
    cycle_numbers = np.array(cycle_numbers)[sort_idx]
    dqdv_matrix = dqdv_matrix[sort_idx]
    file_names = [file_names[i] for i in sort_idx]
    
    # Find optimal number of clusters
    print("\nFinding optimal number of clusters...")
    k_values, inertias, silhouette_scores = find_optimal_k(dqdv_matrix)
    
    # Plot results for finding optimal k
    plot_optimal_k(k_values, inertias, silhouette_scores)
    
    # Get optimal k based on silhouette score
    optimal_k = k_values[np.argmax(silhouette_scores)]
    print(f"Optimal number of clusters based on silhouette score: {optimal_k}")
    
    # Perform K-means clustering with optimal k
    print(f"\nPerforming K-means clustering with {optimal_k} clusters...")
    kmeans, kmeans_labels, kmeans_silhouette = perform_kmeans_clustering(dqdv_matrix, n_clusters=optimal_k)
    print(f"K-means silhouette score: {kmeans_silhouette:.4f}")
    
    # Plot K-means clustering results
    plot_clustering_results(voltage_grid, dqdv_matrix, kmeans_labels, cycle_numbers, "K-means")
    
    # Perform DBSCAN clustering
    print("\nPerforming DBSCAN clustering...")
    # Try different eps values
    eps_values = [0.5, 1.0, 1.5, 2.0]
    best_eps = None
    best_silhouette = -1
    best_dbscan = None
    best_dbscan_labels = None
    
    for eps in eps_values:
        dbscan, dbscan_labels, dbscan_silhouette = perform_dbscan_clustering(dqdv_matrix, eps=eps, min_samples=2)
        n_clusters = len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0)
        print(f"DBSCAN with eps={eps}: {n_clusters} clusters", end="")
        
        if dbscan_silhouette is not None:
            print(f", silhouette score: {dbscan_silhouette:.4f}")
            if dbscan_silhouette > best_silhouette:
                best_silhouette = dbscan_silhouette
                best_eps = eps
                best_dbscan = dbscan
                best_dbscan_labels = dbscan_labels
        else:
            print(", silhouette score: N/A (less than 2 valid clusters)")
    
    if best_dbscan is not None:
        print(f"Best DBSCAN parameters: eps={best_eps}, silhouette score: {best_silhouette:.4f}")
        plot_clustering_results(voltage_grid, dqdv_matrix, best_dbscan_labels, cycle_numbers, "DBSCAN")
    else:
        print("DBSCAN did not find valid clusters. Skipping DBSCAN visualization.")
    
    # Perform hierarchical clustering
    print("\nPerforming hierarchical clustering...")
    hc, hc_labels, hc_silhouette = perform_hierarchical_clustering(dqdv_matrix, n_clusters=optimal_k)
    print(f"Hierarchical clustering silhouette score: {hc_silhouette:.4f}")
    
    # Plot hierarchical clustering results
    plot_clustering_results(voltage_grid, dqdv_matrix, hc_labels, cycle_numbers, "Hierarchical")
    
    # Save clustering results
    print("\nSaving clustering results...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = "ml_results"
    os.makedirs(results_dir, exist_ok=True)
    
    # Save cluster assignments
    clusters_file = os.path.join(results_dir, f"clustering_results_{timestamp}.csv")
    with open(clusters_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['File', 'Cycle', 'KMeans_Cluster', 'DBSCAN_Cluster', 'Hierarchical_Cluster'])
        
        for i, (file, cycle) in enumerate(zip(file_names, cycle_numbers)):
            kmeans_cluster = kmeans_labels[i]
            dbscan_cluster = best_dbscan_labels[i] if best_dbscan_labels is not None else "N/A"
            hc_cluster = hc_labels[i]
            writer.writerow([file, cycle, kmeans_cluster, dbscan_cluster, hc_cluster])
    
    print(f"Clustering results saved to {clusters_file}")
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()