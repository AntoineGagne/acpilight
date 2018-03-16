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
from typing import TypeVar

CONTROLLERS_PATH = ["/sys/class/backlight", "/sys/class/leds"]

T = TypeVar('T')


def error(msg):
    print(sys.argv[0] + ": " + msg)


def get_controllers():
    ctrls = OrderedDict()
    for path in CONTROLLERS_PATH:
        for name in os.listdir(path):
            ctrls[name] = os.path.join(path, name)
    return ctrls


def normalize(value: T, minimum_value: T, maximum_value: T) -> T:
    """Normalize a value so that it doesn't exceed a given range. Supports all
       ordered types.

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


class Controller(object):
    def __init__(self, path):
        self._brightness_path = os.path.join(path, "brightness")
        with open(os.path.join(path, "max_brightness")) as maximum_brightness_file:
            self._max_brightness = int(maximum_brightness_file.read())

    def raw_brightness(self):
        raw_brightness = 0
        with open(self._brightness_path) as brightness_file:
            raw_brightness = int(brightness_file.read())

        return raw_brightness

    def brightness(self):
        return self.raw_brightness() * 100 / self._max_brightness

    def set_raw_brightness(self, new_value):
        with open(self._brightness_path, 'w') as brightness_file:
            brightness_file.write('{0:.0f}'.format(new_value))

    def set_brightness(self, percent):
        self.set_raw_brightness(percent * self._max_brightness / 100)


def sweep_brightness(ctrl, current, target, steps, delay):
    sleep = (delay / 1000.) / steps
    for s in range(1, steps):
        pc = current + (target - current) * s / steps
        ctrl.set_brightness(pc)
        time.sleep(sleep)
    ctrl.set_brightness(target)


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


def _make_controller(controller_name):
    controllers = get_controllers()

    if controller_name not in controllers.values():
        error("unknown controller '{}'".format(controller_name))
        sys.exit(1)

    return Controller(controllers[controller_name])


def _display_brightness(arguments):
    print('{0:.0f}'.format(arguments.ctrl.brightness()))


def _display_fractional_brightness(arguments):
    print('{0:.2f}'.format(arguments.ctrl.brightness()))


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

    # perform the requested action
    current = arguments.ctrl.brightness()
    if arguments.set is not None:
        target = arguments.set
    elif arguments.inc is not None:
        target = current + arguments.inc
    elif arguments.dec is not None:
        target = current - arguments.dec
    target = normalize(target, 0, 100)
    if current == target:
        pass
    elif arguments.steps <= 1 or arguments.time < 1:
        arguments.ctrl.set_brightness(target)
    else:
        sweep_brightness(
            arguments.ctrl,
            current,
            target,
            arguments.steps,
            arguments.time
        )


def main():
    controllers = tuple(get_controllers().values())
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
        default=Controller(controllers[0]),
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
