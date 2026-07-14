from dataclasses import dataclass

FIELD_RANGES: dict[str, tuple[float, float]] = {
    "N":           (0.0,   140.0),
    "P":           (5.0,   145.0),
    "K":           (5.0,   205.0),
    "temperature": (0.0,    50.0),
    "humidity":    (0.0,   100.0),
    "rainfall":    (0.0,   300.0),
    "ph":          (0.0,    14.0),
}

@dataclass
class InputVector:
    N: float
    P: float
    K: float
    temperature: float
    humidity: float
    rainfall: float
    ph: float
