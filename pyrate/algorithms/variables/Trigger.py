""" Trigger requirements.
"""

from pyrate.core.Algorithm import Algorithm


class Trigger(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):
        pass


# EOF
