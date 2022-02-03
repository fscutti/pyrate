""" A trapezoidal filter for waveforms.

    Required parameters:
        rise: (int) The rise time of the trapezoid filter
        gap:  (int) The width of the top of the trapezoid filter
        rate: (float) The sample rate of the digitiser
        tau:  (float) The decay constant of the pulse

    Optional parameters:
        zeropole: (Bool) True by default
    
    Required states:
        initialise:
            output:
        execute:
            input: <Waveform object>
            output: SELF
    
    Example config:

    TrapezoidFilter_CHX:
        algorithm:
            name: TrapezoidFilter
            rise: 10
            gap: 10
            rate: 500e6
            tau: 2e-6
            zeropole: True
        initialise:
            output:
        execute:
            input: CorrectedWaveform_CHX
            output: SELF
        waveform: CorrectedWaveform_CHX

"""

from pyrate.core.Algorithm import Algorithm

class TrapezoidFilter(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)
    
    def initialise(self, config):
        """ Set up the trapezoid parameters
        """        
        # Trapezoid parameters
        rise = int(config["algorithm"]["rise"])
        gap = int(config["algorithm"]["gap"])
        period = 1/float(config["algorithm"]["rate"])
        tau = float(config["algorithm"]["tau"])
        if "zeropole" in config["algorithms"]:
            zeropole = bool(config["algorithm"]["zeropole"])
        else:
            zeropole = True
        self.store.put(f"{config['name']}:rise", rise)
        self.store.put(f"{config['name']}:gap", gap)
        self.store.put(f"{config['name']}:period", period)
        self.store.put(f"{config['name']}:tau", tau)
        self.store.put(f"{config['name']}:zeropole", zeropole)

    def execute(self, config):
        """ Caclulates the trap filtered waveform
        """
        # Get the parameters
        rise = self.store.get(f"{config['name']}:rise")
        gap = self.store.get(f"{config['name']}:gap")
        period = self.store.get(f"{config['name']}:period")
        tau = self.store.get(f"{config['name']}:tau")
        zeropole = self.store.get(f"{config['name']}:zeropole")

        # Get the actual waveform, finally.
        waveform = self.store.get(config["waveform"])
        if self.store.check(f"{config['name']}:length"):
            length = self.store.get(f"{config['name']}:length")
        else:
            length = len(waveform)
            self.store.put(f"{config['name']}:length", length, "PERM")

        # Parameters and formula from Digital techniques for real-time pulse shaping in radiation measurements
        # https://doi.org/10.1016/0168-9002(94)91652-7
        d = 0
        dn = []
        p = []
        r = []
        trap = []
        for i in range(length):
            # Main formula
            d = self._v(waveform, i) - self._v(waveform, i-rise) - self._v(waveform, i-(gap + rise)) + self._v(waveform, i-(2*rise + gap))
            dn.append(d)
            if zeropole:
                M = tau/period + 0.5 # Pole-zero correction parameter
            else:
                M = 1
            p.append(self._v(p, i-1) + d)
            r.append(self._v(p, i) + M*d)
            trap.append(self._v(trap, i-1) + self._v(r, i)/(M*rise))
        
        self.store.put(f"{config['name']}", trap)

    def _v(self, waveform, i):
        """ returns the i'th element of a waveform or 0 if out of range
        """
        try:
            return waveform[i]
        except:
            return 0

# EOF