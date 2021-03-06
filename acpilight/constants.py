"""Contains various constants."""

from typing import List

#: The paths where the backlight controllers can be found
CONTROLLERS_PATH: List[str] = ["/sys/class/backlight", "/sys/class/leds"]

#: The name of the file that contains the maximum brightness value
MAXIMUM_BRIGHTNESS_FILE: str = "max_brightness"

#: The name of the file that contains the brightness value
BRIGHTNESS_FILE: str = "brightness"

#: The minimum brightness value that a controller can take
MINIMUM_BRIGHTNESS_VALUE: int = 0
