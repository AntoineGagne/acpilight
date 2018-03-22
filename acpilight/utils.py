"""Contains utilities functions."""

from typing import TypeVar


T = TypeVar('T')


def normalize(value: T, minimum_value: T, maximum_value: T) -> T:
    """Normalize a value so that it doesn't exceed a given range.

    .. note::

        Supports all ordered types.

    :param value: The value to normalize
    :param minimum_value: The minimum value that ``value`` can take
    :param maximum_value: The maximum value that ``value`` can take
    :returns: If the value is between the minimum and maximum value, then
              returns the value. Otherwise, returns one of the bounds.

    :Example:

    >>> normalize(-5, 0, 100)
    0
    """
    return max(min(value, maximum_value), minimum_value)
