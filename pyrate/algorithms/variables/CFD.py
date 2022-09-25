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

import numba
import numpy as np
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate

class CFD(Algorithm):
    __slots__ = ("delay", "scale", "cfd_threshold", "cfd", "waveform", "waveform_delayed", "CFDTimes")

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
        self.CFDTimes = np.zeros(1)

    def execute(self, condition=None):
        """Caclulates the waveform CFD"""
        # Reset all the waveforms, safer to do at the start
        # self.clear_arrays()

        waveform = self.store.get(self.config["input"]["waveform"])
        if waveform is Pyrate.NONE:
            return

        self.CFDTimes, self.cfd = self.CFDCalc(waveform=waveform, cfd=self.cfd, 
                                                delay=self.delay, scale=self.scale, 
                                                cfd_threshold=self.cfd_threshold)

        if self.CFDTimes.size == 0:
            return

        self.store.put(self.name, self.CFDTimes[0])
        self.store.put(f"{self.output['times']}", self.CFDTimes)
        self.store.put(f"{self.output['trace']}", self.cfd)

    # Remove numpy dependence for speed and cross-check with more up to date code above
    @staticmethod
    @numba.njit(cache=True)
    def CFDCalc(waveform, cfd, delay, scale, cfd_threshold):

        # Parameters and formula from Digital techniques for real-time pulse shaping in radiation measurements
        # https://doi.org/10.1016/0168-9002(94)91652-7

        CFDTimes = np.zeros(len(waveform))

        crossed = False
        max_cfd_len = len(waveform) - delay
        num_zero_crossing = 0
        num_thresh_crossing = 0
        f = 0
        cfd = np.zeros(max_cfd_len)

        # C-like replacement of numpy-based code block below loops
        for i in range(0, max_cfd_len):
            cfd[i] = (scale*waveform[i-delay]) - waveform[i]

            if cfd[i] >= cfd_threshold and not crossed:
                crossed = True
                num_thresh_crossing += 1
                if i == max_cfd_len:
                    break
            
            if crossed and cfd[i]<=0 and cfd[i-1]>0:
                if (cfd[i] - cfd[i+1]) == 0:
                    crossed = False
                    CFDTimes[num_zero_crossing] = i
                    num_zero_crossing += 1
                else:
                    crossed = False
                    f = cfd[i]/(cfd[i] - cfd[i+1])
                    CFDTimes[num_zero_crossing] = i+f
                    num_zero_crossing += 1

        if num_zero_crossing==0 or num_thresh_crossing==0:
            CFDTimes = np.array([np.float64(x) for x in range(0)])
            return CFDTimes, cfd
        
        CFDTimes = CFDTimes[:num_zero_crossing]

        return CFDTimes, cfd

# EOF
