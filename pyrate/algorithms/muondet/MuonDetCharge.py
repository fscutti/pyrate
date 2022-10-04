""" Computation of energy deposited.
"""

from pyrate.core.Algorithm import Algorithm


class MuonDetCharge(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self, condition=None):

        if self.config["format"] == "ROOT":

            e = self.store.get(self.config["input"]["edep"])

            self.store.put(self.name, e)


# EOF
