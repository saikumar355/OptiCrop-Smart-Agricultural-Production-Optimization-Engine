"""
Property-based tests for PredictionRepository.

Properties verified:
- count() always equals the number of records saved
- get_paginated() never returns more than page_size records
- get_paginated() never exposes hashed_ip (structural — field must exist but is internal)
- Records are returned in descending timestamp order
"""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.repositories.prediction_repository import PredictionRepository
from app.models.prediction_record import PredictionRecord


def _make_record(ts: str = "2026-01-01T10:00:00Z", crop: str = "rice") -> PredictionRecord:
    return PredictionRecord(
        id=None, timestamp=ts,
        N=90.0, P=42.0, K=43.0, temperature=20.8,
        humidity=82.0, rainfall=202.9, ph=6.5,
        predicted_crop=crop, confidence_score=0.95,
        model_name="TestModel", hashed_ip="deadbeefhash",
    )


@pytest.fixture
def mem_repo():
    return PredictionRepository(':memory:')


@given(n=st.integers(min_value=0, max_value=50))
@settings(max_examples=50)
def test_count_equals_saves(n):
    """After saving n records, count() must equal n."""
    repo = PredictionRepository(':memory:')
    for _ in range(n):
        repo.save(_make_record())
    assert repo.count() == n


@given(
    n=st.integers(min_value=1, max_value=40),
    page_size=st.integers(min_value=1, max_value=20),
)
@settings(max_examples=80)
def test_paginated_never_exceeds_page_size(n, page_size):
    """get_paginated() must never return more rows than page_size."""
    repo = PredictionRepository(':memory:')
    for _ in range(n):
        repo.save(_make_record())
    records = repo.get_paginated(1, page_size)
    assert len(records) <= page_size


@given(n=st.integers(min_value=2, max_value=20))
@settings(max_examples=40)
def test_paginated_descending_timestamp_order(n):
    """
    Records saved with sequential timestamps must be returned in descending order
    (most recent first).
    """
    repo = PredictionRepository(':memory:')
    for i in range(n):
        ts = f"2026-01-{i+1:02d}T10:00:00Z"
        repo.save(_make_record(ts=ts))
    records = repo.get_paginated(1, n)
    timestamps = [r.timestamp for r in records]
    assert timestamps == sorted(timestamps, reverse=True)


@given(n=st.integers(min_value=1, max_value=30))
@settings(max_examples=40)
def test_paginated_records_have_hashed_ip_field(n):
    """
    Every record returned by get_paginated() must carry a hashed_ip attribute.
    The API layer is responsible for omitting it from responses; the repo must preserve it.
    """
    repo = PredictionRepository(':memory:')
    for _ in range(n):
        repo.save(_make_record())
    records = repo.get_paginated(1, n)
    for r in records:
        assert hasattr(r, 'hashed_ip')
        assert r.hashed_ip == "deadbeefhash"


def test_count_after_delete_all_is_zero():
    """delete_all() must result in count() == 0."""
    repo = PredictionRepository(':memory:')
    for _ in range(10):
        repo.save(_make_record())
    repo.delete_all()
    assert repo.count() == 0


def test_delete_single_record_reduces_count():
    """delete(id) must reduce count by exactly 1."""
    repo = PredictionRepository(':memory:')
    r = _make_record()
    repo.save(r)
    assert repo.count() == 1
    repo.delete(r.id)
    assert repo.count() == 0
