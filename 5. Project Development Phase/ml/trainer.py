import time
import logging
import pandas as pd
from typing import Dict, Any

from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder

from ml.exceptions import DataIngestionError

logger = logging.getLogger(__name__)


class XGBWrapper(BaseEstimator, ClassifierMixin):
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.model = xgb.XGBClassifier(
            eval_metric='mlogloss',
            random_state=random_state
        )
        self.le = LabelEncoder()

    def fit(self, X, y):
        y_encoded = self.le.fit_transform(y)
        self.classes_ = self.le.classes_
        self.model.fit(X, y_encoded)
        return self

    def predict(self, X):
        preds = self.model.predict(X)
        return self.le.inverse_transform(preds)

    def predict_proba(self, X):
        return self.model.predict_proba(X)

def train_models(train_df: pd.DataFrame) -> Dict[str, Any]:
    if train_df.empty:
        raise DataIngestionError("Training set is empty. Cannot proceed with training.")
        
    num_features = ['N', 'P', 'K', 'temperature', 'humidity', 'rainfall', 'ph']
    X_train = train_df[num_features]
    y_train = train_df['label']
    
    # Initialize algorithms
    algorithms = {
        'Logistic Regression': LogisticRegression(max_iter=2000, random_state=42),
        'Decision Tree': DecisionTreeClassifier(random_state=42),
        'Random Forest': RandomForestClassifier(random_state=42),
        'KNN': KNeighborsClassifier(),
        'Naive Bayes': GaussianNB(),
        'SVM': CalibratedClassifierCV(SVC(random_state=42)),
        'Gradient Boosting': GradientBoostingClassifier(random_state=42),
        'Extra Trees': ExtraTreesClassifier(random_state=42),
        'XGBoost': XGBWrapper(random_state=42)
    }
    
    trained_models = {}
    
    for name, model in algorithms.items():
        logger.info(f"Starting training for {name}...")
        start_time = time.time()
        
        try:
            model.fit(X_train, y_train)
            elapsed_time = time.time() - start_time
            logger.info(f"Completed training for {name} in {elapsed_time:.2f}s")
            trained_models[name] = model
        except Exception as e:
            logger.error(f"Failed to train {name}. Reason: {str(e)}")
            continue
            
    return trained_models
