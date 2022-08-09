""" Uses raw waveform to calculate the baseline for the event. 
    Requires input from raw waveform and the number of samples used for the
    baseline calculation - this can be varied by the user and is defined in
    the config file. There is also optional input for the threshold used
    to check pulses in the sample window, if not specified it is set to 20.

    Before taking the average of the first n samples in the waveform, checks
    for a pulse in that window by comparing averages calculated in a rolling average.
    If a pulse is found, it moves to the end of the window and calculates using a window
    there. If there is a pulse in that window, the alg will return an incorrect baseline. 
    Can be run on any waveform, typically RawWaveform

    This is an improvement on BaselineNaive to account for events/pulses at the start 
    of the event window.

    Required parameters:
        samples: The number of samples from the start to calculate the 
                 baseline over.
    
    Required inputs:
        waveform: The waveform object for which the baseline will be caluclated.
    
    Example config:

    Baseline_CHX:
        algorithm: BaselineDynamic
        samples: 40
        threshold: 20
        input: 
            waveform: PhysicalWaveform_CHX

    Todo: Get baseline automatically for ZLE firmware

"""
import sys
import numpy as np
from pyrate.core.Algorithm import Algorithm
import sys
from scipy.ndimage.filters import uniform_filter1d
from pyrate.utils.enums import Pyrate


class BaselineDynamic(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self, condition=None):
        """Calculates the baseline from the first n samples of the waveform"""
        waveform = self.store.get(self.config["input"]["waveform"])

        if "samples" not in self.config:
            sys.exit("ERROR in Baseline, 'samples' not found in the config")
        
        if "threshold" not in self.config:
            check_thres = 20
        elif "threshold" in self.config:
            check_thres = self.config["threshold"]

        nsamples = self.config["samples"]

        if waveform is Pyrate.NONE or waveform.size < nsamples:
            self.store.put(self.name, Pyrate.NONE)
            return

        averages = self.moving_average(waveform=waveform[:nsamples], n=4)
        averages_diffs = averages[1:] - averages[:-1]
        pulse_idx = np.where(np.abs(averages_diffs)>=check_thres)[0]
        
        if pulse_idx.shape[0]>0:
            # Ok, now we go to the end of the waveform because a pulse is occuring in the baseline window
            Baseline = np.sum(waveform[-1*nsamples:]) / nsamples
        
        else:

            # Get the baseline from the front of the waveform.
            Baseline = np.sum(waveform[:nsamples]) / nsamples

        self.store.put(self.name, Baseline)

    def moving_average(self, waveform, n):
        # Uniform 1D filter is equivalent to a moving average, and is more efficient and accurate than similar numpy methods
        return uniform_filter1d(waveform, size=n)


# EOF

