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
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)
    
    def initialise(self, config):
        """ Set up the CFD and trapezoid parameters
        """
        # CFD parameters
        delay = int(config["algorithm"]["delay"])
        scale = int(config["algorithm"]["scale"])
        cfd_threshold = float(config["algorithm"]["cfd_threshold"])
        if "savecfd" in config["algorithms"]:
            savecfd = bool(config["algorithm"]["savecfd"])
        else:
            savecfd = False

        self.store.put(f"{config['name']}:delay", delay)
        self.store.put(f"{config['name']}:scale", scale)
        self.store.put(f"{config['name']}:cfd_threshold", cfd_threshold)
        self.store.put(f"{config['name']}:savecfd", savecfd)


    def execute(self, config):
        """ Caclulates the waveform CFD
        """
        # Get the parameters and mode
        delay = self.store.get(f"{config['name']}:delay")
        scale = self.store.get(f"{config['name']}:scale")
        cfd_threshold = self.store.get(f"{config['name']}:cfd_threshold")
        savecfd = self.store.get(f"{config['name']}:savecffd")

        # Get the actual waveform, finally.
        waveform = self.store.get(config["waveform"])
        waveform = self.store.get(config["waveform"])
        if self.store.check(f"{config['name']}:length"):
            length = self.store.get(f"{config['name']}:length")
        else:
            length = len(waveform)
            self.store.put(f"{config['name']}:length", length, "PERM")

        # Parameters and formula from Digital techniques for real-time pulse shaping in radiation measurements
        # https://doi.org/10.1016/0168-9002(94)91652-7
        cfd = []
        cross_threshold = False
        CFDTime = -999
        for i in range(length):
            cfd.append(scale * self._v(waveform, i) - self._v(waveform, i-delay))
            if not cross_threshold:
                cross_threshold = cfd[i] > cfd_threshold
            elif CFDTime == -999:
                # Ok, the threshold has been crossed
                # (and we only want to calculate it once, but still want to get 
                # the whole cfd for now)
                if cfd[i] < 0 and cfd[i-1] >= 0:
                    # Now we've crosssed the 0 point
                    f = cfd[i-1] / (cfd[i-1] - cfd[i])
                    CFDTime = i-1+f
                    if not savecfd:
                        # We're done here :)
                        break
        
        # if use_trap:
        #     # Store the trap
        #     self.store.put(f"{config['name']}:trapezoid", trap)
        #     # CFDTime -= (gap+rise)
        self.store.put(config["name"], CFDTime)
        if savecfd:
            self.store.put(f"{config['name']}Trace", cfd)

    def _v(self, waveform, i):
        """ returns the i'th element of a waveform or 0 if out of range
        """
        try:
            return waveform[i]
        except:
            return 0

# EOF