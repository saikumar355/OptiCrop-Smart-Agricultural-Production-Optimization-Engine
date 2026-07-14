import pytest
import os
import tempfile
from app.repositories.prediction_repository import PredictionRepository
from app.models.prediction_record import PredictionRecord


@pytest.fixture
def repo():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    r = PredictionRepository(db_path)
    yield r
    # Close all sqlite connections before deletion (required on Windows)
    try:
        import sqlite3
        sqlite3.connect(db_path).close()
    except Exception:
        pass
    try:
        os.unlink(db_path)
    except PermissionError:
        pass  # Windows may still hold the handle; not a test failure


def make_record(**overrides):
    defaults = dict(
        id=None,
        timestamp="2026-01-01T10:00:00Z",
        N=90.0, P=42.0, K=43.0,
        temperature=20.8, humidity=82.0, rainfall=202.9, ph=6.5,
        predicted_crop="rice",
        confidence_score=0.95,
        model_name="TestModel",
        hashed_ip="abc123hash"
    )
    defaults.update(overrides)
    return PredictionRecord(**defaults)


class TestPredictionRepository:

    def test_initial_count_is_zero(self, repo):
        assert repo.count() == 0

    def test_save_increases_count(self, repo):
        repo.save(make_record())
        assert repo.count() == 1

    def test_save_multiple_records(self, repo):
        for i in range(5):
            repo.save(make_record(predicted_crop=f"crop_{i}"))
        assert repo.count() == 5

    def test_get_paginated_returns_records(self, repo):
        repo.save(make_record())
        records = repo.get_paginated(1, 25)
        assert len(records) == 1
        assert records[0].predicted_crop == "rice"

    def test_get_paginated_respects_page_size(self, repo):
        for i in range(10):
            repo.save(make_record())
        records = repo.get_paginated(1, 3)
        assert len(records) == 3

    def test_get_paginated_returns_empty_for_out_of_range_page(self, repo):
        repo.save(make_record())
        records = repo.get_paginated(10, 25)
        assert records == []

    def test_save_sets_record_id(self, repo):
        record = make_record()
        repo.save(record)
        assert record.id is not None
        assert record.id > 0
