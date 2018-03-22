from io import StringIO
from unittest import mock

from hypothesis import given
from hypothesis.strategies import integers
from typing import IO, AnyStr

from acpilight.acpilight import normalize, Controller


@given(integers())
def test_that_given_a_number_when_normalizing_then_respects_normalization_range(value: int):
    new_value = normalize(value, 0, 100)

    assert 0 <= new_value <= 100


@given(integers(), integers(min_value=0))
def test_that_given_two_brightness_file_when_setting_percent_brightness_value_then_value_does_not_exceed_valid_range(value: int, max_brightness_value: int):
    brightness_file: IO[AnyStr] = mock.create_autospec(StringIO)
    max_brightness_file: IO[AnyStr] = StringIO(str(max_brightness_value))

    controller = Controller(brightness_file, max_brightness_file)
    controller.brightness = value

    assert 0 <= int(brightness_file.write.call_args[0][0]) <= max_brightness_value
