import os
import json
from dotenv import load_dotenv

# Load .env at config import time so all os.environ.get() calls below pick it up,
# even when Flask's reloader re-imports this module in a child process.
load_dotenv()

class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change_me_in_production')
    CSRF_SECRET_KEY = os.environ.get('CSRF_SECRET_KEY', 'change_me_csrf_secret')
    
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'instance/opticrop.db')
    MODEL_REGISTRY_PATH = os.environ.get('MODEL_REGISTRY_PATH', 'saved_models/')
    ACTIVE_MODEL_PATH = os.environ.get('ACTIVE_MODEL_PATH', 'saved_models/model_latest.pkl')
    ACTIVE_SCALER_PATH = os.environ.get('ACTIVE_SCALER_PATH', 'saved_models/scaler_latest.pkl')
    DATASET_PATH = os.environ.get('DATASET_PATH', 'datasets/crop_recommendation.csv')
    
    MISSING_VALUE_STRATEGY = os.environ.get('MISSING_VALUE_STRATEGY', 'drop')
    OUTLIER_STRATEGY = os.environ.get('OUTLIER_STRATEGY', 'iqr_clip')
    SCALER_TYPE = os.environ.get('SCALER_TYPE', 'standard')
    TEST_RATIO = float(os.environ.get('TEST_RATIO', '0.2'))
    RANDOM_SEED = int(os.environ.get('RANDOM_SEED', '42'))
    CV_FOLDS = int(os.environ.get('CV_FOLDS', '5'))
    HYPERPARAM_STRATEGY = os.environ.get('HYPERPARAM_STRATEGY', 'grid')
    
    RECOMMEND_RATE_LIMIT = os.environ.get('RECOMMEND_RATE_LIMIT', '20 per minute')
    SUITABILITY_RATE_LIMIT = os.environ.get('SUITABILITY_RATE_LIMIT', '20 per minute')
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    
    LOG_PATH = os.environ.get('LOG_PATH', 'logs/opticrop.log')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    GUNICORN_WORKERS = int(os.environ.get('GUNICORN_WORKERS', '4'))
    
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', '')
    
    CHARTJS_URL = os.environ.get('CHARTJS_URL', 'https://cdn.jsdelivr.net/npm/chart.js')
    EDA_STATIC_DIR = os.environ.get('EDA_STATIC_DIR', 'app/static/eda/')
    
    _thresholds_str = os.environ.get('SUITABILITY_THRESHOLDS', '{}')
    try:
        SUITABILITY_THRESHOLDS = json.loads(_thresholds_str)
    except json.JSONDecodeError:
        SUITABILITY_THRESHOLDS = {}

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')

class ProductionConfig(BaseConfig):
    DEBUG = False
