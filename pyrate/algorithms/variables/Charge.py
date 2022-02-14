""" Computation of charge associated with a waveform.
"""

from pyrate.core.Algorithm import Algorithm


class Charge(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self):

        waveform = self.store.get(self.config["waveform"])

        charge = waveform.Integral()

        self.store.put(self.name, charge)


# EOF
