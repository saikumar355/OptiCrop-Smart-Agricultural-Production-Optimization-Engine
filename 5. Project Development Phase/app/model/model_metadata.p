from dataclasses import dataclass

@dataclass
class ModelMetadata:
    model_name: str
    f1_weighted: float
    serialization_timestamp: str
    model_path: str
    scaler_path: str
