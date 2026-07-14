import os
import pandas as pd
import logging
from ml.exceptions import ConfigurationError, DataIngestionError, DataParseError

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ['N', 'P', 'K', 'temperature', 'humidity', 'rainfall', 'ph', 'label']
NUMERIC_COLUMNS  = ['N', 'P', 'K', 'temperature', 'humidity', 'rainfall', 'ph']

COLUMN_RANGES = {
    'N':           (0.0,   140.0),
    'P':           (5.0,   145.0),
    'K':           (5.0,   205.0),
    'temperature': (0.0,    50.0),
    'humidity':    (0.0,   100.0),
    'rainfall':    (0.0,   300.0),
    'ph':          (0.0,    14.0),
}


def _validate_schema(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise DataParseError(f"Dataset is missing required columns: {missing}")


def _validate_types(df: pd.DataFrame) -> None:
    for col in NUMERIC_COLUMNS:
        if col not in df.columns:
            continue
        non_numeric = pd.to_numeric(df[col], errors='coerce').isna()
        if non_numeric.any():
            raise DataParseError(f"Column '{col}' contains non-numeric values in rows: {df.index[non_numeric].tolist()}")


def _validate_ranges(df: pd.DataFrame) -> None:
    violations = []
    for col, (min_val, max_val) in COLUMN_RANGES.items():
        if col not in df.columns:
            continue
        out_of_range = df[(df[col] < min_val) | (df[col] > max_val)]
        if not out_of_range.empty:
            violations.append(f"Column '{col}': {len(out_of_range)} row(s) outside [{min_val}, {max_val}]")

    if violations:
        logger.warning(f"Range violations found: {violations}")
        # Non-fatal — just warn; rows will be clipped in preprocessor


def ingest_data() -> pd.DataFrame:
    dataset_path = os.environ.get('DATASET_PATH')
    if not dataset_path:
        raise ConfigurationError("Environment variable 'DATASET_PATH' is missing.")

    if not os.path.exists(dataset_path):
        raise DataIngestionError(f"Dataset file not found at path: {dataset_path}")

    try:
        df = pd.read_csv(dataset_path)
    except Exception as e:
        raise DataParseError(f"Failed to parse CSV at {dataset_path}: {str(e)}")

    if df.empty or len(df.columns) == 0:
        raise DataParseError(f"DataFrame loaded from {dataset_path} is empty or has no columns.")

    _validate_schema(df)
    _validate_types(df)
    _validate_ranges(df)

    logger.info(f"Successfully loaded dataset from {dataset_path}. Rows: {len(df)}, Columns: {len(df.columns)}")
    return df
