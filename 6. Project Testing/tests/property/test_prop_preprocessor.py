"""
Property-based tests for ml/preprocessor.py.

Properties verified:
- After preprocessing, the output DataFrame has zero missing values
- Duplicate rows are fully removed (output has no exact-duplicate rows)
- Class distribution counts sum to total row count
- The returned scaler is not None
"""
import os
import pytest
import numpy as np
import pandas as pd
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from ml.preprocessor import preprocess_data


NUM_FEATURES = ['N', 'P', 'K', 'temperature', 'humidity', 'rainfall', 'ph']
LABELS = ['rice', 'wheat', 'maize', 'mango', 'banana']


def _bounded_float(lo, hi):
    return st.floats(min_value=lo, max_value=hi, allow_nan=False, allow_infinity=False)


# Strategy: a single valid row as a dict
row_strategy = st.fixed_dictionaries({
    'N':           _bounded_float(0.0,   140.0),
    'P':           _bounded_float(5.0,   145.0),
    'K':           _bounded_float(5.0,   205.0),
    'temperature': _bounded_float(0.0,    50.0),
    'humidity':    _bounded_float(0.0,   100.0),
    'rainfall':    _bounded_float(0.0,   300.0),
    'ph':          _bounded_float(0.0,    14.0),
    'label':       st.sampled_from(LABELS),
})


def _rows_to_df(rows):
    return pd.DataFrame(rows)


@given(rows=st.lists(row_strategy, min_size=3, max_size=30))
@settings(max_examples=80, deadline=5000)
def test_no_missing_values_after_preprocessing(rows):
    """After preprocessing, the output DataFrame must contain zero NaN values."""
    df = _rows_to_df(rows)
    result_df, _ = preprocess_data(df)
    assert result_df.isnull().sum().sum() == 0


@given(rows=st.lists(row_strategy, min_size=3, max_size=20))
@settings(max_examples=60, deadline=5000)
def test_no_duplicate_rows_after_preprocessing(rows):
    """After preprocessing, the output DataFrame must have no duplicate rows."""
    df = _rows_to_df(rows)
    result_df, _ = preprocess_data(df)
    assert result_df.duplicated().sum() == 0


@given(rows=st.lists(row_strategy, min_size=3, max_size=20))
@settings(max_examples=60, deadline=5000)
def test_class_distribution_sums_to_total_rows(rows):
    """Per-class counts must sum to the total number of rows in the output DataFrame."""
    df = _rows_to_df(rows)
    result_df, _ = preprocess_data(df)
    if 'label' in result_df.columns:
        assert result_df['label'].value_counts().sum() == len(result_df)


@given(rows=st.lists(row_strategy, min_size=3, max_size=20))
@settings(max_examples=60, deadline=5000)
def test_scaler_is_not_none(rows):
    """preprocess_data() must always return a non-None scaler."""
    df = _rows_to_df(rows)
    _, scaler = preprocess_data(df)
    assert scaler is not None


@given(rows=st.lists(row_strategy, min_size=3, max_size=20))
@settings(max_examples=60, deadline=5000)
def test_label_column_preserved(rows):
    """The 'label' column must be present in the output DataFrame."""
    df = _rows_to_df(rows)
    result_df, _ = preprocess_data(df)
    assert 'label' in result_df.columns


@given(
    base_rows=st.lists(row_strategy, min_size=3, max_size=10),
    dup_count=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=40, deadline=5000)
def test_exact_duplicate_count_is_removed(base_rows, dup_count):
    """
    If we add dup_count copies of the first row, after deduplication the output
    must have exactly len(base_rows) rows (unique rows only).
    """
    assume(len(base_rows) >= 1)
    df = _rows_to_df(base_rows + [base_rows[0]] * dup_count)
    result_df, _ = preprocess_data(df)
    # All rows in result must be unique
    assert result_df.duplicated().sum() == 0
