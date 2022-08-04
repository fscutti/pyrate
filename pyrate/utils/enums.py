""" Testing of Pyrate's own Enumerator
"""

from enum import Enum


class Pyrate(Enum):
    NONE = 0  # A None object for usage between algorithms.
    EXECUTED = 1  # A None object for usage between algorithms.
    WRITTEN = 2  # Tells the Run to skip writing for a target.
