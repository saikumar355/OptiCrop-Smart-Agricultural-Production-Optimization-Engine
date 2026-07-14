import logging
from typing import Dict, Any
from app.models.input_vector import InputVector

logger = logging.getLogger(__name__)

FEATURE_LABELS = {
    'N': 'Nitrogen (N)',
    'P': 'Phosphorus (P)',
    'K': 'Potassium (K)',
    'temperature': 'Temperature',
    'humidity': 'Humidity',
    'rainfall': 'Rainfall',
    'ph': 'Soil pH',
}


class SuitabilityService:
    def __init__(self, config) -> None:
        # config may be a Flask app.config dict or a config class object
        if isinstance(config, dict):
            self.thresholds = config.get('SUITABILITY_THRESHOLDS', {})
        else:
            self.thresholds = getattr(config, 'SUITABILITY_THRESHOLDS', {})

    def evaluate_crop(self, crop: str, input_vector: InputVector) -> Dict[str, Any]:
        """
        Evaluate a single target crop against the input vector.
        Returns a dict shaped for the frontend:
          {
            crop, is_suitable, feedback,
            issues: { feature: { status, feedback } }
          }
        """
        bounds = self.thresholds.get(crop)
        if not bounds:
            return {
                "crop": crop,
                "is_suitable": False,
                "feedback": f"No threshold data available for {crop.capitalize()}.",
                "issues": {},
            }

        issues: Dict[str, Any] = {}
        out_of_bounds = 0
        marginal_count = 0

        for feature in ['N', 'P', 'K', 'temperature', 'humidity', 'rainfall', 'ph']:
            val = getattr(input_vector, feature)
            label = FEATURE_LABELS.get(feature, feature)

            if feature not in bounds:
                continue

            f_min = bounds[feature].get('min', 0)
            f_max = bounds[feature].get('max', 9999)

            if f_min <= val <= f_max:
                issues[label] = {
                    "status": "suitable",
                    "feedback": f"{val} is within optimal range [{f_min}–{f_max}].",
                }
            else:
                margin = 0.15 * (f_max - f_min) if f_max != f_min else 0.15 * abs(f_min)
                if (f_min - margin) <= val <= (f_max + margin):
                    marginal_count += 1
                    issues[label] = {
                        "status": "marginal",
                        "feedback": (
                            f"{val} is slightly outside the optimal range [{f_min}–{f_max}]. "
                            "Marginal — may need adjustment."
                        ),
                    }
                else:
                    out_of_bounds += 1
                    issues[label] = {
                        "status": "unsuitable",
                        "feedback": (
                            f"{val} is outside the acceptable range [{f_min}–{f_max}]. "
                            "This condition is unsuitable."
                        ),
                    }

        if out_of_bounds == 0 and marginal_count == 0:
            is_suitable = True
            feedback = (
                f"All parameters are within optimal range for {crop.capitalize()}. "
                "Your land is highly suitable."
            )
        elif out_of_bounds == 0:
            is_suitable = True
            feedback = (
                f"{crop.capitalize()} is marginally suitable. "
                f"{marginal_count} parameter(s) are slightly off — consider minor adjustments."
            )
        else:
            is_suitable = False
            feedback = (
                f"{crop.capitalize()} is not suitable for these conditions. "
                f"{out_of_bounds} parameter(s) are outside acceptable limits."
            )

        logger.info(
            "Suitability evaluated. Crop=%s suitable=%s out_of_bounds=%d marginal=%d",
            crop, is_suitable, out_of_bounds, marginal_count,
        )

        return {
            "crop": crop,
            "is_suitable": is_suitable,
            "feedback": feedback,
            "issues": issues,
        }

    # Keep old method for backward compatibility with tests
    def evaluate(self, input_vector: InputVector):
        from app.models.suitability_result import SuitabilityResult
        suitable, marginal, unsuitable = [], [], []
        for crop in self.thresholds:
            result = self.evaluate_crop(crop, input_vector)
            if result['is_suitable'] and 'slightly' not in result['feedback']:
                suitable.append(crop)
            elif result['is_suitable']:
                marginal.append(crop)
            else:
                unsuitable.append(crop)
        return SuitabilityResult(suitable=suitable, marginal=marginal, unsuitable=unsuitable)
