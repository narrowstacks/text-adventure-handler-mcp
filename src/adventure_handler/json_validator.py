"""Custom JSON validation for FastMCP tools to handle both dict and JSON string inputs."""

import json
from typing import Any, Dict, Optional, Union
from pydantic import field_validator, ValidationInfo


def json_or_dict_validator(v: Union[dict, str, None]) -> Optional[dict]:
    """
    Validator that accepts either a dictionary or a JSON string and returns a dictionary.

    This validator can be used with Pydantic's field_validator to automatically
    convert JSON strings to dictionaries during validation.

    Args:
        v: Either a dictionary, JSON string, or None

    Returns:
        A dictionary if input was valid, None if input was None

    Raises:
        ValueError: If the input is a string but not valid JSON
        TypeError: If the input is neither a dict, string, nor None
    """
    if v is None:
        return None
    if isinstance(v, dict):
        return v
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            if not isinstance(parsed, dict):
                raise ValueError(f"JSON string must parse to a dictionary, got {type(parsed).__name__}")
            return parsed
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {str(e)}")
    raise TypeError(f"Expected dict, JSON string, or None; got {type(v).__name__}")


# Alternative: Using Pydantic's BeforeValidator for type coercion
from pydantic import BeforeValidator
from typing import Annotated

# Create a type alias that automatically converts JSON strings to dicts
JsonDict = Annotated[Optional[dict], BeforeValidator(json_or_dict_validator)]


# For testing purposes
if __name__ == "__main__":
    from pydantic import BaseModel

    class TestModel(BaseModel):
        data: JsonDict = None

    # Test cases
    test_cases = [
        None,
        {"key": "value"},
        '{"key": "value"}',
        '{"nested": {"data": true, "count": 42}}',
    ]

    for test in test_cases:
        try:
            model = TestModel(data=test)
            print(f"✅ Input type: {type(test).__name__:10} → Output: {model.data}")
        except Exception as e:
            print(f"❌ Input type: {type(test).__name__:10} → Error: {e}")

    # Test error cases
    error_cases = [
        '"not a dict"',  # JSON string but not a dict
        '{invalid json}',  # Invalid JSON
        123,  # Wrong type
    ]

    print("\nError cases:")
    for test in error_cases:
        try:
            model = TestModel(data=test)
            print(f"✅ Input: {test} → Output: {model.data}")
        except Exception as e:
            print(f"❌ Input: {test} → Error: {type(e).__name__}: {e}")