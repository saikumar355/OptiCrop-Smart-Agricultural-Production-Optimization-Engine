import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

# Adjust path to import ml and app modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from ml.exceptions import ConfigurationError, DataIngestionError, DataParseError
from ml.ingestion import ingest_data
from ml.preprocessor import preprocess_data
from ml.eda_visualizer import generate_eda_plots
from ml.trainer import train_models
from ml.evaluator import evaluate_models
from ml.model_selector import select_and_save_best_model
from sklearn.model_selection import train_test_split

# Setup basic logging for the script
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
logger = logging.getLogger(__name__)

def perform_split(df):
    test_ratio = float(os.environ.get('TEST_RATIO', '0.2'))
    if not (0.0 < test_ratio < 1.0):
        raise ConfigurationError(f"TEST_RATIO must be between 0 and 1 exclusive, got {test_ratio}")
        
    random_seed = int(os.environ.get('RANDOM_SEED', '42'))
    
    if 'label' not in df.columns:
        train_df, test_df = train_test_split(df, test_size=test_ratio, random_state=random_seed)
        logger.info(f"Split data into {len(train_df)} train and {len(test_df)} test rows (unstratified, no label).")
        return train_df, test_df
        
    class_counts = df['label'].value_counts()
    if (class_counts < 2).any():
        logger.warning("One or more classes have < 2 samples. Falling back to non-stratified split.")
        train_df, test_df = train_test_split(df, test_size=test_ratio, random_state=random_seed)
    else:
        train_df, test_df = train_test_split(
            df, test_size=test_ratio, random_state=random_seed, stratify=df['label']
        )
        
    logger.info(f"Split data into {len(train_df)} train and {len(test_df)} test rows.")
    return train_df, test_df

def write_status(status: str):
    registry_path = os.environ.get('MODEL_REGISTRY_PATH', 'saved_models/')
    os.makedirs(registry_path, exist_ok=True)
    status_file = os.path.join(registry_path, 'training_status.json')
    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        with open(status_file, 'w') as f:
            json.dump({"status": status, "timestamp": timestamp}, f)
    except Exception as e:
        logger.error(f"Failed to write training status: {e}")

def main():
    try:
        # Require DATASET_PATH
        if not os.environ.get('DATASET_PATH'):
            raise ConfigurationError("DATASET_PATH is required but not set.")
            
        logger.info("Starting ML Pipeline...")
        
        # 1. Ingestion
        df = ingest_data()
        
        # 2. Preprocessing
        preprocessed_df, scaler = preprocess_data(df)
        
        # 3. EDA
        generate_eda_plots(preprocessed_df)
        
        # 4. Split
        train_df, test_df = perform_split(preprocessed_df)
        
        # 5. Training
        trained_models = train_models(train_df)
        
        # 6. Evaluation
        evaluation_report = evaluate_models(trained_models, test_df)
        
        # 7. Model Selection
        select_and_save_best_model(evaluation_report, scaler)
        
        write_status("completed")
        logger.info("ML Pipeline completed successfully.")
        
    except (ConfigurationError, DataIngestionError, DataParseError) as e:
        logger.error(f"Pipeline failed: {e}")
        write_status("failed")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected pipeline error: {e}")
        write_status("failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
