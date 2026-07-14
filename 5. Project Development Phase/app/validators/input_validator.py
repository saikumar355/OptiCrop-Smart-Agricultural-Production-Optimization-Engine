import html
from typing import Dict, Union, Any
from app.models.input_vector import InputVector, FIELD_RANGES

class ValidationError(Exception):
    def __init__(self, fields: Dict[str, str]):
        self.fields = fields
        super().__init__("Validation failed")

class InputValidator:
    @staticmethod
    def validate(data: Dict[str, Any]) -> Union[InputVector, ValidationError]:
        errors = {}
        validated_data = {}
        
        required_fields = ['N', 'P', 'K', 'temperature', 'humidity', 'rainfall', 'ph']
        
        for field in required_fields:
            if field not in data or data[field] is None or str(data[field]).strip() == "":
                errors[field] = "Field is required."
                continue
                
            raw_value = str(data[field]).strip()
            
            try:
                float_val = float(raw_value)
            except ValueError:
                errors[field] = "Numeric value required."
                continue
                
            min_val, max_val = FIELD_RANGES[field]
            if not (min_val <= float_val <= max_val):
                errors[field] = f"Value {float_val} is outside valid range [{min_val}, {max_val}]."
                continue
                
            # HTML escape is mostly for strings, but since these are floats, there is no real string payload.
            # However, if any text field is added later, we escape it. For now, it's just float parsing.
            # "HTML-escape all string values before logging or storage using html.escape()"
            # We don't have strings here except the parsed floats. Let's just be safe.
            # The prompt implies we might have string inputs? No, all 7 fields are float.
            
            validated_data[field] = float_val
            
        if errors:
            # We raise or return? Task says "-> InputVector | ValidationError"
            # It's better to return the error or raise it. The controller handles it.
            # We will return the ValidationError instance.
            return ValidationError(errors)
            
        return InputVector(**validated_data)
