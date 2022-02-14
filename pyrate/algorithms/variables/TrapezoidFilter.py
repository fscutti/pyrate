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
        waveform: CorrectedWaveform_CHX

"""

from pyrate.core.Algorithm import Algorithm

class TrapezoidFilter(Algorithm):
    __slots__ = ('rise', 'gap', 'period', 'tau', 'zeropole', 'length')

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)
    
    def initialise(self):
        """ Set up the trapezoid parameters
        """        
        # Trapezoid parameters
        self.rise = int(self.config["algorithm"]["rise"])
        self.gap = int(self.config["algorithm"]["gap"])
        self.period = 1/float(self.config["algorithm"]["rate"])
        self.tau = float(self.config["algorithm"]["tau"])
        if "zeropole" in self.config["algorithm"]:
            self.zeropole = bool(self.config["algorithm"]["zeropole"])
        else:
            self.zeropole = True
        self.length = None

    def execute(self):
        """ Caclulates the trap filtered waveform
        """
        # Get the actual waveform, finally.
        waveform = self.store.get(self.config["waveform"])
        if self.length is None:
            self.length = len(waveform)

        # Parameters and formula from Digital techniques for real-time pulse shaping in radiation measurements
        # https://doi.org/10.1016/0168-9002(94)91652-7
        d = 0
        dn = []
        p = []
        r = []
        trap = []
        for i in range(self.length):
            # Main formula
            d = self._v(waveform, i) - self._v(waveform, i-self.rise) - self._v(waveform, i-(self.gap + self.rise)) + self._v(waveform, i-(2*self.rise + self.gap))
            dn.append(d)
            if self.zeropole:
                M = self.tau/self.period + 0.5 # Pole-zero correction parameter
            else:
                M = 1
            p.append(self._v(p, i-1) + d)
            r.append(self._v(p, i) + M*d)
            trap.append(self._v(trap, i-1) + self._v(r, i)/(M*self.rise))
        
        self.store.put(f"{self.name}", trap)

    def _v(self, waveform, i):
        """ returns the i'th element of a waveform or 0 if out of range
        """
        try:
            return waveform[i]
        except:
            return 0

# EOF