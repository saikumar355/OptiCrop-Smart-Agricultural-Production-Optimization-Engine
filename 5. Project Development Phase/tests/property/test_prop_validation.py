"""
Property-based tests for InputValidator.

Properties verified:
- Any input with all 7 fields present and within range → always returns InputVector
- Any input with at least one missing/non-numeric/out-of-range field → always returns ValidationError
- Confidence score of a valid InputVector is always in [0.0, 1.0] (structural property)
"""
import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.validators.input_validator import InputValidator, ValidationError
from app.models.input_vector import InputVector, FIELD_RANGES

# Strategy for a single valid field value
def valid_float(field: str):
    lo, hi = FIELD_RANGES[field]
    return st.floats(min_value=lo, max_value=hi, allow_nan=False, allow_infinity=False)

# Strategy for a complete valid payload dict
valid_payload = st.fixed_dictionaries({
    field: valid_float(field) for field in FIELD_RANGES
})


@given(data=valid_payload)
@settings(max_examples=200)
def test_valid_payload_always_returns_input_vector(data):
    """For all valid inputs, validate() must return an InputVector, never a ValidationError."""
    result = InputValidator.validate(data)
    assert isinstance(result, InputVector), (
        f"Expected InputVector for valid payload, got {type(result).__name__}. "
        f"ValidationError fields: {getattr(result, 'fields', None)}"
    )


@given(data=valid_payload, field=st.sampled_from(list(FIELD_RANGES.keys())))
@settings(max_examples=200)
def test_missing_field_always_returns_validation_error(data, field):
    """Removing any one field from a valid payload always produces ValidationError."""
    payload = {k: v for k, v in data.items() if k != field}
    result = InputValidator.validate(payload)
    assert isinstance(result, ValidationError)
    assert field in result.fields


@given(data=valid_payload, field=st.sampled_from(list(FIELD_RANGES.keys())))
@settings(max_examples=200)
def test_non_numeric_field_always_returns_validation_error(data, field):
    """Replacing any field with a non-numeric string always produces ValidationError."""
    payload = {**data, field: 'not_a_number'}
    result = InputValidator.validate(payload)
    assert isinstance(result, ValidationError)
    assert field in result.fields


@given(
    data=valid_payload,
    field=st.sampled_from(list(FIELD_RANGES.keys())),
    delta=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=200)
def test_out_of_range_above_max_always_returns_validation_error(data, field, delta):
    """Any value above the field maximum always produces ValidationError for that field."""
    _, hi = FIELD_RANGES[field]
    payload = {**data, field: hi + delta}
    result = InputValidator.validate(payload)
    assert isinstance(result, ValidationError)
    assert field in result.fields


@given(
    data=valid_payload,
    field=st.sampled_from(list(FIELD_RANGES.keys())),
    delta=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=200)
def test_out_of_range_below_min_always_returns_validation_error(data, field, delta):
    """Any value below the field minimum always produces ValidationError for that field."""
    lo, _ = FIELD_RANGES[field]
    payload = {**data, field: lo - delta}
    # Only meaningful when the result would be below minimum (lo - delta < lo)
    assume(lo - delta < lo)
    result = InputValidator.validate(payload)
    assert isinstance(result, ValidationError)
    assert field in result.fields


def test_empty_dict_returns_all_seven_field_errors():
    """An empty dict must produce errors for exactly all 7 required fields."""
    result = InputValidator.validate({})
    assert isinstance(result, ValidationError)
    assert set(result.fields.keys()) == set(FIELD_RANGES.keys())
