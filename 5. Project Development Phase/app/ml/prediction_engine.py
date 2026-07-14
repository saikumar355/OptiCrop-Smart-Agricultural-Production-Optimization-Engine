import pickle
import os
import numpy as np
import pandas as pd
from typing import List
from app.models.prediction_result import PredictionResult

FEATURE_NAMES = ['N', 'P', 'K', 'temperature', 'humidity', 'rainfall', 'ph']


class PredictionEngine:
    def __init__(self, model_path: str, scaler_path: str) -> None:
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at path: {model_path}")
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Scaler file not found at path: {scaler_path}")

        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)

        # Derive a human-readable model name from the artifact filename.
        # e.g.  "saved_models/ExtraTrees_2026-07-01T122126Z.pkl"  →  "ExtraTrees_2026-07-01T122126Z"
        self.model_name: str = os.path.splitext(os.path.basename(model_path))[0]

    def predict(self, input_vector: List[float]) -> PredictionResult:
        if len(input_vector) != 7:
            raise ValueError(f"Expected input vector of length 7, got {len(input_vector)}")

        try:
            numeric_values = [float(v) for v in input_vector]
        except (TypeError, ValueError):
            raise ValueError("Input vector contains non-numeric values.")

        input_df = pd.DataFrame([numeric_values], columns=FEATURE_NAMES)
        scaled_array = self.scaler.transform(input_df)
        scaled_df = pd.DataFrame(scaled_array, columns=FEATURE_NAMES)

        predicted_label = self.model.predict(scaled_df)[0]

        if hasattr(self.model, "predict_proba"):
            probabilities = self.model.predict_proba(scaled_df)[0]
            confidence_score = float(np.max(probabilities))
        else:
            confidence_score = 1.0

        return PredictionResult(
            predicted_label=str(predicted_label),
            confidence_score=confidence_score,
        )
