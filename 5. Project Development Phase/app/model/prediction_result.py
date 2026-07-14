from dataclasses import dataclass

@dataclass
class PredictionResult:
    predicted_label: str
    confidence_score: float
