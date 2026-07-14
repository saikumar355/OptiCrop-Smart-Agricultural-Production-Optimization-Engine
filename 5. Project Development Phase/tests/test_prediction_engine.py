import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from app.ml.prediction_engine import PredictionEngine
from app.models.prediction_result import PredictionResult


class TestPredictionEngine:

    def _make_engine(self):
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array(["rice"])
        mock_model.predict_proba.return_value = np.array([[0.1, 0.8, 0.1]])

        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = np.array([[0.1] * 7])

        with patch("builtins.open", MagicMock()), \
             patch("pickle.load", side_effect=[mock_model, mock_scaler]):
            with patch("os.path.exists", return_value=True):
                engine = PredictionEngine.__new__(PredictionEngine)
                engine.model = mock_model
                engine.scaler = mock_scaler

        return engine

    def test_predict_returns_prediction_result(self):
        engine = self._make_engine()
        result = engine.predict([90.0, 42.0, 43.0, 20.8, 82.0, 202.9, 6.5])
        assert isinstance(result, PredictionResult)
        assert result.predicted_label == "rice"
        assert 0.0 <= result.confidence_score <= 1.0

    def test_predict_raises_on_wrong_input_length(self):
        engine = self._make_engine()
        with pytest.raises(ValueError, match="Expected input vector of length 7"):
            engine.predict([1.0, 2.0, 3.0])

    def test_predict_raises_on_non_numeric_input(self):
        engine = self._make_engine()
        with pytest.raises(ValueError):
            engine.predict(["a", "b", "c", "d", "e", "f", "g"])
