import os
import pickle
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from ml.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

def select_and_save_best_model(evaluation_report: Dict[str, Any], scaler: Any) -> None:
    registry_path = os.environ.get('MODEL_REGISTRY_PATH', 'saved_models/')
    
    valid_models = []
    excluded_models = []
    
    for name, metrics in evaluation_report.items():
        if 'error' in metrics or metrics.get('f1_weighted_mean') is None:
            excluded_models.append(name)
        else:
            valid_models.append({
                'name': name,
                'f1': metrics['f1_weighted_mean'],
                'precision': metrics.get('precision_weighted', 0.0),
                'model': metrics['best_model']
            })
            
    if excluded_models:
        logger.warning(f"Excluded models due to missing F1 scores or errors: {', '.join(excluded_models)}")
        
    if not valid_models:
        raise ValueError("No valid models with F1 scores found in the evaluation report.")
        
    # Sort descending by F1, then precision, then alphabetical name (reversed since we sort descending)
    # Wait, we want alphabetical ascending if tie. We can sort multiple times or use a custom key.
    # To sort descending by F1, descending by precision, ascending by name:
    # Python sorts tuples element by element.
    valid_models.sort(key=lambda x: (x['f1'], x['precision'], x['name'].lower()), reverse=True)
    # But reverse=True will make name sort descending as well. Let's fix that by negating numeric metrics.
    valid_models.sort(key=lambda x: (-x['f1'], -x['precision'], x['name'].lower()))
    
    best_entry = valid_models[0]
    best_name = best_entry['name']
    best_f1 = best_entry['f1']
    best_model = best_entry['model']
    
    logger.info("Summary Table of all models by F1-weighted (descending):")
    for idx, vm in enumerate(valid_models):
        logger.info(f"{idx+1}. {vm['name']} - F1: {vm['f1']:.4f} - Precision: {vm['precision']:.4f}")
        
    logger.info(f"Selected best model: {best_name} with F1 score: {best_f1:.4f}")
    
    os.makedirs(registry_path, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    model_filename = f"{best_name.replace(' ', '')}_{timestamp}.pkl"
    scaler_filename = f"scaler_{timestamp}.pkl"
    
    model_filepath = os.path.join(registry_path, model_filename)
    scaler_filepath = os.path.join(registry_path, scaler_filename)
    metadata_filepath = os.path.join(registry_path, "metadata.json")
    
    try:
        with open(model_filepath, 'wb') as f:
            pickle.dump(best_model, f)
            
        with open(scaler_filepath, 'wb') as f:
            pickle.dump(scaler, f)
            
        metadata = {
            "model_name": best_name,
            "f1_weighted": best_f1,
            "serialization_timestamp": timestamp,
            "model_path": model_filepath,
            "scaler_path": scaler_filepath
        }
        
        with open(metadata_filepath, 'w') as f:
            json.dump(metadata, f, indent=4)
            
    except Exception as e:
        logger.error(f"Failed to serialize artifacts to {registry_path}: {e}")
        raise e
        
    logger.info(f"Successfully serialized best model to {model_filepath}")
    logger.info(f"Successfully serialized scaler to {scaler_filepath}")
    logger.info(f"Successfully wrote metadata to {metadata_filepath}")
