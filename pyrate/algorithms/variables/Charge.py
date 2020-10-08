""" Computation of charge associated with a waveform.
"""

from pyrate.core.Algorithm import Algorithm


class Charge(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):
        # print("Calling: ", config["name"])
        charge = self.store.get(config["waveform"])
        # print(self.store.get("INPUT:idx"))
        self.store.put(config["name"], charge)


# EOF
