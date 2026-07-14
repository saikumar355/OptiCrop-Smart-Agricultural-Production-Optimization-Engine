"""
Property-based tests for ml/model_selector.py.

Properties verified:
- The selected model always has the highest F1-weighted score
- When F1 scores tie, the model with higher precision is always selected
- When both F1 and precision tie, the alphabetically first name is selected
- metadata.json always contains required keys after a successful run
"""
import json
import os
import tempfile
import numpy as np
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st
from unittest.mock import patch
from sklearn.dummy import DummyClassifier
from sklearn.preprocessing import StandardScaler

from ml.model_selector import select_and_save_best_model


def _dummy_model():
    """A real, picklable sklearn estimator."""
    clf = DummyClassifier(strategy='most_frequent')
    clf.fit(np.array([[1]]), np.array([0]))
    return clf


def _dummy_scaler():
    """A real, picklable sklearn scaler."""
    scaler = StandardScaler()
    scaler.fit(np.array([[1, 2, 3, 4, 5, 6, 7]]))
    return scaler


def _report_from_scores(scores: dict) -> dict:
    return {
        name: {
            'f1_weighted_mean': f1,
            'precision_weighted': prec,
            'best_model': _dummy_model(),
        }
        for name, (f1, prec) in scores.items()
    }


def _run(report) -> dict:
    """Run selector in a fresh temp directory; return parsed metadata.json."""
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, {'MODEL_REGISTRY_PATH': tmp}):
            select_and_save_best_model(report, _dummy_scaler())
        return json.loads(open(os.path.join(tmp, 'metadata.json')).read())


# Strategy: 2-5 model entries with valid F1 and precision scores
model_scores_strategy = st.dictionaries(
    keys=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=3, max_size=12),
    values=st.tuples(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    ),
    min_size=2,
    max_size=5,
)


@given(scores=model_scores_strategy)
@settings(max_examples=100, deadline=10000)
def test_selected_model_has_max_f1(scores):
    """The model chosen must always have the globally highest F1-weighted score."""
    report = _report_from_scores(scores)
    meta = _run(report)
    best_f1 = meta['f1_weighted']
    max_f1 = max(f1 for f1, _ in scores.values())
    assert abs(best_f1 - max_f1) < 1e-9


@given(
    name_a=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=3, max_size=10),
    name_b=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=3, max_size=10),
    f1=st.floats(min_value=0.5, max_value=1.0, allow_nan=False),
    prec_a=st.floats(min_value=0.0, max_value=0.79, allow_nan=False),
    delta=st.floats(min_value=0.01, max_value=0.19, allow_nan=False),
)
@settings(max_examples=80, deadline=10000)
def test_precision_tiebreak_selects_higher_precision(name_a, name_b, f1, prec_a, delta):
    """When F1 scores are equal, higher precision wins."""
    assume(name_a != name_b)
    prec_b = min(prec_a + delta, 1.0)
    assume(prec_b > prec_a)
    scores = {name_a: (f1, prec_a), name_b: (f1, prec_b)}
    meta = _run(_report_from_scores(scores))
    assert meta['model_name'] == name_b


@given(
    name_a=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=3, max_size=10),
    name_b=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=3, max_size=10),
    f1=st.floats(min_value=0.5, max_value=1.0, allow_nan=False),
    prec=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
@settings(max_examples=80, deadline=10000)
def test_alphabetical_tiebreak(name_a, name_b, f1, prec):
    """When F1 and precision both tie, alphabetically first name wins."""
    assume(name_a != name_b)
    assume(name_a.lower() != name_b.lower())
    scores = {name_a: (f1, prec), name_b: (f1, prec)}
    meta = _run(_report_from_scores(scores))
    expected = min(name_a.lower(), name_b.lower())
    assert meta['model_name'].lower() == expected


@given(scores=model_scores_strategy)
@settings(max_examples=80, deadline=10000)
def test_metadata_always_has_required_keys(scores):
    """metadata.json must always contain all required keys."""
    report = _report_from_scores(scores)
    meta = _run(report)
    for key in ('model_name', 'f1_weighted', 'serialization_timestamp', 'model_path', 'scaler_path'):
        assert key in meta
