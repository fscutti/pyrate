""" The charge constant is calculated from the impedance, the sample rate, 
    waveform units, and a  conversion for the desired output charge units.
    ChargeConstant = Waveform units * 1/(Z * Sample rate) * charge units

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
    
    Required states:
        initialise:
            output:
    
    Example config:
    
    ChargeConstant_CHX:
        algorithm:
            name: ChargeConstant
            impedance: 50
            rate: 500e6
            unit: pC
            waveform_unit: mV
        initialise:
            output:
"""

import sys
from pyrate.core.Algorithm import Algorithm

wf_units = {"V":1.0, "mV":1e-3, "uV":1e-6}
q_units = {"C":1.0, "mC":1e3, "uC":1e6, "nC":1e9, "pC":1e12, "fC":1e15}

class ChargeConstant(Algorithm):
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
                sys.exit("ERROR: In algorithm ChargeConstant, unit parameter could not be converted to a float.")
        
        waveform_units = config["algorithm"]["waveform_unit"]
        if waveform_units in wf_units:
            waveform_units = wf_units[waveform_units]
        else:
            try:
                waveform_units = float(waveform_units)
            except:
                sys.exit("ERROR: In algorithm ChargeConstant, waveform_unit could not be converted to a float.")

        charge_constant = waveform_units * charge_units/(impedance * sample_rate)
        self.store.put(f"{config['name']}", charge_constant)

# EOF