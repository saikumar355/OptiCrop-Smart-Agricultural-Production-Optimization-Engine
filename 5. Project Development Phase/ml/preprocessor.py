import os
import pandas as pd
import numpy as np
import logging
from typing import Tuple, Any
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from ml.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

def preprocess_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Any]:
    df = df.copy()
    initial_rows = len(df)
    
    # Identify numerical features
    num_features = ['N', 'P', 'K', 'temperature', 'humidity', 'rainfall', 'ph']
    
    # Step 1: Handle missing values
    missing_strategy = os.environ.get('MISSING_VALUE_STRATEGY', 'drop')
    missing_count = df.isnull().sum().sum()
    if missing_count > 0:
        if missing_strategy == 'drop':
            df.dropna(inplace=True)
        elif missing_strategy == 'mean':
            df[num_features] = df[num_features].fillna(df[num_features].mean())
        elif missing_strategy == 'median':
            df[num_features] = df[num_features].fillna(df[num_features].median())
        else:
            raise ConfigurationError(f"Invalid MISSING_VALUE_STRATEGY: {missing_strategy}")
        logger.info(f"Handled {missing_count} missing values using {missing_strategy} strategy.")
    else:
        logger.info("No missing values found.")
        if missing_strategy not in ['drop', 'mean', 'median']:
            raise ConfigurationError(f"Invalid MISSING_VALUE_STRATEGY: {missing_strategy}")

    # Step 2: Remove exact-duplicate rows
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        df.drop_duplicates(inplace=True)
    logger.info(f"Removed {duplicates} duplicate rows.")
    
    # Step 3: Treat outliers
    outlier_strategy = os.environ.get('OUTLIER_STRATEGY', 'iqr_clip')
    if outlier_strategy == 'iqr_clip':
        outliers_treated = 0
        for col in num_features:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Count outliers
            outliers_treated += ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            
            # Clip
            df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
        logger.info(f"Treated {outliers_treated} outlier values using {outlier_strategy}.")
    elif outlier_strategy == 'none':
        logger.info("Outlier treatment skipped as per strategy 'none'.")
    else:
        raise ConfigurationError(f"Invalid OUTLIER_STRATEGY: {outlier_strategy}")

    # Step 4: Fit and apply scaler
    scaler_type = os.environ.get('SCALER_TYPE', 'standard')
    if scaler_type == 'standard':
        scaler = StandardScaler()
    elif scaler_type == 'minmax':
        scaler = MinMaxScaler()
    elif scaler_type == 'robust':
        scaler = RobustScaler()
    else:
        raise ConfigurationError(f"Invalid SCALER_TYPE: {scaler_type}")
    
    df[num_features] = scaler.fit_transform(df[num_features])
    logger.info(f"Applied {scaler_type} scaler to numerical features.")
    
    # Step 5: Feature engineering (placeholder hook)
    # No additional features added in this version.
    
    # Step 6: Compute and log Pearson correlation matrix
    corr_matrix = df[num_features].corr(method='pearson')
    logger.info(f"Pearson correlation matrix:\n{corr_matrix}")
    
    # Step 7: Compute and log class distribution
    if 'label' in df.columns:
        dist = df['label'].value_counts()
        rel_dist = df['label'].value_counts(normalize=True)
        logger.info("Class distribution (count):")
        logger.info(f"\n{dist}")
        logger.info("Class distribution (relative frequency):")
        logger.info(f"\n{rel_dist}")
        
    return df, scaler
