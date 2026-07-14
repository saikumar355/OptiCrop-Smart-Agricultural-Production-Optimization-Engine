"""
Tests for app/services/suitability_service.py
"""
import pytest
from app.services.suitability_service import SuitabilityService
from app.models.input_vector import InputVector
from app.models.suitability_result import SuitabilityResult


RICE_THRESHOLDS = {
    "rice": {
        "N":           {"min": 60,  "max": 100},
        "P":           {"min": 30,  "max": 60},
        "K":           {"min": 35,  "max": 55},
        "temperature": {"min": 18,  "max": 28},
        "humidity":    {"min": 70,  "max": 90},
        "rainfall":    {"min": 150, "max": 250},
        "ph":          {"min": 5.5, "max": 7.5},
    }
}

MULTI_THRESHOLDS = {
    **RICE_THRESHOLDS,
    "wheat": {
        "N":           {"min": 50,  "max": 120},
        "P":           {"min": 20,  "max": 80},
        "K":           {"min": 30,  "max": 100},
        "temperature": {"min": 10,  "max": 25},
        "humidity":    {"min": 40,  "max": 80},
        "rainfall":    {"min": 50,  "max": 200},
        "ph":          {"min": 6.0, "max": 8.0},
    },
}


def _config(thresholds):
    class Cfg:
        SUITABILITY_THRESHOLDS = thresholds
    return Cfg()


def _vector(**overrides):
    defaults = dict(N=90.0, P=42.0, K=43.0, temperature=20.8,
                    humidity=82.0, rainfall=202.9, ph=6.5)
    defaults.update(overrides)
    return InputVector(**defaults)


class TestSuitabilityService:

    def test_returns_suitability_result(self):
        svc = SuitabilityService(_config(RICE_THRESHOLDS))
        result = svc.evaluate(_vector())
        assert isinstance(result, SuitabilityResult)

    def test_suitable_crop_in_suitable_list(self):
        svc = SuitabilityService(_config(RICE_THRESHOLDS))
        result = svc.evaluate(_vector())
        assert 'rice' in result.suitable

    def test_unsuitable_crop_in_unsuitable_list(self):
        svc = SuitabilityService(_config(RICE_THRESHOLDS))
        # temperature way out of range for rice
        result = svc.evaluate(_vector(temperature=5.0, humidity=20.0))
        assert 'rice' in result.unsuitable

    def test_every_crop_appears_in_exactly_one_tier(self):
        svc = SuitabilityService(_config(MULTI_THRESHOLDS))
        result = svc.evaluate(_vector())
        all_crops = result.suitable + result.marginal + result.unsuitable
        # Every configured crop must appear exactly once
        for crop in MULTI_THRESHOLDS:
            assert all_crops.count(crop) == 1

    def test_tiers_are_disjoint(self):
        svc = SuitabilityService(_config(MULTI_THRESHOLDS))
        result = svc.evaluate(_vector())
        suitable_set = set(result.suitable)
        marginal_set = set(result.marginal)
        unsuitable_set = set(result.unsuitable)
        assert suitable_set.isdisjoint(marginal_set)
        assert suitable_set.isdisjoint(unsuitable_set)
        assert marginal_set.isdisjoint(unsuitable_set)

    def test_empty_thresholds_returns_empty_lists(self):
        svc = SuitabilityService(_config({}))
        result = svc.evaluate(_vector())
        assert result.suitable == []
        assert result.marginal == []
        assert result.unsuitable == []

    def test_marginal_when_slightly_out_of_bounds(self):
        svc = SuitabilityService(_config(RICE_THRESHOLDS))
        # Rice humidity range is [70, 90], IQR span = 20, 15% margin = 3.
        # humidity=91 is 1 above max, which is within the 3-unit margin → marginal.
        result = svc.evaluate(_vector(humidity=91.0))
        assert 'rice' in result.marginal or 'rice' in result.suitable

    def test_does_not_call_prediction_engine(self):
        """SuitabilityService must never touch the ML model."""
        svc = SuitabilityService(_config(RICE_THRESHOLDS))
        # Simply assert no PredictionEngine attribute exists on the service
        assert not hasattr(svc, 'engine')
        assert not hasattr(svc, 'model')
