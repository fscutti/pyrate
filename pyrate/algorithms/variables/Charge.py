""" Calculates the charge - the sum over a region of a waveform scaled by 
    physical PMT and circuit parameters.
    Sums the waveform over a passed in window object. The charge constant is
    calculated from the impedance, and the sample rate.
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
            output: SELF
    
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
            output: SELF
        waveform: CorrectedWaveform_CHX
        window: Window_CHX
"""

import sys
from pyrate.core.Algorithm import Algorithm

wf_units = {"V":1.0, "mV":1e-3, "uV":1e-6}
q_units = {"C":1.0, "mC":1e3, "uC":1e6, "nC":1e9, "pC":1e12, "fC":1e15}

class Charge(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)
    
    def initialise(self, config):
        """ Prepare the constant for calculating charge
        """
        # Deal with charge constants
        impedance = config["algorithm"]["impedance"]
        sample_rate = float(config["algorithm"]["rate"])
        charge_units = config["algorithm"]["unit"]
        if charge_units in q_units:
            charge_units = q_units[charge_units]
        else:
            try:
                charge_units = float(charge_units)
            except:
                sys.exit("ERROR: In algorithm Charge, unit parameter could not be converted to a float.")
        
        waveform_units = config["algorithm"]["waveform_unit"]
        if waveform_units in wf_units:
            waveform_units = wf_units[waveform_units]
        else:
            try:
                waveform_units = float(waveform_units)
            except:
                sys.exit("ERROR: In algorithm Charge, waveform_unit could not be converted to a float.")

        charge_constant = waveform_units * 1e12/(impedance * sample_rate) # in pC
        self.store.put(f"{config['name']}:charge_constant", charge_constant)

    def execute(self, config):
        """ Calculates the charge by summing over the waveform
        """
        window = self.store.get(config["window"])
        # check for invalid windows
        if window == -999 or window is None:
            Charge = -999
        else:
            # good to go, let's get the charge constant
            charge_constant = self.store.get(f"{config['name']}:charge_constant")

            waveform = self.store.get(config["waveform"])
            # Calcualte the actual charge over the window
            Charge = sum(waveform[window[0]:window[1]]) * charge_constant
        self.store.put(config["name"], Charge)

# EOF