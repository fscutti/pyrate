""" Calculates the CFD of a waveform.
    From this it also calculates the CFD zero crossing point - i.e. the cfd time
    Outputs the crossing point time. Can also save the CFD if savecfd is True
    The CFD will be saved optionally as <OBJNAME>Trace

    Required parameters:
        delay: (int)   The amount the CFD algorithm will delay the input trace
        scale: (float) The amount the CFD algorithm will scale the first trace 
                       in the calculation.
        cfd_threshold: (float) The minimum height the CFD must cross before a
                               zero crossing point can be calculated
    
    Optional parameters:
        savecfd: (bool) False by default
    
    Required states:
        initialise:
            output:
        execute:
            input: <Waveform object>
    
    Example configs:

    CFD_CHX:
        algorithm:
            name: CFD
            delay: 5
            scale: 1
            cfd_threshold: 10
        initialise:
            output:
        execute:
            input: CorrectedWaveform_CHX
        waveform: CorrectedWaveform_CHX
    
    CFD_CHX:
        algorithm:
            name: CFD
            delay: 5
            scale: 1
            cfd_threshold: 10
            savecfd: True
        initialise:
            output:
        execute:
            input: TrapezoidWaveform_CHX
        waveform: TrapezoidWaveform_CHX

    Todo: Decide if we want to subtract the gap and rise time from the CFDTime
          in trapezoid mode.
"""

import numpy as np
from pyrate.core.Algorithm import Algorithm

class CFD(Algorithm):
    __slots__ = ("delay", "scale", "cfd_threshold", "savecfd", "cfd", "waveform", "waveform_delay_scaled")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self):
        """Set up the CFD and trapezoid parameters"""
        # CFD parameters
        self.delay = int(self.config["algorithm"]["delay"])
        self.scale = int(self.config["algorithm"]["scale"])
        self.cfd_threshold = float(self.config["algorithm"]["cfd_threshold"])

        if "savecfd" in self.config["algorithm"]:
            self.savecfd = bool(self.config["algorithm"]["savecfd"])

        else:
            self.savecfd = False

        self.cfd = np.zeros(0)
        self.waveform = np.zeros(0)
        self.waveform_delay_scaled = np.zeros(0)

    def execute(self):
        """Caclulates the waveform CFD"""
        # Get the actual waveform, finally.
        waveform = self.store.get(self.config["waveform"])
        waveform_len = waveform.size

        if (waveform_len + self.delay) > self.waveform.size:
            # Our waveform is larger than the storage
            # we need to grow our arrays
            self.waveform.resize(waveform_len + self.delay)
            self.waveform_delay_scaled.resize(waveform_len + self.delay)

        # Parameters and formula from Digital techniques for real-time pulse shaping in radiation measurements
        # https://doi.org/10.1016/0168-9002(94)91652-7
        CFDTime = -999 # Just in case we get an invalid result

        self.waveform[:-self.delay] = waveform
        self.waveform_delay_scaled[self.delay:] = self.scale * waveform
        self.cfd = self.waveform - self.waveform_delay_scaled

        # Possible numpy way to do it quickly
        # https://stackoverflow.com/questions/3843017/efficiently-detect-sign-changes-in-python
        zero_cross = np.where(np.diff(np.sign(self.cfd)))[0]
        cross_threshold = np.where(self.cfd > self.cfd_threshold)[0]
        if cross_threshold.size:
            # Only look at the zero crosses after the threshold cross
            zero_cross = zero_cross[zero_cross>cross_threshold[0]]
            if zero_cross.size:
                # Ok, now we check the first valid zero cross
                fc = zero_cross[0] # First crossing (left side)
                f = self.cfd[fc]/(self.cfd[fc] - self.cfd[fc+1]) # CFD fraction
                CFDTime = zero_cross[0] + f
        
        self.store.put(self.name, CFDTime)
        if self.savecfd:
            self.store.put(f"{self.name}Trace", self.cfd)

        self.waveform.fill(0)
        self.waveform_delay_scaled.fill(0)

# EOF
