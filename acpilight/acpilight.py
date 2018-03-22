"""Control backlight and LED brightness on Linux using the ``sys`` filesystem
   with a backward-compatibile user interface.

   :copyright: (c) 2016-2017 by wave++ `Yuri D'Elia <wavexx@thregr.org>`_
"""

import argparse
import os
import sys
import time

from argparse import ArgumentDefaultsHelpFormatter
from collections import OrderedDict
from math import trunc
from typing import TypeVar, Optional, IO, AnyStr, MutableMapping

from acpilight.constants import (
    CONTROLLERS_PATH,
    BRIGHTNESS_FILE,
    MAXIMUM_BRIGHTNESS_FILE,
    MINIMUM_BRIGHTNESS_VALUE
)

T = TypeVar('T')


def error(msg):
    print(sys.argv[0] + ": " + msg)


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


def pc(arg):
    if len(arg) == 0 or arg[0] not in '=+-0123456789':
        return None
    if arg[0] not in '=+-':
        arg = '=' + arg
    try:
        float(arg[1:])
    except ValueError:
        return None
    return arg


def _display_controllers(arguments):
    controllers = get_controllers()
    for controller in controllers:
        print(controller)


def _make_controller(controller_name: Optional[str]) -> Controller:
    controllers = get_controllers()

    if controller_name is not None and controller_name not in controllers.values():
        error("unknown controller '{}'".format(controller_name))
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


def _display_brightness(arguments):
    print('{0:.0f}'.format(arguments.ctrl.brightness))


def _display_fractional_brightness(arguments):
    print('{0:.2f}'.format(arguments.ctrl.brightness))


def _handle_other_actions(arguments):
    if arguments.pc is not None:
        v = float(arguments.pc[1:])
        if arguments.pc[0] == '=':
            arguments.set = v
        elif arguments.pc[0] == '+':
            arguments.inc = v
        elif arguments.pc[0] == '-':
            arguments.dec = v
    if arguments.fps:
        arguments.steps = int((arguments.fps / 1000) * arguments.time)

    if arguments.set is not None:
        target = arguments.set
    elif arguments.inc is not None:
        target = arguments.ctrl.brightness + arguments.inc
    elif arguments.dec is not None:
        target = arguments.ctrl.brightness - arguments.dec
    target = normalize(target, 0, 100)
    if arguments.ctrl.brightness == target:
        pass
    elif arguments.steps <= 1 or arguments.time < 1:
        arguments.ctrl.brightness = target
    else:
        sweep_brightness(
            arguments.ctrl,
            target,
            arguments.steps,
            arguments.time
        )


def main():
    parser = argparse.ArgumentParser(
        description='Control backlight brightness',
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-list",
        action="store_const",
        dest='command',
        const=_display_controllers,
        help="list controllers"
    )
    group.add_argument(
        "-getf",
        action="store_const",
        dest='command',
        const=_display_fractional_brightness,
        help="get fractional brightness"
    )
    group.add_argument(
        "-get",
        action="store_const",
        dest='command',
        const=_display_brightness,
        help="get brightness"
    )
    group.add_argument(
        "-set",
        metavar="PERCENT",
        type=float,
        help="set brightness"
    )
    group.add_argument(
        "-inc",
        metavar="PERCENT",
        type=float,
        help="increase brightness"
    )
    group.add_argument(
        "-dec",
        metavar="PERCENT",
        type=float,
        help="decrease brightness"
    )
    group.add_argument(
        "pc",
        metavar="PERCENT",
        type=pc,
        nargs='?',
        help="[=+-]PERCENT to set, increase, decrease brightness")
    parser.add_argument(
        "-ctrl",
        default=_make_controller(None),
        type=_make_controller,
        help="set the controller to use"
    )
    parser.add_argument(
        "-time",
        metavar="MILLISECS",
        type=int,
        default=200,
        help="fading period (in milliseconds)"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-steps",
        type=int,
        default=0,
        help="fading steps"
    )
    group.add_argument(
        "-fps",
        type=int,
        default=0,
        help="fading frame rate"
    )
    parser.add_argument(
        "-display",
        help="ignored"
    )
    parser.set_defaults(command=_handle_other_actions)
    arguments = parser.parse_args()
    arguments.command(arguments)
