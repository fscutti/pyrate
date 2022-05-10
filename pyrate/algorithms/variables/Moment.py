""" Calculates the mean, stddev, skew and excess kurtosis of a waveform,
    treating the waveform as a over the passed in window range.
    The moments heavily depend on the window passed in. For best results, ensure
    that your windows are tuned for your expected pulse lengths.
    Momrnt = sum(x_i - mu)^n/N / stddev^n

    
    Required parameters:
        rate: (float) The digitisation rate

    Optional parameters:
        mode: (str) Let's the user change to algebraic moments instead of
                    central, normalised moments. To get the algebraic moments
                    pass in the flag "algebraic"
   

    Required states:
        initialise:
            output:
        execute:
            input: <Waveform object>, <Window object>
    

    Example config:
    
    Skew_CHX:
        algorithm:
            name: Moment
            rate: 500e6
        initialise:
            output:
        execute:
            input: CorrectedWaveform_CHX, Window_CHX
        waveform: CorrectedWaveform_CHX
        window: Window_CHX
"""

import numpy as np
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate

class Moment(Algorithm):
    __slots__ = ("mode", "time_period", "times")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self):
        """Prepares the config order of the moment"""
        self.mode = 0
        if "mode" in self.config["algorithm"]:
            if self.mode.lower() == "algebraic":
                self.mode = 1

        self.time_period = 1 / float(self.config["algorithm"]["rate"])
        self.times = np.arange(0)

    def execute(self):
        """Calculates the 4th order moments"""
        waveform = self.store.get(self.config["waveform"])
        window = self.store.get(self.config["window"])
        if waveform is Pyrate.NONE or window is Pyrate.NONE:
            self.store.put(self.name, Pyrate.NONE)
            return

        waveform_len = waveform.size
        # Check if the times array matches the data
        if self.times.size < waveform_len:
            # Times array not big enough, growing to the size of the waveform
            self.times = (np.arange(waveform_len) * self.time_period + self.time_period / 2) * 1e9 # in ns

        # The waveform over the region of interest
        x = self.times[window[0]:window[1]]
        fx = waveform[window[0]:window[1]]
        fsum = np.sum(fx)
        if fsum == 0:
            self.store.put(self.name, Pyrate.NONE)
            return

        inner = fx * x
        mean = np.sum(inner) / fsum
        inner *= x
        m2 = np.sum(inner) / fsum
        inner *= x
        m3 = np.sum(inner) / fsum #/ np.power(variance, 1.5)
        inner *= x
        m4 = np.sum(inner) / fsum #/ np.power(variance, 2) - 3

        # Convert to central moments
        M2 = m2 - np.power(mean,2) # AKA Variance
        if M2 < 0:
            # Can't really go any further, skew and kurtosis aren't real
            moments = [mean, np.nan, np.nan, np.nan]
        else:
            # Get the rest of the central moments
            M4 = m4 - 3*np.power(mean,4) + 6*np.power(mean,2)*m2 - 4*mean*m3
            M3 = m3 + 2*np.power(mean,3) - 3*mean*m2

            # Convert the central moments to useful variables
            stddev = np.sqrt(M2)
            skew = M3 / np.power(stddev, 3)
            excess_kurtosis = M4 / np.power(stddev, 4) - 3

            moments = [mean, stddev, skew, excess_kurtosis]

        self.store.put(self.name, moments)

        # Old version
        # if self.mode == 0:
        #     inner = np.power(x - mu, 2) * fx
        #     variance = np.sum(inner) / fsum
        #     if variance < 0:
        #         moments = [1, mu, variance, np.nan, np.nan]
        #     else:
        #         inner *= x - mu
        #         skew = (np.sum(inner) / fsum) / np.power(variance, 1.5)
        #         # skew = (np.sum(np.power(x - mu, 3) * fx) / fsum) / np.power(variance, 1.5)
        #         inner *= x - mu
        #         excess_kurtosis = (np.sum(inner) / fsum) / np.power(variance, 2) - 3
        #         # excess_kurtosis = (np.sum(np.power(x - mu, 4) * fx) / fsum) / np.power(variance, 1.5) - 3
        #         moments = [1, mu, variance, skew, excess_kurtosis]

        # else:
        #     # Algebraic moments
        #     moments = []
        #     for i in range(self.order + 1):
        #         if i == 0:
        #             moments[i] = 1 # definitionally
        #         else:
        #             moments[i] = np.sum(np.power(x, i) * fx) / fsum


# EOF
