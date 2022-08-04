""" Testing of Pyrate's own Enumerator
"""

from enum import Enum


class Pyrate(Enum):
    NONE = 0            # A None object for internal pyrate core use.
    INVALID_VALUE = 1   # A placeholder for invalid values between algorithms.
    WRITTEN = 2         # Tells the Run to skip writing for a target.
