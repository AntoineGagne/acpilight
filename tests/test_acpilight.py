from io import StringIO
from unittest import mock

from hypothesis import given
from hypothesis.strategies import integers

from acpilight.acpilight import normalize, Controller, generate_brightness_steps


@given(integers())
def test_that_given_a_number_when_normalizing_then_respects_normalization_range(value: int):
    new_value = normalize(value, 0, 100)

    assert 0 <= new_value <= 100


@given(integers(), integers(min_value=0))
def test_that_given_two_brightness_file_when_setting_percent_brightness_value_then_value_does_not_exceed_valid_range(value: int, max_brightness_value: int):
    brightness_file = mock.create_autospec(StringIO)
    max_brightness_file = StringIO(str(max_brightness_value))

    controller = Controller(brightness_file, max_brightness_file)
    controller.brightness = value

    assert 0 <= int(brightness_file.write.call_args[0][0]) <= max_brightness_value


@given(integers(min_value=10, max_value=100), integers(min_value=0, max_value=10))
def test_that_given_a_controller_and_a_target_brightness_and_a_amount_of_steps_when_generating_brightness_steps_then_all_steps_are_inferior_or_equals_to_the_target(target_brightness, steps):
    brightness_file = StringIO('0')
    max_brightness_file = StringIO('100')

    controller = Controller(brightness_file, max_brightness_file)

    assert all(
        step <= target_brightness
        for step in generate_brightness_steps(controller, target_brightness, steps)
    )
