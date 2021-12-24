""" Converts physical waveform into a baseline subtracted and polarity 
    corrected waveform.
    This takes in the physical waveform as input, but also the polarity of 
    the physical waveform as well as the baseline calculated by the baseline algorithm.
    The polarity is the only user defined input.
    Multiplies physcial waveform by the polarity to correct it, 
    after having subtracted the baseline.

    Required parameters:
        In algorithm:
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
            polarity: neg
        initialise:
            output:
        execute:
            input: PhysicalWaveform_CHX, Baseline_CHX
        waveform: PhysicalWaveform_CHX
        baseline: Baseline_CHX
"""

from pyrate.core.Algorithm import Algorithm
import sys

class CorrectedWaveform(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def initialise(self, config):
        """ Prepare the polarity
        """
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

    def execute(self, config):
        """ Calculates the baseline corrected waveform
        """
        waveform = self.store.get(config["waveform"])
        polarity = self.store.get(f"{config['name']}:polarity")
        baseline = self.store.get(config["baseline"])

        # Flip the waveform if needed, and subtract baseline
        corrected_waveform = polarity * (waveform - baseline)
        self.store.put(config["name"], corrected_waveform)

# EOF