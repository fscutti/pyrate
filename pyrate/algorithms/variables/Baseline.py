""" Uses physical waveform to calculate the baseline for the event. 
    Requires input from physical waveform and the number of samples used for the
    baseline calculation - this can be varied by the user and is defined in
    the config file.
    Takes the average of the first n samples in the waveform. Can be run on any
    waveform, typically PhysicalWaveform

    This can probably be improved to account for events/pulses at the start 
    of the event window.

    Required states:
        execute:
            input: <waveform>

    Required parameters:
        samples: The number of samples from the start to calculate the 
                 baseline over.
        waveform: The waveform object for which the baseline will be caluclated.
    
    Example config:

    Baseline_CHX:
        algorithm: 
            name: Baseline
            samples: 40
        execute:
            input: PhysicalWaveform_CHX
        waveform: PhysicalWaveform_CHX

    Todo: Get baseline automatically for ZLE firmware

"""
import sys
import numpy as np
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate


class Baseline(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self):
        """Calculates the baseline from the first n samples of the waveform"""
        waveform = self.store.get(self.config["waveform"])

        if "samples" not in self.config["algorithm"]:
            sys.exit("ERROR in Baseline, 'samples' not found in the config")

        nsamples = self.config["algorithm"]["samples"]

        if waveform is Pyrate.NONE or waveform.size < nsamples:
            self.store.put(self.name, Pyrate.NONE)
            return

        # Get the baseline.
        Baseline = np.sum(waveform[:nsamples]) / nsamples

        self.store.put(self.name, Baseline)


# EOF

