""" Calculates the X2 charge ratio variable, used to describe pulse shape, as defined in
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
    
    DAMAX2_CHX:
        algorithm:
            name: DAMAX2
            impedance: 50
            rate: 500e6
            unit: pC
            waveform_unit: mV
            cfd_delay: 10
        initialise:
            output:
        execute:
            input: CorrectedWaveform_CHX, PulseStart_CHX
        waveform: CorrectedWaveform_CHX
        pulse_start: PulseStart_CHX
"""

import sys
import numpy as np
from pyrate.core.Algorithm import Algorithm

wf_units = {"V": 1.0, "mV": 1e-3, "uV": 1e-6}
q_units = {"C": 1.0, "mC": 1e3, "uC": 1e6, "nC": 1e9, "pC": 1e12, "fC": 1e15}


class DAMAX2(Algorithm):
    __slots__ = ("charge_constant", "delay", "sample_rate")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self):
        """Prepare the constant for calculating charge"""
        # Deal with charge constants
        impedance = self.config["algorithm"]["impedance"]
        self.sample_rate = float(self.config["algorithm"]["rate"])
        charge_units = self.config["algorithm"]["unit"]
        self.delay = 0

        if "cfd_delay" in self.config["algorithm"]:
            self.delay = self.config["algorithm"]["cfd_delay"]

        if charge_units in q_units:
            charge_units = q_units[charge_units]

        else:
            try:
                charge_units = float(charge_units)

            except:
                sys.exit(
                    "ERROR: In algorithm Charge, unit parameter could not be converted to a float."
                )

        waveform_units = self.config["algorithm"]["waveform_unit"]

        if waveform_units in wf_units:
            waveform_units = wf_units[waveform_units]

        else:
            try:
                waveform_units = float(waveform_units)

            except:
                sys.exit(
                    "ERROR: In algorithm Charge, waveform_unit could not be converted to a float."
                )

        self.charge_constant = waveform_units * charge_units / (impedance * self.sample_rate)

    def execute(self):
        """Charge ratio X2 defined according to:
        Characterization of SABRE crystal NaI-33 with direct underground counting (arXiv:2012.02610)"""

        pulse_start = self.store.get(self.config["pulse_start"]) - self.delay

        window1 = (int(pulse_start), int(pulse_start + int(50*(self.sample_rate*1e-9))))
        window2 = (int(pulse_start), int(pulse_start + int(600*(self.sample_rate*1e-9))))
        
        waveform = self.store.get(self.config["waveform"])

        # Calcualte the actual charge over the window
        charge1 = np.sum(waveform[window1[0] : window1[1]]) * self.charge_constant
        charge2 = np.sum(waveform[window2[0] : window2[1]]) * self.charge_constant

        X2_ChargeRatio = charge1/charge2

        self.store.put(self.name, X2_ChargeRatio)


# EOF
