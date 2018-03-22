"""Control backlight and LED brightness on Linux using the ``sys`` filesystem
   with a backward-compatibile user interface.

   :copyright: (c) 2016-2017 by wave++ `Yuri D'Elia <wavexx@thregr.org>`_
"""

import argparse
import sys

from argparse import ArgumentDefaultsHelpFormatter

from acpilight.brightness import sweep_brightness, get_controllers, make_controller
from acpilight.utils import normalize


def error(msg):
    print(sys.argv[0] + ": " + msg)


def percent(arg):
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
        type=percent,
        nargs='?',
        help="[=+-]PERCENT to set, increase, decrease brightness")
    parser.add_argument(
        "-ctrl",
        default=make_controller(None),
        type=make_controller,
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
