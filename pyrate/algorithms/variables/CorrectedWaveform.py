""" Converts the raw waveform into a baseline subtracted and polarity 
    corrected, physical units waveform.
    This takes in the raw waveform as input, but also the polarity of 
    the raw waveform as well as the baseline calculated by the baseline algorithm.
    The polarity is the only user defined input.
    Multiplies physcial waveform by the polarity to correct it, 
    after having subtracted the baseline.

    Required parameters:
        In algorithm:
            vpp:      Voltage range of the digitiser
            adcrange: Number of bits in the digitiser's ADC range
            polarity: Polarity of the input waveform: (pos)itive, (neg)ative,
                      1, -1 etc...
        
        In main:
            baseline: A Baseline object
            waveform: A Waveform object

    Requires states:
        initialise:
            output:
        execute:
            intput: <Waveform object>, <Baseline object>

    Example config:

    CorrectedWaveform_CHX:
        algorithm: 
            name: CorrectedWaveform
            vpp: 2.5
            adcrange: 16384
            polarity: neg
            units: mV
        initialise:
            output:
        execute:
            input: RawWaveform_CHX, Baseline_CHX
        raw_waveform: RawWaveform_CHX
        baseline: Baseline_CHX
        wc_waveform: EVENT:GROUP:CHX:RawWaveform
"""

from pyrate.core.Algorithm import Algorithm
import sys

wf_units = {"V":1.0, "mV":1e3, "uV":1e6}

class CorrectedWaveform(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def initialise(self, config):
        """ Prepare the input waveform scaling and polarity
        """
        # Again we need to check the reader as it determines what kind of input
        # we could have and how we access its information
        # First we find out what kind of grouping is being used
        groups = self.store.get("GROUPS")

        # Temporary, needs fixing, not generalised for all possible group structures
        if groups[0] == '0':
            # Default, no group specified
            reader = self.store.get("INPUT:READER:name")
        else:
            reader = self.store.get(f"INPUT:READER:GROUP:name")
        
        # Convert to physical units
        if "units" in config["algorithm"]:
            units = config["algorithm"]["units"]
        else:
            units = "mV"
        if units in wf_units:
            units = wf_units[units]
        else:
            try:
                units = float(units)
            except:
                sys.exit("ERROR: in CorrectedWaveform config, please")

        # Handle the converison from ADC is appropriate
        if reader != "ReaderWaveCatcherMMAP":
            Vpp = float(config["algorithm"]["vpp"])
            BitRange = int(config["algorithm"]["adcrange"])

            # Conversion factor between ADC and mV
            conversion = (Vpp / BitRange) * units
            
            # Now work out the conversion
        else:
            conversion = units     # just convert to mV

        # Sets polarity constant based on user input.
        if "polarity" in config["algorithm"]:
            polarity = config["algorithm"]["polarity"]
        else:
            sys.exit("ERROR in CorrectedWaveform config, please provide a polarity")
        if "neg" in polarity.lower():
            polarity = -1
        elif "pos" in polarity.lower():
            polarity = 1
        else:
            try:
                polarity = int(polarity)
            except:
                sys.exit(f"Error: invalid polarity {polarity}")

        self.store.put(f"{config['name']}:polarity", polarity)
        self.store.put(f"{config['name']}:reader", reader)     
        self.store.put(f"{config['name']}:conversion", conversion)

    def execute(self, config):
        """ Calculates the baseline corrected waveform
        """
        reader = self.store.get(f"{config['name']}:reader")
        if reader == "ReaderWaveCatcherMMAP":
            waveform = self.store.get(config["wc_waveform"])
        else:
            waveform = self.store.get(config["raw_waveform"])
        waveform = self.store.get(config["waveform"])
        conversion = self.store.get(f"{config['name']}:conversion")
        polarity = self.store.get(f"{config['name']}:polarity")
        baseline = self.store.get(config["baseline"])
        
        # Flip the waveform if needed, and subtract baseline
        corrected_waveform = conversion * polarity * (waveform - baseline)
        self.store.put(config["name"], corrected_waveform)

# EOF