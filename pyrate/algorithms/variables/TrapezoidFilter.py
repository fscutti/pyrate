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

import numpy as np
from pyrate.core.Algorithm import Algorithm

class TrapezoidFilter(Algorithm):
    __slots__ = ("rise", "gap", "period", "tau", "zeropole", "traplen", "M", "dn0", "dn1", "dn2", "dn3")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self):
        """Set up the trapezoid parameters"""
        # Trapezoid parameters
        self.rise = int(self.config["algorithm"]["rise"])
        self.gap = int(self.config["algorithm"]["gap"])
        self.period = 1 / float(self.config["algorithm"]["rate"])
        self.tau = float(self.config["algorithm"]["tau"])
        if "zeropole" in self.config["algorithm"]:
            self.zeropole = bool(self.config["algorithm"]["zeropole"])
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

    def execute(self):
        """Caclulates the trap filtered waveform"""
        waveform = self.store.get(self.config["waveform"])
        waveform_len = waveform.size

        if (waveform_len + self.traplen) > self.dn0.size:
            # Our waveform is larger than the storage
            # we need to grow our arrays
            self.dn0.resize(waveform_len + self.traplen)
            self.dn1.resize(waveform_len + self.traplen)
            self.dn2.resize(waveform_len + self.traplen)
            self.dn3.resize(waveform_len + self.traplen)

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
        self.dn0.fill(0)
        self.dn1.fill(0)
        self.dn2.fill(0)
        self.dn3.fill(0)

# EOF
