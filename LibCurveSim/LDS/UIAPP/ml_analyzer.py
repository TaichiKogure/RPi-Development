"""
Machine Learning Analyzer Module

This module provides machine learning functionality for the battery simulation and analysis tool.
It implements various machine learning models for analyzing battery data.
"""

import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.svm import SVR

# Try to import TensorFlow for neural network models
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False


class MLAnalyzer:
    """
    Class for machine learning analysis.
    """
    
    def __init__(self):
        """Initialize the ML analyzer."""
        pass
    
    def run_pca(self, data, n_components=2, standardize=True):
        """
        Run Principal Component Analysis (PCA) on the data.
        
        Args:
            data: Input data matrix (samples x features)
            n_components: Number of principal components
            standardize: Whether to standardize the data
            
        Returns:
            Dictionary with PCA results
        """
        # Standardize data if requested
        if standardize:
            scaler = StandardScaler()
            data_scaled = scaler.fit_transform(data)
        else:
            data_scaled = data
        
        # Run PCA
        pca = PCA(n_components=n_components)
        principal_components = pca.fit_transform(data_scaled)
        
        # Calculate loadings
        loadings = pca.components_.T * np.sqrt(pca.explained_variance_)
        
        return {
            'principal_components': principal_components,
            'explained_variance_ratio': pca.explained_variance_ratio_,
            'loadings': loadings,
            'pca_model': pca,
            'scaler': scaler if standardize else None
        }
    
    def run_random_forest(self, X, y, n_estimators=100, max_depth=None, test_size=0.2, random_state=None):
        """
        Run Random Forest regression on the data.
        
        Args:
            X: Input features
            y: Target values
            n_estimators: Number of trees in the forest
            max_depth: Maximum depth of the trees
            test_size: Proportion of the data to use for testing
            random_state: Random state for reproducibility
            
        Returns:
            Dictionary with Random Forest results
        """
        # Split data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Create and train the model
        model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state
        )
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        
        # Calculate metrics
        train_mse = mean_squared_error(y_train, y_pred_train)
        train_mae = mean_absolute_error(y_train, y_pred_train)
        train_r2 = r2_score(y_train, y_pred_train)
        
        test_mse = mean_squared_error(y_test, y_pred_test)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        test_r2 = r2_score(y_test, y_pred_test)
        
        return {
            'model': model,
            'feature_importances': model.feature_importances_,
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test,
            'y_pred_train': y_pred_train,
            'y_pred_test': y_pred_test,
            'train_mse': train_mse,
            'train_mae': train_mae,
            'train_r2': train_r2,
            'test_mse': test_mse,
            'test_mae': test_mae,
            'test_r2': test_r2
        }
    
    def run_clustering(self, data, n_clusters=3, algorithm='kmeans', standardize=True):
        """
        Run clustering on the data.
        
        Args:
            data: Input data matrix (samples x features)
            n_clusters: Number of clusters
            algorithm: Clustering algorithm ('kmeans' or 'hierarchical')
            standardize: Whether to standardize the data
            
        Returns:
            Dictionary with clustering results
        """
        # Standardize data if requested
        if standardize:
            scaler = StandardScaler()
            data_scaled = scaler.fit_transform(data)
        else:
            data_scaled = data
        
        # Run clustering
        if algorithm.lower() == 'kmeans':
            model = KMeans(n_clusters=n_clusters, random_state=42)
        elif algorithm.lower() == 'hierarchical':
            model = AgglomerativeClustering(n_clusters=n_clusters)
        else:
            raise ValueError(f"Unknown clustering algorithm: {algorithm}")
        
        labels = model.fit_predict(data_scaled)
        
        # Calculate cluster centers (for KMeans only)
        if algorithm.lower() == 'kmeans':
            cluster_centers = model.cluster_centers_
            if standardize:
                cluster_centers = scaler.inverse_transform(cluster_centers)
        else:
            cluster_centers = None
        
        return {
            'labels': labels,
            'model': model,
            'cluster_centers': cluster_centers,
            'scaler': scaler if standardize else None
        }
    
    def run_neural_network(self, X, y, hidden_units=[64, 32], dropout_rate=0.2, epochs=200,
                          batch_size=16, test_size=0.2, random_state=None, patience=30):
        """
        Run Neural Network regression on the data.
        
        Args:
            X: Input features
            y: Target values
            hidden_units: List of units in each hidden layer
            dropout_rate: Dropout rate
            epochs: Number of epochs
            batch_size: Batch size
            test_size: Proportion of the data to use for testing
            random_state: Random state for reproducibility
            patience: Patience for early stopping
            
        Returns:
            Dictionary with Neural Network results
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is not available. Please install it to use neural networks.")
        
        # Split data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Standardize the data
        scaler_X = StandardScaler()
        X_train_scaled = scaler_X.fit_transform(X_train)
        X_test_scaled = scaler_X.transform(X_test)
        
        # Create the model
        model = Sequential()
        
        # Add input layer and first hidden layer
        model.add(Dense(hidden_units[0], activation='relu', input_shape=(X_train.shape[1],)))
        model.add(Dropout(dropout_rate))
        
        # Add additional hidden layers
        for units in hidden_units[1:]:
            model.add(Dense(units, activation='relu'))
            model.add(Dropout(dropout_rate))
        
        # Add output layer
        model.add(Dense(1))
        
        # Compile the model
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        # Set up callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=patience, restore_best_weights=True),
            ModelCheckpoint('best_model.h5', monitor='val_loss', save_best_only=True)
        ]
        
        # Train the model
        history = model.fit(
            X_train_scaled, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            callbacks=callbacks,
            verbose=0
        )
        
        # Make predictions
        y_pred_train = model.predict(X_train_scaled).flatten()
        y_pred_test = model.predict(X_test_scaled).flatten()
        
        # Calculate metrics
        train_mse = mean_squared_error(y_train, y_pred_train)
        train_mae = mean_absolute_error(y_train, y_pred_train)
        train_r2 = r2_score(y_train, y_pred_train)
        
        test_mse = mean_squared_error(y_test, y_pred_test)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        test_r2 = r2_score(y_test, y_pred_test)
        
        return {
            'model': model,
            'history': history,
            'scaler_X': scaler_X,
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test,
            'y_pred_train': y_pred_train,
            'y_pred_test': y_pred_test,
            'train_mse': train_mse,
            'train_mae': train_mae,
            'train_r2': train_r2,
            'test_mse': test_mse,
            'test_mae': test_mae,
            'test_r2': test_r2
        }
    
    def run_svr(self, X, y, kernel='rbf', C=1.0, test_size=0.2, random_state=None):
        """
        Run Support Vector Regression (SVR) on the data.
        
        Args:
            X: Input features
            y: Target values
            kernel: Kernel type ('linear', 'poly', 'rbf', 'sigmoid')
            C: Regularization parameter
            test_size: Proportion of the data to use for testing
            random_state: Random state for reproducibility
            
        Returns:
            Dictionary with SVR results
        """
        # Split data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Standardize the data
        scaler_X = StandardScaler()
        X_train_scaled = scaler_X.fit_transform(X_train)
        X_test_scaled = scaler_X.transform(X_test)
        
        # Create and train the model
        model = SVR(kernel=kernel, C=C)
        model.fit(X_train_scaled, y_train)
        
        # Make predictions
        y_pred_train = model.predict(X_train_scaled)
        y_pred_test = model.predict(X_test_scaled)
        
        # Calculate metrics
        train_mse = mean_squared_error(y_train, y_pred_train)
        train_mae = mean_absolute_error(y_train, y_pred_train)
        train_r2 = r2_score(y_train, y_pred_train)
        
        test_mse = mean_squared_error(y_test, y_pred_test)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        test_r2 = r2_score(y_test, y_pred_test)
        
        return {
            'model': model,
            'scaler_X': scaler_X,
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test,
            'y_pred_train': y_pred_train,
            'y_pred_test': y_pred_test,
            'train_mse': train_mse,
            'train_mae': train_mae,
            'train_r2': train_r2,
            'test_mse': test_mse,
            'test_mae': test_mae,
            'test_r2': test_r2
        }