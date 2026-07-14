import pytest
from unittest.mock import MagicMock
from app.services.recommendation_service import RecommendationService
from app.models.input_vector import InputVector
from app.models.prediction_result import PredictionResult


class TestRecommendationService:

    def _make_service(self, predicted_label="rice", confidence=0.92, model_name="ExtraTrees_ts"):
        mock_engine = MagicMock()
        mock_engine.predict.return_value = PredictionResult(
            predicted_label=predicted_label,
            confidence_score=confidence,
        )
        mock_engine.model_name = model_name

        mock_repo = MagicMock()
        mock_repo.save.return_value = None

        service = RecommendationService(engine=mock_engine, repo=mock_repo)
        return service, mock_engine, mock_repo

    def _valid_vector(self):
        return InputVector(N=90.0, P=42.0, K=43.0, temperature=20.8,
                           humidity=82.0, rainfall=202.9, ph=6.5)

    def test_recommend_returns_tuple(self):
        service, engine, repo = self._make_service()
        result, model_name = service.recommend(self._valid_vector(), hashed_ip="abc123")
        assert isinstance(result, PredictionResult)
        assert isinstance(model_name, str)

    def test_recommend_returns_correct_label(self):
        service, engine, repo = self._make_service()
        result, _ = service.recommend(self._valid_vector(), hashed_ip="abc123")
        assert result.predicted_label == "rice"

    def test_recommend_model_name_from_engine(self):
        service, engine, repo = self._make_service(model_name="ExtraTrees_ts")
        _, model_name = service.recommend(self._valid_vector(), hashed_ip="abc123")
        assert model_name == "ExtraTrees_ts"

    def test_recommend_calls_engine_predict_once(self):
        service, engine, repo = self._make_service()
        service.recommend(self._valid_vector(), hashed_ip="abc123")
        engine.predict.assert_called_once()

    def test_recommend_saves_to_repo(self):
        service, engine, repo = self._make_service()
        service.recommend(self._valid_vector(), hashed_ip="abc123")
        repo.save.assert_called_once()

    def test_recommend_passes_correct_features_to_engine(self):
        service, engine, repo = self._make_service()
        vector = self._valid_vector()
        service.recommend(vector, hashed_ip="abc123")
        call_args = engine.predict.call_args[0][0]
        assert call_args[0] == vector.N
        assert call_args[6] == vector.ph

    def test_recommend_record_uses_real_model_name(self):
        service, engine, repo = self._make_service(model_name="MyModel_v2")
        service.recommend(self._valid_vector(), hashed_ip="abc123")
        saved_record = repo.save.call_args[0][0]
        assert saved_record.model_name == "MyModel_v2"
        assert saved_record.model_name != "ActiveModel"

    def test_recommend_hashed_ip_stored_in_record(self):
        service, engine, repo = self._make_service()
        service.recommend(self._valid_vector(), hashed_ip="deadbeef1234")
        saved_record = repo.save.call_args[0][0]
        assert saved_record.hashed_ip == "deadbeef1234"
