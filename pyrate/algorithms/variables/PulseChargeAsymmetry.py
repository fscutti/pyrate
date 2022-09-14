""" An algorithm to quantify the charge asymmetry between two waveforms from the same experimental setup.

    Required parameters:
    
    Required inputs:
        charge1: (int)/(float) A variable quantifying some aspect of waveform 1 for comparison to waveform 2
        charge2: (int)/(float) A variable quantifying some aspect of waveform 2 for comparison to waveform 1
    
    
    Example config:
    
    PulseChargeAsymmetry_CHX_CHY:
        algorithm: PulseChargeAsymetry
        input:
            charge1: PulseCharge_CHX
            charge2: PulseCharge_CHY
"""

import numpy as np
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate


class PulseChargeAsymmetry(Algorithm):
    __slots__ = ("delay", "sample_rate")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self, condition=None):
        """Calculate asymmetry variable, using definition from cosine100 (arXiv:1710.05299)"""

        charge1 = self.store.get(self.config["input"]["charge1"])
        charge2 = self.store.get(self.config["input"]["charge2"])
        if charge1 is Pyrate.NONE or charge2 is Pyrate.NONE:
            return

        if charge1+charge2==0:
            asymmetry = np.nan
        else:
            asymmetry = (charge1 - charge2)/(charge1 + charge2)

        self.store.put(self.name, asymmetry)


# EOF