import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging

logger = logging.getLogger(__name__)

def generate_eda_plots(df: pd.DataFrame):
    eda_dir = os.environ.get('EDA_STATIC_DIR', 'app/static/eda/')
    os.makedirs(eda_dir, exist_ok=True)
    
    num_features = ['N', 'P', 'K', 'temperature', 'humidity', 'rainfall', 'ph']
    
    # Generate correlation heatmap
    plt.figure(figsize=(10, 8))
    corr = df[num_features].corr(method='pearson')
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
    plt.title('Correlation Heatmap')
    plt.tight_layout()
    plt.savefig(os.path.join(eda_dir, 'correlation_heatmap.png'))
    plt.close()
    
    # Generate class distribution
    if 'label' in df.columns:
        plt.figure(figsize=(12, 6))
        sns.countplot(data=df, x='label', order=df['label'].value_counts().index, palette='viridis')
        plt.title('Class Distribution')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(eda_dir, 'class_distribution.png'))
        plt.close()
        
    # Generate feature histograms
    for feature in num_features:
        plt.figure(figsize=(8, 6))
        sns.histplot(df[feature], kde=True, bins=30, color='skyblue')
        plt.title(f'Distribution of {feature}')
        plt.tight_layout()
        plt.savefig(os.path.join(eda_dir, f'feature_hist_{feature}.png'))
        plt.close()
        
    logger.info(f"EDA plots generated and saved to {eda_dir}")
