""" Calculates the mean, stddev, skew and excess kurtosis of a waveform,
    treating the waveform as a over the passed in window range.
    The moments heavily depend on the window passed in. For best results, ensure
    that your windows are tuned for your expected pulse lengths.
    Momrnt = sum(x_i - mu)^n/N / stddev^n

    
    Required parameters:
        rate: (float) The digitisation rate
    
    Required inputs:
        waveform: (array-like) A waveform-like object
        window: (tuple-like) A window object    

    Example config:
    
    Skew_CHX:
        algorithm: Moment
        rate: 500e6
        input:
            waveform: CorrectedWaveform_CHX
            window: Window_CHX
"""

import numpy as np
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate
import numba
import math

class Moment(Algorithm):
    __slots__ = ("mode", "time_period", "times")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self, condition=None):
        """Prepares the config order of the moment"""
        self.time_period = 1 / float(self.config["rate"])
        self.times = np.arange(0)

    def execute(self, condition=None):
        """Calculates the 4th order moments"""
        waveform = self.store.get(self.config["input"]["waveform"])
        window = self.store.get(self.config["input"]["window"])
        if waveform is Pyrate.NONE or window is Pyrate.NONE:
            return
        
        if window[0]==None and window[1]==None:
            window_size = len(waveform)
            window_start = 0
            window_end = len(waveform)
        else:
            window_size = window[1]-window[0]
            window_start = window[0]
            window_end = window[1]

        mean, stddev, skew, kurtosis = self.MomentsCalc(waveform = waveform, window_start = window_start, window_end = window_end, window_size=window_size, time_period=self.time_period)

        # self.store.put(self.name, moments)
        self.store.put(f"{self.output['mean']}", mean)
        self.store.put(f"{self.output['stddev']}", stddev)
        self.store.put(f"{self.output['skew']}", skew)
        self.store.put(f"{self.output['kurtosis']}", kurtosis)

    @staticmethod
    @numba.njit(cache=True)
    def MomentsCalc(waveform, window_start, window_end, window_size, time_period):

        mean = Pyrate.NONE
        stddev = Pyrate.NONE
        skew = Pyrate.NONE
        kurtosis = Pyrate.NONE
        fsum = 0.0
        m2 = Pyrate.NONE
        m3 = Pyrate.NONE
        m4 = Pyrate.NONE
        M2 = Pyrate.NONE
        M3 = Pyrate.NONE
        M4 = Pyrate.NONE
        excess_kurtosis = Pyrate.NONE
        inner_sum = 0.0
        inner_square_sum = 0.0
        inner_cube_sum = 0.0
        inner_quart_sum = 0.0
        inner = 0.0
        time = 0.0

        # Waveform over region of interest
        for i in range(window_start, window_end):
            time = (i*time_period + time_period/2)*1e9
            fsum += waveform[i]
            inner = waveform[i]*time
            inner_sum += inner
            inner *= time
            inner_square_sum += inner
            inner *= time
            inner_cube_sum += inner
            inner *= time
            inner_quart_sum += inner

        if fsum==0:
            mean = np.nan
            stddev = np.nan
            skew = np.nan
            kurtosis = np.nan
            return mean, stddev, skew, kurtosis

        mean = inner_sum/fsum
        m2 = inner_square_sum/fsum
        m3 = inner_cube_sum/fsum
        m4 = inner_quart_sum/fsum

        # Convert to central moments
        M2 = m2 - mean**2
        if M2<0:
            # Negative SD means skew and kurt aren't real
            stddev = np.nan
            skew = np.nan
            kurtosis = np.nan
        else:
            M4 = m4 - 3*(mean**4) + 6*(mean**2)*m2 - 4*mean*m3
            M3 = m3 + 2*(mean**3) - 3*mean*m2

            # Conversion to useful variables
            stddev = math.sqrt(M2) # Numba maps math.sqrt to sqrtf in libc, not sure about numpy
            skew = M3 / (stddev**3)
            excess_kurtosis = M4 / (stddev**4) - 3
            kurtosis = excess_kurtosis

        return mean, stddev, skew, kurtosis


# EOF
