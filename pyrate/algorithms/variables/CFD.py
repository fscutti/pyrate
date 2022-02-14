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

from pyrate.core.Algorithm import Algorithm

class CFD(Algorithm):
    __slots__ = ('delay', 'scale', 'cfd_threshold', 'savecfd')

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)
    
    def initialise(self):
        """ Set up the CFD and trapezoid parameters
        """
        # CFD parameters
        self.delay = int(self.config["algorithm"]["delay"])
        self.scale = int(self.config["algorithm"]["scale"])
        self.cfd_threshold = float(self.config["algorithm"]["cfd_threshold"])
        if "savecfd" in self.config["algorithm"]:
            self.savecfd = bool(self.config["algorithm"]["savecfd"])
        else:
            self.savecfd = False

    def execute(self):
        """ Caclulates the waveform CFD
        """
        # Get the actual waveform, finally.
        waveform = self.store.get(self.config["waveform"])
        waveform = self.store.get(self.config["waveform"])
        if self.store.check(f"{self.name}:length"):
            length = self.store.get(f"{self.name}:length")
        else:
            length = len(waveform)
            self.store.put(f"{self.name}:length", length, "PERM")

        # Parameters and formula from Digital techniques for real-time pulse shaping in radiation measurements
        # https://doi.org/10.1016/0168-9002(94)91652-7
        cfd = []
        cross_threshold = False
        CFDTime = -999
        for i in range(length):
            cfd.append(self.scale * self._v(waveform, i) - self._v(waveform, i-self.delay))
            if not cross_threshold:
                cross_threshold = cfd[i] > self.cfd_threshold
            elif CFDTime == -999:
                # Ok, the threshold has been crossed
                # (and we only want to calculate it once, but still want to get 
                # the whole cfd for now)
                if cfd[i] < 0 and cfd[i-1] >= 0:
                    # Now we've crosssed the 0 point
                    f = cfd[i-1] / (cfd[i-1] - cfd[i])
                    CFDTime = i-1+f
                    if not self.savecfd:
                        # We're done here :)
                        break
        
        # if use_trap:
        #     # Store the trap
        #     self.store.put(f"{self.name}:trapezoid", trap)
        #     # CFDTime -= (gap+rise)
        self.store.put(self.name, CFDTime)
        if self.savecfd:
            self.store.put(f"{self.name}Trace", cfd)

    def _v(self, waveform, i):
        """ returns the i'th element of a waveform or 0 if out of range
        """
        try:
            return waveform[i]
        except:
            return 0

# EOF