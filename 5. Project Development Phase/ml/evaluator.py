import os
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List

from sklearn.model_selection import StratifiedKFold, cross_validate, GridSearchCV, RandomizedSearchCV
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from ml.trainer import XGBWrapper

logger = logging.getLogger(__name__)

def get_param_grid(model_name: str) -> Dict[str, List[Any]]:
    # Minimal grids to stay within reasonable training time
    if model_name == 'Logistic Regression':
        return {'C': [1.0, 10.0]}
    elif model_name == 'Decision Tree':
        return {'max_depth': [None, 10]}
    elif model_name == 'Random Forest':
        return {'n_estimators': [50, 100]}
    elif model_name == 'KNN':
        return {'n_neighbors': [3, 5]}
    elif model_name == 'Naive Bayes':
        return {}
    elif model_name == 'SVM':
        # CalibratedClassifierCV wraps SVC, so params use estimator__ prefix
        return {'estimator__C': [1.0, 10.0]}
    elif model_name == 'Gradient Boosting':
        return {'n_estimators': [50, 100]}
    elif model_name == 'Extra Trees':
        return {'n_estimators': [50, 100]}
    elif model_name == 'XGBoost':
        return {}
    return {}

def evaluate_models(trained_models: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
    cv_folds = int(os.environ.get('CV_FOLDS', '5'))
    search_strategy = os.environ.get('HYPERPARAM_STRATEGY', 'grid')

    num_features = ['N', 'P', 'K', 'temperature', 'humidity', 'rainfall', 'ph']
    X = df[num_features]
    y = df['label']

    classes = df['label'].unique()
    min_class_count = int(df['label'].value_counts().min())
    # Ensure cv_folds never exceeds per-class sample count
    actual_folds = min(cv_folds, min_class_count)
    if actual_folds < cv_folds:
        logger.warning(
            f"CV folds reduced from {cv_folds} to {actual_folds} "
            f"because the smallest class has only {min_class_count} samples."
        )
    if actual_folds < 2:
        actual_folds = 2

    is_multiclass = len(classes) > 2
    report = {}
    skf = StratifiedKFold(n_splits=actual_folds, shuffle=True, random_state=42)

    for name, model in trained_models.items():
        logger.info(f"Evaluating {name}...")
        try:
            param_grid = get_param_grid(name)
            
            # Step 1: Hyperparameter tuning (only if params exist)
            best_model = model
            if param_grid:
                if search_strategy == 'grid':
                    search = GridSearchCV(model, param_grid, cv=skf, scoring='f1_weighted', n_jobs=1)
                elif search_strategy == 'random':
                    search = RandomizedSearchCV(model, param_grid, cv=skf, scoring='f1_weighted', n_iter=10, random_state=42, n_jobs=1)
                else:
                    search = None
                    
                if search:
                    search.fit(X, y)
                    best_model = search.best_estimator_
                    logger.info(f"{name} best params: {search.best_params_}")
            
            # Step 2: Cross validation for robust metrics
            # cross_validate on the best model
            scoring = ['accuracy', 'f1_weighted', 'precision_weighted', 'recall_weighted']
            
            # ROC AUC is complex for multiclass with string labels via cross_validate directly, 
            # we will compute it manually on a train/test split or try to include it if OvR is supported.
            
            cv_results = cross_validate(best_model, X, y, cv=skf, scoring=scoring, n_jobs=1)
            
            f1_mean = np.mean(cv_results['test_f1_weighted'])
            f1_std = np.std(cv_results['test_f1_weighted'])
            
            # To get a single ROC AUC, evaluate on the whole set (or we can just skip or do a 1-fold for ROC)
            # Actually requirements state: Compute ROC-AUC (OvR for <=10 classes) per model.
            roc_auc = None
            if len(classes) <= 10 and hasattr(best_model, "predict_proba"):
                try:
                    y_prob = best_model.predict_proba(X)
                    roc_auc = roc_auc_score(y, y_prob, multi_class='ovr', average='weighted')
                except Exception as e:
                    logger.warning(f"Could not compute ROC-AUC for {name}: {e}")
            
            report[name] = {
                'accuracy': np.mean(cv_results['test_accuracy']),
                'f1_weighted_mean': f1_mean,
                'f1_weighted_std': f1_std,
                'precision_weighted': np.mean(cv_results['test_precision_weighted']),
                'recall_weighted': np.mean(cv_results['test_recall_weighted']),
                'roc_auc': roc_auc,
                'best_model': best_model
            }
            logger.info(f"{name} evaluation complete. F1-Weighted: {f1_mean:.4f} ± {f1_std:.4f}")
            
        except Exception as e:
            logger.error(f"Failed to evaluate {name}: {e}")
            report[name] = {'error': str(e)}
            continue
            
    return report
