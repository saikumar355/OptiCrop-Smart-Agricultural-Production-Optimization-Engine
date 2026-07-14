"""
Tests for ml/model_selector.py — best-model selection logic.
"""
import json
import os
import numpy as np
import pytest
from unittest.mock import patch
from sklearn.dummy import DummyClassifier
from sklearn.preprocessing import StandardScaler
from ml.model_selector import select_and_save_best_model


def _dummy_model():
    """A real picklable sklearn estimator for serialization tests."""
    clf = DummyClassifier(strategy='most_frequent')
    clf.fit(np.array([[1]]), np.array([0]))
    return clf


def _dummy_scaler():
    scaler = StandardScaler()
    scaler.fit(np.array([[1, 2, 3, 4, 5, 6, 7]]))
    return scaler


def _report(entries):
    """Build an evaluation report dict from (name, f1, precision) tuples."""
    report = {}
    for name, f1, precision in entries:
        report[name] = {
            'f1_weighted_mean': f1,
            'precision_weighted': precision,
            'best_model': _dummy_model(),
        }
    return report


class TestModelSelector:

    def _run(self, report, tmp_path):
        """Run select_and_save_best_model using a temp registry path."""
        with patch.dict(os.environ, {'MODEL_REGISTRY_PATH': str(tmp_path)}):
            select_and_save_best_model(report, _dummy_scaler())
        return json.loads((tmp_path / 'metadata.json').read_text())

    def test_highest_f1_is_selected(self, tmp_path):
        report = _report([('ModelA', 0.90, 0.88), ('ModelB', 0.95, 0.91)])
        meta = self._run(report, tmp_path)
        assert meta['model_name'] == 'ModelB'

    def test_precision_tiebreak(self, tmp_path):
        report = _report([('ModelA', 0.95, 0.88), ('ModelB', 0.95, 0.92)])
        meta = self._run(report, tmp_path)
        assert meta['model_name'] == 'ModelB'

    def test_alphabetical_tiebreak(self, tmp_path):
        report = _report([('Zebra', 0.95, 0.90), ('Alpha', 0.95, 0.90)])
        meta = self._run(report, tmp_path)
        assert meta['model_name'] == 'Alpha'

    def test_excluded_error_models_are_skipped(self, tmp_path):
        report = _report([('GoodModel', 0.88, 0.85)])
        report['BrokenModel'] = {'error': 'Training failed'}
        meta = self._run(report, tmp_path)
        assert meta['model_name'] == 'GoodModel'

    def test_no_valid_models_raises(self, tmp_path):
        report = {'BadModel': {'error': 'failed'}}
        with patch.dict(os.environ, {'MODEL_REGISTRY_PATH': str(tmp_path)}):
            with pytest.raises(ValueError, match="No valid models"):
                select_and_save_best_model(report, _dummy_scaler())

    def test_metadata_json_written_correctly(self, tmp_path):
        report = _report([('ExtraTrees', 0.93, 0.91)])
        meta = self._run(report, tmp_path)
        assert 'model_name' in meta
        assert 'f1_weighted' in meta
        assert 'serialization_timestamp' in meta
        assert 'model_path' in meta
        assert 'scaler_path' in meta

    def test_f1_score_in_metadata_matches(self, tmp_path):
        report = _report([('RandomForest', 0.89, 0.87)])
        meta = self._run(report, tmp_path)
        assert abs(meta['f1_weighted'] - 0.89) < 1e-6

    def test_artifacts_created_on_disk(self, tmp_path):
        report = _report([('DecisionTree', 0.82, 0.80)])
        self._run(report, tmp_path)
        pkl_files = list(tmp_path.glob('DecisionTree_*.pkl'))
        scaler_files = list(tmp_path.glob('scaler_*.pkl'))
        assert len(pkl_files) == 1
        assert len(scaler_files) == 1
