""" Calculates the CFD of a waveform.
    From this it also calculates the CFD zero crossing points - i.e. the cfd time
    Outputs the first crossing point time. Also outputs the crossing point times
    as an array. and outputs the CFD as an array, which can be accessed on the
    store using <OBJNAME>CrossTimes and <OBJNAME>Trace respectively

    Required parameters:
        delay: (int)   The amount the CFD algorithm will delay the input trace
        scale: (float) The amount the CFD algorithm will scale the first trace 
                       in the calculation.
        cfd_threshold: (float) The minimum height the CFD must cross before a
                               zero crossing point can be calculated

    Required inputs:
        waveform: A waveform-like object (list/array)
    
    Example configs:

    CFD_CHX:
        algorithm: CFD
        delay: 5
        scale: 1
        cfd_threshold: 10
        input:
            waveform: CorrectedWaveform_CHX
    
    CFD_CHX:
        algorithm: CFD
        delay: 5
        scale: 1
        cfd_threshold: 10
        input:
            waveform: TrapezoidWaveform_CHX

"""

import numpy as np
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate

class CFD(Algorithm):
    __slots__ = ("delay", "scale", "cfd_threshold", "cfd", "waveform", "waveform_delayed")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self, condition=None):
        """Set up the CFD and trapezoid parameters"""
        # CFD parameters
        self.delay = int(self.config["delay"])
        self.scale = int(self.config["scale"])
        self.cfd_threshold = float(self.config["cfd_threshold"])

        self.cfd = np.zeros(0)
        self.waveform = np.zeros(0)
        self.waveform_delayed = np.zeros(0)

    def execute(self, condition=None):
        """Caclulates the waveform CFD"""
        # Reset all the waveforms, safer to do at the start
        self.clear_arrays()

        waveform = self.store.get(self.config["input"]["waveform"])
        if waveform is Pyrate.NONE:
            return
        
        waveform_len = waveform.size
        if (waveform_len + self.delay) > self.waveform.size:
            # Our waveform is larger than the storage
            # we need to grow our arrays
            self.waveform = np.resize(self.waveform, waveform_len + self.delay)
            self.waveform_delayed = np.resize(self.waveform_delayed, waveform_len + self.delay)

        # Parameters and formula from Digital techniques for real-time pulse shaping in radiation measurements
        # https://doi.org/10.1016/0168-9002(94)91652-7

        self.waveform[:-self.delay] = waveform
        self.waveform_delayed[self.delay:] = waveform
        self.cfd = (self.scale * self.waveform) - self.waveform_delayed

        # Possible numpy way to do it quickly
        # https://stackoverflow.com/questions/3843017/efficiently-detect-sign-changes-in-python
        zero_cross = np.where(np.diff(np.sign(self.cfd)))[0]
        cross_threshold = np.where(self.cfd > self.cfd_threshold)[0]

        if cross_threshold.size == 0:
            return
        
        zero_cross = zero_cross[zero_cross>cross_threshold[0]]
        if zero_cross.size == 0:
            return

        f = self.cfd[zero_cross]/(self.cfd[zero_cross] - self.cfd[zero_cross+1])
        CFDTimes = zero_cross + f
        self.store.put(self.name, CFDTimes[0])
        self.store.put(f"{self.output['times']}", CFDTimes)
        self.store.put(f"{self.output['trace']}", self.cfd)
            # if cross_threshold.size:
            #     # Only look at the zero crosses after the threshold cross
            #     zero_cross = zero_cross[zero_cross>cross_threshold[0]]
            #     if zero_cross.size:
            #         # Ok, now we check the first valid zero cross
            #         fc = zero_cross[0] # First crossing (left side)
            #         f = self.cfd[fc]/(self.cfd[fc] - self.cfd[fc+1]) # CFD fraction
            #         CFDTime = zero_cross[0] + f
        

        # self.store.put(self.name, CFDTime)
        # if self.savecfd:
        #     self.store.put(f"{self.name}Trace", self.cfd)

    def clear_arrays(self):
        """ Fills all the internal arrays with 0
        """
        self.waveform.fill(0)
        self.waveform_delayed.fill(0)

    # Remove numpy dependence for speed and cross-check with more up to date code above
    @staticmethod
    @numba.jit(nopython=True, cache=True)
    def CFDCalc(selfwaveform, waveform, cfd, delay, scale, cfd_threshold, waveform_delay_scaled):

        # Parameters and formula from Digital techniques for real-time pulse shaping in radiation measurements
        # https://doi.org/10.1016/0168-9002(94)91652-7

        zero_cross = -999.0
        cross_threshold = -999.0
        CFDTimes = np.array([1], dtype=np.float64)

        selfwaveform[:-1*delay] = waveform
        waveform_delay_scaled[delay:] = scale * waveform
        cfd = selfwaveform - waveform_delay_scaled

        # Possible numpy way to do it quickly
        # https://stackoverflow.com/questions/3843017/efficiently-detect-sign-changes-in-python
        zero_cross = np.where(np.diff(np.sign(cfd)))[0]
        cross_threshold = np.where(cfd > cfd_threshold)[0]

        if cross_threshold.size == 0:
            CFDTimes[0] = -999.0
            return CFDTimes, cfd
        
        zero_cross = zero_cross[zero_cross>cross_threshold[0]]
        if zero_cross.size == 0:
            CFDTimes[0] = -999.0
            return CFDTimes, cfd

        f = cfd[zero_cross]/(cfd[zero_cross] - cfd[zero_cross+1])
        CFDTimes = zero_cross + f

        return CFDTimes, cfd

# EOF
