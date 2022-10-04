""" Compute average energy in input bins.
"""

from pyrate.core.Algorithm import Algorithm


class AverageBinEnergy(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self, condition=None):

        e = self.store.get("EVENT:nT:edepScint")

        self.store.put(self.name, e)


# EOF
