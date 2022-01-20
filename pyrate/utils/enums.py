""" Testing of Pyrate's own Enumerator
"""

from enum import Enum


class Pyrate(Enum):
    SKIP_WRITE = 1  # Tells the Run to skip writing for an object
    NONE = 2  # A None object for internal pyrate use
