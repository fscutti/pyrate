""" Calculates the X1 charge ratio variable, used to describe pulse shape, as defined in
    Characterization of SABRE crystal NaI-33 with direct underground counting (arXiv:2012.02610)

    Required parameters:
        impedance: (float) the impedance of the signal
        rate: (float) the sample rate of the digitiser
        unit: (str)/(float) the desired output charge unit.
              Accepts strings: e.g. C, mC, uC, nC, pC
              otherwise accepts floats for the charge to be mulitplied by
        waveform_unit: (str)/(float) The units of the input waveform
                       Accepts strings: e.g. V or mV
                       Otherwise accepts floats for the appropriate conversion
                       for non-physical waveforms (ADC).
        cfd_delay: (int) The delay used in the CFD timing algorithm, is subtracted off of
                    a cfd PulseStart to get the actual PulseStart
        waveform: The waveform to caluclate the charge of (typically physcial)
        pulse_start: The trigger location of the pulse (either CFD or something else)
    
    Required states:
        initialise:
            output:
        execute:
            input: <Waveform object>, <PulseStart object>
    
    Example config:
    
    DAMAX1_CHX:
        algorithm:
            name: DAMAX1
            rate: 500e6
            cfd_delay: 10
        initialise:
            output:
        execute:
            input: CorrectedWaveform_CHX, PulseStart_CHX
        waveform: CorrectedWaveform_CHX
        pulse_start: PulseStart_CHX
"""

import numpy as np
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate


class DAMAX1(Algorithm):
    __slots__ = ("delay", "sample_rate")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self):
        """Prepare Initialised variables - CFD delay and digitiser sample rate"""
        # Deal with CFD delay if CFD is being used as the timing
        self.sample_rate = float(self.config["rate"])
        self.delay = 0

        if "cfd_delay" in self.config:
            self.delay = self.config["cfd_delay"]

    def execute(self):
        """Charge ratio X1 defined according to:
        Characterization of SABRE crystal NaI-33 with direct underground counting (arXiv:2012.02610)"""

        pulse_start = self.store.get(self.config["input"]["pulse_start"])
        waveform = self.store.get(self.config["input"]["waveform"])
        if pulse_start is Pyrate.NONE or waveform is Pyrate.NONE:
            self.store.put(self.name, Pyrate.NONE)
            return
        
        pulse_start -= self.delay
        window1 = (int(pulse_start + 100*(self.sample_rate*1e-9)), int(pulse_start + 600*(self.sample_rate*1e-9)))
        window2 = (int(pulse_start), int(pulse_start + 600*(self.sample_rate*1e-9)))
        
        # Calcualte the actual charge over the window
        charge1 = np.sum(waveform[window1[0] : window1[1]])
        charge2 = np.sum(waveform[window2[0] : window2[1]])

        if (charge1<=0 or charge2<=0):
            self.store.put(self.name, Pyrate.NONE)
            return
        
        X1_ChargeRatio = charge1/charge2
        self.store.put(self.name, X1_ChargeRatio)


# EOF
