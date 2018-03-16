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

APP_DESC = "control backlight brightness"
SYS_PATH = ["/sys/class/backlight", "/sys/class/leds"]

T = TypeVar('T')


def error(msg):
    print(sys.argv[0] + ": " + msg)


def get_controllers():
    ctrls = OrderedDict()
    for path in SYS_PATH:
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
        self._max_brightness = int(
            open(os.path.join(path, "max_brightness")).read())

    def raw_brightness(self):
        return int(open(self._brightness_path).read())

    def brightness(self):
        return self.raw_brightness() * 100 / self._max_brightness

    def set_raw_brightness(self, b):
        open(self._brightness_path, "w").write(str(int(round(b))))

    def set_brightness(self, pc):
        self.set_raw_brightness(pc * self._max_brightness / 100)


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
    sys.exit(0)


def _make_controller(controller_name):
    controllers = get_controllers()

    if controller_name not in controllers.values():
        error("unknown controller '{}'".format(controller_name))
        sys.exit(1)

    return Controller(controllers[controller_name])


def _display_brightness(arguments):
    print(int(round(arguments.ctrl.brightness())))
    sys.exit(0)


def _display_fractional_brightness(arguments):
    print(arguments.ctrl.brightness())
    sys.exit(0)


def main():
    controllers = tuple(get_controllers().values())
    ap = argparse.ArgumentParser(
        description=APP_DESC,
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "-list",
        action="store_const",
        dest='command',
        const=_display_controllers,
        help="list controllers"
    )
    g.add_argument(
        "-getf",
        action="store_const",
        dest='command',
        const=_display_fractional_brightness,
        help="get fractional brightness"
    )
    g.add_argument(
        "-get",
        action="store_const",
        dest='command',
        const=_display_brightness,
        help="get brightness"
    )
    g.add_argument(
        "-set",
        metavar="PERCENT",
        type=float,
        help="Set brightness"
    )
    g.add_argument(
        "-inc",
        metavar="PERCENT",
        type=float,
        help="increase brightness"
    )
    g.add_argument(
        "-dec",
        metavar="PERCENT",
        type=float,
        help="decrease brightness"
    )
    g.add_argument(
        "pc",
        metavar="PERCENT",
        type=pc,
        nargs='?',
        help="[=+-]PERCENT to set, increase, decrease brightness")
    ap.add_argument(
        "-ctrl",
        default=Controller(controllers[0]),
        type=_make_controller,
        help="set the controller to use"
    )
    ap.add_argument(
        "-time",
        metavar="MILLISECS",
        type=int,
        default=200,
        help="fading period (in milliseconds)"
    )
    g = ap.add_mutually_exclusive_group()
    g.add_argument(
        "-steps",
        type=int,
        default=0,
        help="Fading steps (default: 0)"
    )
    g.add_argument(
        "-fps",
        type=int,
        default=0,
        help="Fading frame rate (default: 0)"
    )
    ap.add_argument(
        "-display",
        help="Ignored"
    )
    args = ap.parse_args()

    if args.command is not None:
        args.command(args)

    # uniform set arguments
    if args.pc is not None:
        v = float(args.pc[1:])
        if args.pc[0] == '=':
            args.set = v
        elif args.pc[0] == '+':
            args.inc = v
        elif args.pc[0] == '-':
            args.dec = v
    if args.fps:
        args.steps = int((args.fps / 1000) * args.time)

    # perform the requested action
    current = args.ctrl.brightness()
    if args.set is not None:
        target = args.set
    elif args.inc is not None:
        target = current + args.inc
    elif args.dec is not None:
        target = current - args.dec
    target = normalize(target, 0, 100)
    if current == target:
        pass
    elif args.steps <= 1 or args.time < 1:
        args.ctrl.set_brightness(target)
    else:
        sweep_brightness(args.ctrl, current, target, args.steps, args.time)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except IOError as e:
        error(str(e))
        sys.exit(1)
