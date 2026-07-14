"""
Property-based tests for PredictionEngine.

Properties verified:
- predict() always returns a PredictionResult with confidence_score in [0.0, 1.0]
- predict() always raises ValueError for wrong-length inputs
- predict() always raises ValueError for non-numeric inputs
- predicted_label is always a non-empty string
"""
import numpy as np
import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from unittest.mock import MagicMock

from app.ml.prediction_engine import PredictionEngine
from app.models.prediction_result import PredictionResult


def _make_engine(predicted_label='rice', proba=None):
    """Build a PredictionEngine with mocked model and scaler."""
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([predicted_label])
    if proba is None:
        proba = [0.05] * 19 + [0.05]  # 20 classes summing to 1.0
        proba[0] = 0.05
    mock_model.predict_proba.return_value = np.array([proba])

    mock_scaler = MagicMock()
    mock_scaler.transform.return_value = np.zeros((1, 7))

    engine = PredictionEngine.__new__(PredictionEngine)
    engine.model = mock_model
    engine.scaler = mock_scaler
    engine.model_name = 'TestModel'
    return engine


# Strategy: a valid 7-element input vector
valid_vector = st.lists(
    st.floats(min_value=0.0, max_value=300.0, allow_nan=False, allow_infinity=False),
    min_size=7, max_size=7,
)


@given(vec=valid_vector)
@settings(max_examples=200)
def test_predict_always_returns_prediction_result(vec):
    """For any valid 7-element float vector, predict() must return a PredictionResult."""
    engine = _make_engine()
    result = engine.predict(vec)
    assert isinstance(result, PredictionResult)


@given(vec=valid_vector)
@settings(max_examples=200)
def test_confidence_score_always_in_unit_interval(vec):
    """confidence_score must always be in [0.0, 1.0]."""
    engine = _make_engine()
    result = engine.predict(vec)
    assert 0.0 <= result.confidence_score <= 1.0


@given(vec=valid_vector)
@settings(max_examples=100)
def test_predicted_label_always_non_empty_string(vec):
    """predicted_label must always be a non-empty string."""
    engine = _make_engine(predicted_label='maize')
    result = engine.predict(vec)
    assert isinstance(result.predicted_label, str)
    assert len(result.predicted_label) > 0


@given(
    length=st.integers(min_value=0, max_value=6) | st.integers(min_value=8, max_value=20)
)
@settings(max_examples=100)
def test_wrong_length_always_raises_value_error(length):
    """Any input vector whose length != 7 must raise ValueError."""
    engine = _make_engine()
    vec = [1.0] * length
    with pytest.raises(ValueError, match="Expected input vector of length 7"):
        engine.predict(vec)


@given(
    good=st.lists(
        st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        min_size=6, max_size=6,
    ),
    bad=st.text(min_size=1, max_size=10).filter(lambda s: not _is_numeric(s)),
)
@settings(max_examples=100)
def test_non_numeric_input_always_raises_value_error(good, bad):
    """Any non-numeric value in the vector must raise ValueError."""
    engine = _make_engine()
    vec = good + [bad]
    with pytest.raises(ValueError):
        engine.predict(vec)


def _is_numeric(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False
