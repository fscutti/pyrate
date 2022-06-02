""" Calculates the ratio of two numbers e.g. charge. 
    Uses pre-calculated values, set up as separate objects
    Ratio = x1/x2

    Required parameters:
        x1: (Number) Ratio numerator (object), calculated by a 
                         previously defined algorithm
        x2: (Number) Ratio denominator (object) see above.
    
    Required states:
        execute:
            input: <Number object 1>, <Number object 2>
    
    Example config:
    PromptDelayChargeRatio_CHX:
        algorithm:
            name: Ratio
        execute:
            input: PromptCharge_CHX, DelayCharge_CHX
        x1: PromptCharge_CHX
        x2: DelayCharge_CHX
"""

from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate

class Ratio(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self):
        """Calculates the ratio of the two input values"""
        x1 = self.store.get(self.config["input"]["x1"])
        x2 = self.store.get(self.config["input"]["x2"])
        if x1 is Pyrate.NONE or x2 is Pyrate.NONE:
            self.store.put(self.name, Pyrate.NONE)
            return
        elif x2 == 0:
            self.store.put(self.name, float("inf"))
            return
            # print("WARNING: x2 = 0, Ratio is infinite. Check integration windows")
        
        Ratio = x1 / x2
        self.store.put(self.name, Ratio)


# EOF
