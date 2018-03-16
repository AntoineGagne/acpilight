from hypothesis import given
from hypothesis.strategies import integers

from acpilight.acpilight import normalize


@given(integers())
def test_that_given_a_number_when_normalizing_then_respects_normalization_range(value):
    new_value = normalize(value, 0, 100)

    assert 0 <= new_value <= 100
