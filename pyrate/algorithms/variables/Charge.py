""" Calculates the charge - the sum over a region of a waveform scaled by 
    physical PMT and circuit parameters.
    Sums the waveform over a passed in window object. The charge constant is
    calculated from the impedance, and the sample rate.
    Charge = 1/(Z * Sample rate) * Sum trace[i]

    Required parameters:
        impedance: (float) the impedance of the signal
        rate: (float) the sample rate of the digitiser
        waveform: The waveform to caluclate the charge of
        window: (tuple) The start and stop window for calculating the charge
    
    Required states:
        initialise:
            output:
        execute:
            input: <Waveform object>, <Window object>
            output: SELF
    
    Example config:
    
    Charge_CHX:
        algorithm:
            name: Charge
            impedance: 50
            rate: 500e6
        initialise:
            output:
        execute:
            input: CorrectedWaveform_CHX, Window_CHX
            output: SELF
        waveform: CorrectedWaveform_CHX
        window: Window_CHX
"""

import numpy as np
from pyrate.core.Algorithm import Algorithm

class Charge(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)
    
    def initialise(self, config):
        """ Prepare the constant for calculating charge
        """
        # Deal with charge constants
        impedance = config["algorithm"]["impedance"]
        sample_rate = float(config["algorithm"]["rate"])

        charge_constant = 1e12/(impedance * sample_rate) # in pC
        self.store.put(f"{config['name']}:charge_constant", charge_constant)

    def execute(self, config):
        """ Calculates the charge by summing over the waveform
        """
        window = self.store.get(config["window"])
        charge_constant = self.store.get(f"{config['name']}:charge_constant")

        waveform = self.store.get(config["waveform"])
        # Calcualte the actual charge over the window
        Charge = np.sum(waveform[window[0]:window[1]]) * charge_constant
        self.store.put(config["name"], Charge)

# EOF