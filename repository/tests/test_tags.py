from repository.templatetags.observation_filters import (
    format_magnitude,
    round_uncertainty,
)


def test_round_uncertainty():
    test_cases = [
        (0, "0"),
        (0.123, "0.12"),
        (0.234, "0.23"),
        (0.345, "0.3"),
        (0.0123, "0.012"),
        (0.0345, "0.03"),
    ]
    for input_val, expected in test_cases:
        assert round_uncertainty(input_val) == expected


def test_format_magnitude():
    test_cases = [
        (None, None, ""),  # Test None values
        (12.345, None, ""),
        (12.345, 0, "12.345"),
        (12.345, 0.123, "12.35"),
        (12.345, 0.023, "12.345"),
        (12.345, 0.5, "12.3"),
        (12.345, 0.95, "12.3"),
        (12.0, 0.1, "12.0"),
    ]

    for value, uncertainty, expected in test_cases:
        assert format_magnitude(value, uncertainty) == expected
