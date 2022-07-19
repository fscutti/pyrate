""" Calculates the charge - the sum over a region of a waveform scaled by 
    physical PMT and circuit parameters.
    Sums the waveform over a passed in window object. The charge constant is
    calculated from the impedance, the sample rate, waveform units, and a 
    conversion for the desired output charge units.
    Charge = 1/(Z * Sample rate) * Sum trace[i]

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
        waveform: The waveform to caluclate the charge of (typically physcial)
        window: (tuple) The start and stop window for calculating the charge
    
    Required states:
        initialise:
            output:
        execute:
            input: <Waveform object>, <Window object>
    
    Example config:
    
    Charge_CHX:
        algorithm:
            name: Charge
            impedance: 50
            rate: 500e6
            unit: pC
            waveform_unit: mV
        initialise:
            output:
        execute:
            input: CorrectedWaveform_CHX, Window_CHX
        waveform: CorrectedWaveform_CHX
        window: Window_CHX
"""
import sys
import numpy as np
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate

wf_units = {"V": 1.0, "mV": 1e-3, "uV": 1e-6}
q_units = {"C": 1.0, "mC": 1e3, "uC": 1e6, "nC": 1e9, "pC": 1e12, "fC": 1e15}


class Charge(Algorithm):
    __slots__ = "charge_constant"

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self, condition=None):
        """Prepare the constant for calculating charge"""
        # Deal with charge constants
        impedance = self.config["impedance"]
        sample_rate = float(self.config["rate"])
        charge_units = self.config["unit"]

        if charge_units in q_units:
            charge_units = q_units[charge_units]

        else:
            try:
                charge_units = float(charge_units)

            except:
                sys.exit(
                    "ERROR: In algorithm Charge, unit parameter could not be converted to a float."
                )

        waveform_units = self.config["waveform_unit"]

        if waveform_units in wf_units:
            waveform_units = wf_units[waveform_units]

        else:
            try:
                waveform_units = float(waveform_units)

            except:
                sys.exit(
                    "ERROR: In algorithm Charge, waveform_unit could not be converted to a float."
                )

        self.charge_constant = waveform_units * charge_units / (impedance * sample_rate)

    def execute(self, condition=None):
        """Calculates the charge by summing over the waveform"""
        window = self.store.get(self.config["input"]["window"])
        waveform = self.store.get(self.config["input"]["waveform"])

        # check for invalid windows
        if waveform is Pyrate.NONE or window is Pyrate.NONE:
            self.store.put(self.name, Pyrate.NONE)
            return

        # Calcualte the actual charge over the window
        Charge = np.sum(waveform[window[0] : window[1]]) * self.charge_constant

        self.store.put(self.name, Charge)


# EOF
