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

import numba
import numpy as np
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate

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
            return

        waveform_len = waveform.size

        trap = self.TrapCalc(waveform=waveform, rise=self.rise, gap=self.gap, M=self.M, 
                             waveform_len=waveform_len)

        self.store.put(f"{self.name}", trap)

    @staticmethod
    @numba.njit(cache=True)
    def TrapCalc(waveform, rise, gap, M, waveform_len):
        
        dn = np.zeros(waveform_len)
        p = np.zeros(waveform_len)
        r = np.zeros(waveform_len)
        trap = np.zeros(waveform_len)

        for i in range(waveform_len):
            dn[i] = get(waveform, i) - get(waveform, i-rise) - get(waveform, i-gap) + get(waveform, i-rise-gap)
            p[i] = get(p,i-1) + get(dn,i)
            r[i] = get(p,i) + M*get(dn,i)
            trap[i] = get(trap,i-1) + get(r,i)/(M*rise)

        return trap

@numba.njit(cache=True)
def get(array, i):
    if i < 0:
        return 0
    else: 
        return array[i]

# EOF
