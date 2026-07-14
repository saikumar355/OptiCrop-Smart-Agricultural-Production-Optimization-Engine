from dataclasses import dataclass
from typing import List

@dataclass
class SuitabilityResult:
    suitable: List[str]
    marginal: List[str]
    unsuitable: List[str]
