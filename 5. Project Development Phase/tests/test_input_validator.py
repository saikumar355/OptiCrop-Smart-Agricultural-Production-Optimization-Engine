import pytest
from app.validators.input_validator import InputValidator, ValidationError
from app.models.input_vector import InputVector


class TestInputValidator:

    def _valid_data(self):
        return {
            "N": 90.0,
            "P": 42.0,
            "K": 43.0,
            "temperature": 20.8,
            "humidity": 82.0,
            "rainfall": 202.9,
            "ph": 6.5
        }

    def test_valid_input_returns_input_vector(self):
        result = InputValidator.validate(self._valid_data())
        assert isinstance(result, InputVector)
        assert result.N == 90.0
        assert result.ph == 6.5

    def test_missing_field_returns_validation_error(self):
        data = self._valid_data()
        del data["N"]
        result = InputValidator.validate(data)
        assert isinstance(result, ValidationError)
        assert "N" in result.fields

    def test_non_numeric_value_returns_validation_error(self):
        data = self._valid_data()
        data["N"] = "abc"
        result = InputValidator.validate(data)
        assert isinstance(result, ValidationError)
        assert "N" in result.fields

    def test_out_of_range_value_returns_validation_error(self):
        data = self._valid_data()
        data["N"] = 999.0  # exceeds max 140
        result = InputValidator.validate(data)
        assert isinstance(result, ValidationError)
        assert "N" in result.fields

    def test_boundary_values_are_valid(self):
        data = self._valid_data()
        data["N"] = 0.0
        result = InputValidator.validate(data)
        assert isinstance(result, InputVector)

    def test_empty_dict_returns_all_field_errors(self):
        result = InputValidator.validate({})
        assert isinstance(result, ValidationError)
        assert len(result.fields) == 7

    def test_none_value_returns_validation_error(self):
        data = self._valid_data()
        data["ph"] = None
        result = InputValidator.validate(data)
        assert isinstance(result, ValidationError)
        assert "ph" in result.fields
