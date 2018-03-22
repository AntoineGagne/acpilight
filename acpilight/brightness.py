"""Contains functions and classes that are related to brightness controls."""

import os
import sys
import time
from collections import OrderedDict
from math import trunc
from typing import IO, AnyStr, MutableMapping, Optional

from acpilight.constants import MINIMUM_BRIGHTNESS_VALUE, CONTROLLERS_PATH, MAXIMUM_BRIGHTNESS_FILE, BRIGHTNESS_FILE
from acpilight.utils import normalize


def generate_brightness_steps(controller, target, steps):
    """Generate all the accurate steps to get the controller's current brightness to the target.

    :param controller: The control that control the brightness
    :param target: The target brightness value
    :param steps: The amount of steps to do before reaching the target's brightness value
    :returns: All the steps to be done to reach the target's brightness value
    """
    current = controller.brightness
    for step in range(1, steps):
        yield current + (target - current) * step / steps

    yield target


def sweep_brightness(controller, target, steps, delay):
    """Gradually increase brightness by regular steps over a certain delay up to a certain brightness.

    :param controller: The control that control the brightness
    :param target: The target brightness value
    :param steps: The amount of steps to do before reaching the target's brightness value
    :param delay: The amount of time that the operation must take
    """
    sleep = (delay / 1000.) / steps
    for value in generate_brightness_steps(controller, target, steps):
        controller.brightness = value
        time.sleep(sleep)


class Controller:
    """Controls the brightness of a specific device.

    It controls the brightness of a specific device by writing to its corresponding ``brightness`` file.

    :Example:

    >>> from io import StringIO
    >>> brightness_file = StringIO('5')
    >>> max_brightness_file = StringIO('100')
    >>> controller = Controller(brightness_file, max_brightness_file)
    >>> controller.raw_brightness = 15
    >>> controller.raw_brightness
    15
    """

    def __init__(self, brightness_file: IO[AnyStr], maximum_brightness_file: IO[AnyStr]) -> None:
        self._brightness_file: IO = brightness_file
        self._max_brightness: int = int(maximum_brightness_file.read())

    @property
    def raw_brightness(self) -> int:
        """The current brightness value as an integer."""
        raw_brightness = int(self._brightness_file.read())
        self._brightness_file.seek(0)

        return raw_brightness

    @property
    def brightness(self) -> float:
        """The current brightness in percentage."""
        return self.raw_brightness / self._max_brightness * 100

    @raw_brightness.setter
    def raw_brightness(self, new_value: int):
        new_value = normalize(
            new_value,
            MINIMUM_BRIGHTNESS_VALUE,
            self._max_brightness
        )
        self._brightness_file.write(str(new_value))
        self._brightness_file.seek(0)

    @brightness.setter
    def brightness(self, percent: int):
        self.raw_brightness = trunc(percent * self._max_brightness / 100)


def get_controllers() -> MutableMapping[str, str]:
    """Get all the controllers from the path given by the constants ``CONTROLLERS_PATH``.

    :returns: An :class:`collections.OrderedDict` that contains the controllers'
              name as the keys and their paths as values
    """
    controllers_path_by_controllers_name = OrderedDict()
    for path in CONTROLLERS_PATH:
        for name in os.listdir(path):
            controllers_path_by_controllers_name[name] = os.path.join(path, name)

    return controllers_path_by_controllers_name


def make_controller(controller_name: Optional[str]) -> Controller:
    """Make the given controller if it exists.

    :param controller_name: The name of the controller to create
    :returns: The created controller
    """
    controllers = get_controllers()

    if controller_name is not None and controller_name not in controllers.values():
        print(
            f"{controller_name} is not amongst the valid controllers. Please "
            "specify a valid name.",
            file=sys.stderr
        )
        sys.exit(1)

    controller = controllers.get(controller_name, tuple(controllers.values())[0])
    maximum_brightness_file = open(
        os.path.join(controller, MAXIMUM_BRIGHTNESS_FILE),
        'r'
    )
    brightness_file = open(
        os.path.join(controller, BRIGHTNESS_FILE),
        'w+'
    )
    return Controller(brightness_file, maximum_brightness_file)
