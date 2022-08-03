""" Testing of Pyrate's own Enumerator
"""

from enum import Enum


class Pyrate(Enum):
    WRITTEN = 1  # Tells the Run to skip writing for a target.
    NONE = 2  # A None object for internal pyrate use.
