""" Get waveform of specific PMT.
"""

from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate


class SimulatedWaveformsGetter(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self, condition=None):

        waveform = {"energy": [], "time": []}

        wf_map = self.store.get(self.config["input"]["waveform_map"])

        if wf_map is Pyrate.NONE:
            return

        if self.config["pmt_name"] in wf_map:
            waveform = wf_map[self.config["pmt_name"]]

        self.store.put(self.config["output"]["energy"], waveform["energy"])
        self.store.put(self.config["output"]["time"], waveform["time"])
        self.store.put(self.name, waveform)


# EOF
