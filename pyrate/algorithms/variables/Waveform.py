""" Executes basic operations on raw waveform.
"""

from pyrate.core.Algorithm import Algorithm


class Waveform(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):
        pass


# EOF
