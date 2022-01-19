""" Calculates the CFD of a waveform.
    From this it also calculates the CFD zero crossing point - i.e. the cfd time
    Optionally, it can use a trapezoid filter, and then calculate the CFD of 
    the trapezoid.
    Outputs the full CFD to the store, and saves the CFDTime as:
    "ObjectNameCFDTime"

    Because of the gap and rise time of the trapezoid, the CFDTime will be
    shifted by this amount. If using the trapezoid fiter this may need to be
    applied manually

    Required parameters:
        delay: (int)   The amount the CFD algorithm will delay the input trace
        scale: (float) The amount the CFD algorithm will scale the first trace 
                       in the calculation.
        cfd_threshold: (float) The minimum height the CFD must cross before a
                               zero crossing point can be calculated
    Optional parameters:
        trap: (bool) Determines whether the trapezoid filter is used for the 
                     CFD calculation
        === the following are required if using trap ===
        rise: (int) The rise time of the trapezoid filter
        gap:  (int) The width of the top of the trapezoid filter
        rate: (float) The sample rate of the digitiser
        tau:  (float) The decay constant of the pulse
    
    Required states:
        initialise:
            output:
        execute:
            input: <Waveform object>
            output: SELF, SEFLCFDTime
    
    Example config:

    CFD_CHX:
        algorithm:
            name: CFD
            delay: 5
            scale: 1
            cfd_threshold: 10
            trap: True
            rise: 10
            gap: 10
            rate: 500e6
            tau: 2e-6
        initialise:
            output:
        execute:
            input: CorrectedWaveform_CHX
            output: SELF, SELFCFDTime
        waveform: CorrectedWaveform_CHX

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

        self.store.put(f"{config['name']}:delay", delay)
        self.store.put(f"{config['name']}:scale", scale)
        self.store.put(f"{config['name']}:cfd_threshold", cfd_threshold)
        
        # Trapezoid parameters
        if "trap" in config["algorithm"]:
            trap = config["algorithm"]["trap"]
            if trap:
                rise = int(config["algorithm"]["rise"])
                gap = int(config["algorithm"]["gap"])
                period = 1/float(config["algorithm"]["rate"])
                tau = float(config["algorithm"]["tau"])
                self.store.put(f"{config['name']}:rise", rise)
                self.store.put(f"{config['name']}:gap", gap)
                self.store.put(f"{config['name']}:period", period)
                self.store.put(f"{config['name']}:tau", tau)
            self.store.put(f"{config['name']}:use_trap", trap)
        else:
            self.store.put(f"{config['name']}:use_trap", False)

    def execute(self, config):
        """ Caclulates the waveform CFD
        """
        # Get the parameters and mode
        delay = self.store.get(f"{config['name']}:delay")
        scale = self.store.get(f"{config['name']}:scale")
        cfd_threshold = self.store.get(f"{config['name']}:cfd_threshold")

        use_trap = self.store.get(f"{config['name']}:use_trap")
        if use_trap:
            rise = self.store.get(f"{config['name']}:rise")
            gap = self.store.get(f"{config['name']}:gap")
            period = self.store.get(f"{config['name']}:period")
            tau = self.store.get(f"{config['name']}:tau")

        # Get the actual waveform, finally.
        waveform = self.store.get(config["waveform"])
        length = len(waveform)

        # Parameters and formula from Digital techniques for real-time pulse shaping in radiation measurements
        # https://doi.org/10.1016/0168-9002(94)91652-7
        if use_trap:
            d = 0
            dn = []
            p = []
            r = []
            trap = []
        cfd = []
        cross_threshold = False
        CFDTime = -999
        for i in range(length):
            if use_trap:
                # Main formula
                d = self._v(waveform, i) - self._v(waveform, i-rise) - self._v(waveform, i-(gap + rise)) + self._v(waveform, i-(2*rise + gap))
                dn.append(d)
                M = tau/period + 0.5 # Pole-zero correction parameter
                p.append(self._v(p, i-1) + d)
                r.append(self._v(p, i) + M*d)
                trap.append(self._v(trap, i-1) + self._v(r, i)/(M*rise))
                cfd.append(scale * self._v(trap, i) - self._v(trap, i-delay))
            else:
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
        
        if use_trap:
            # Store the trap
            self.store.put(f"{config['name']}:trapezoid", trap)
            # CFDTime -= (gap+rise)
        self.store.put(config["name"], cfd)
        self.store.put(f"{config['name']}CFDTime", CFDTime)

    def _v(self, waveform, i):
        """ returns the i'th element of a waveform or 0 if out of range
        """
        try:
            return waveform[i]
        except:
            return 0

# EOF