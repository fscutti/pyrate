""" A trapezoidal filter for waveforms.

    Required parameters:
        rise: (int) The rise time of the trapezoid filter
        gap:  (int) The width of the top of the trapezoid filter
        rate: (float) The sample rate of the digitiser
        tau:  (float) The decay constant of the pulse

    Required inputs:
        waveform: (array-like) A waveform-like object

    Optional parameters:
        zeropole: (Bool) True by default
    
    Example config:

    TrapezoidFilter_CHX:
        algorithm: TrapezoidFilter
        rise: 10
        gap: 10
        rate: 500e6
        tau: 2e-6
        zeropole: True
        input:
            waveform: CorrectedWaveform_CHX
"""

import numpy as np
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate
import numba

class TrapezoidFilter(Algorithm):
    __slots__ = ("rise", "gap", "period", "tau", "zeropole", "traplen", "M", "dn0", "dn1", "dn2", "dn3")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self, condition=None):
        """Set up the trapezoid parameters"""
        # Trapezoid parameters
        self.rise = int(self.config["rise"])
        self.gap = int(self.config["gap"])
        self.period = 1 / float(self.config["rate"])
        self.tau = float(self.config["tau"])
        if "zeropole" in self.config:
            self.zeropole = bool(self.config["zeropole"])
        else:
            self.zeropole = True
        
        if self.zeropole == True:
            self.M = self.tau / self.period + 0.5  # Pole-zero correction parameter
        else:
            self.M = 1
        
        self.traplen = 2*self.rise+self.gap

        self.dn0 = np.zeros(0)
        self.dn1 = np.zeros(0)
        self.dn2 = np.zeros(0)
        self.dn3 = np.zeros(0)

    def execute(self, condition=None):
        """Caclulates the trap filtered waveform"""
        waveform = self.store.get(self.config["input"]["waveform"])
        if waveform is Pyrate.NONE:
            self.clear_arrays() # just in case
            return

        waveform_len = waveform.size

        if (waveform_len + self.traplen) > self.dn0.size:
            # Our waveform is larger than the storage
            # we need to grow our arrays
            self.dn0 = np.resize(self.dn0, waveform_len + self.traplen)
            self.dn1 = np.resize(self.dn1, waveform_len + self.traplen)
            self.dn2 = np.resize(self.dn2, waveform_len + self.traplen)
            self.dn3 = np.resize(self.dn3, waveform_len + self.traplen)

        # Parameters and formula from Digital techniques for real-time pulse shaping in radiation measurements
        # https://doi.org/10.1016/0168-9002(94)91652-7
        self.dn0[:waveform_len] = waveform
        self.dn1[self.rise:waveform_len + self.rise] = waveform
        self.dn2[self.gap+self.rise:self.gap+self.rise + waveform_len] = waveform
        self.dn3[2*self.rise+self.gap: 2*self.rise+self.gap + waveform_len] = waveform

        dn = self.dn0 - self.dn1 - self.dn2 + self.dn3

        p = np.cumsum(dn) # Thanks to Marcel Hohmann for recommending this function
        r = np.add(p, self.M*dn)
        trap = np.cumsum(r/(self.M*self.rise))

        # We can't chop off the front otherwise the times will be funky
        trap[:self.traplen] = trap[self.traplen + 1] # Back propagate the first useful value
        # Chop off the end
        trap = trap[:self.traplen+waveform_len]

        self.store.put(f"{self.name}", trap)

        # Reset all the arrays we use
        self.clear_arrays()

    def clear_arrays(self):
        """ Fills all the internal arrays with 0
        """
        self.dn0.fill(0)
        self.dn1.fill(0)
        self.dn2.fill(0)
        self.dn3.fill(0)

    @staticmethod
    @numba.jit(nopython=True, cache=True)
    def TrapCalc(waveform, dn0, dn1, dn2, dn3, rise, gap, period, tau, traplen, M, waveform_len):
        
        dn = np.array([1], dtype=np.float64)
        p = -999.0
        r = np.array([1], dtype=np.float64)
        trap = np.array([1], dtype=np.float64)

        # Parameters and formula from Digital techniques for real-time pulse shaping in radiation measurements
        # https://doi.org/10.1016/0168-9002(94)91652-7
        dn0[:waveform_len] = waveform
        dn1[rise:waveform_len + rise] = waveform
        dn2[gap+rise:gap+rise + waveform_len] = waveform
        dn3[2*rise+gap: 2*rise+gap + waveform_len] = waveform

        dn = dn0 - dn1 - dn2 + dn3

        p = np.cumsum(dn) # Thanks to Marcel Hohmann for recommending this function
        r = np.add(p, M*dn)
        trap = np.cumsum(r/(M*rise))

        # We can't chop off the front otherwise the times will be funky
        trap[:traplen] = trap[traplen + 1] # Back propagate the first useful value
        # Chop off the end
        trap = trap[:traplen+waveform_len]

        return trap

# EOF
