""" Testing of Pyrate's own Enumerator
"""

from enum import Enum


class Pyrate(Enum):
    SKIP_WRITE = 1  # Tells the Run to skip writing for a target.
    NONE = 2  # A None object for internal pyrate use.
    READY = 3  # The object is ready to be written to the output.
