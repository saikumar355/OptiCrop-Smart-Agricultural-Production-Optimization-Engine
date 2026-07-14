from dataclasses import dataclass
from typing import Optional

@dataclass
class PredictionRecord:
    id: Optional[int]
    timestamp: str
    N: float
    P: float
    K: float
    temperature: float
    humidity: float
    rainfall: float
    ph: float
    predicted_crop: str
    confidence_score: float
    model_name: str
    hashed_ip: str
