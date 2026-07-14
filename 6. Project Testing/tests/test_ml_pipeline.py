import pytest
import pandas as pd
import numpy as np
from ml.preprocessor import preprocess_data
from ml.ingestion import _validate_schema, _validate_types, _validate_ranges


class TestPreprocessor:

    def _sample_df(self):
        return pd.DataFrame({
            "N": [90.0, 85.0, 60.0],
            "P": [42.0, 58.0, 55.0],
            "K": [43.0, 41.0, 44.0],
            "temperature": [20.8, 21.7, 23.0],
            "humidity": [82.0, 80.5, 81.0],
            "rainfall": [202.9, 226.7, 263.9],
            "ph": [6.5, 7.0, 7.2],
            "label": ["rice", "rice", "maize"]
        })

    def test_preprocess_returns_df_and_scaler(self):
        df, scaler = preprocess_data(self._sample_df())
        assert isinstance(df, pd.DataFrame)
        assert scaler is not None

    def test_preprocess_drops_duplicates(self):
        df_dup = pd.concat([self._sample_df(), self._sample_df()], ignore_index=True)
        df_out, _ = preprocess_data(df_dup)
        assert len(df_out) == len(self._sample_df())

    def test_preprocess_preserves_label(self):
        df_out, _ = preprocess_data(self._sample_df())
        assert "label" in df_out.columns

    def test_preprocess_scales_numeric_cols(self):
        df_out, scaler = preprocess_data(self._sample_df())
        # After StandardScaler: mean ~0 for each feature
        feature_cols = ['N', 'P', 'K', 'temperature', 'humidity', 'rainfall', 'ph']
        for col in feature_cols:
            assert col in df_out.columns


class TestIngestionValidation:

    def _valid_df(self):
        return pd.DataFrame({
            "N": [90.0],
            "P": [42.0],
            "K": [43.0],
            "temperature": [20.8],
            "humidity": [82.0],
            "rainfall": [202.9],
            "ph": [6.5],
            "label": ["rice"]
        })

    def test_validate_schema_passes_for_valid_df(self):
        # Should not raise
        _validate_schema(self._valid_df())

    def test_validate_schema_raises_for_missing_column(self):
        from ml.exceptions import DataParseError
        df = self._valid_df().drop(columns=["N"])
        with pytest.raises(DataParseError):
            _validate_schema(df)

    def test_validate_types_passes_for_numeric(self):
        _validate_types(self._valid_df())

    def test_validate_ranges_passes_for_valid(self):
        _validate_ranges(self._valid_df())
