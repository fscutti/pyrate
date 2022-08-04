""" Calculates the ratio of two numbers e.g. charge. 
    Uses pre-calculated values, set up as separate objects
    Ratio = numerator/denominator

    Required inputs:
        numerator: (Number) Ratio numerator (object), calculated by a 
                         previously defined algorithm
        denominator: (Number) Ratio denominator (object) see above.
    
    Example config:
    PromptDelayChargeRatio_CHX:
        algorithm: Ratio
        input:
            numerator: PromptCharge_CHX
            denominator: DelayCharge_CHX
"""

from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate

class Ratio(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self, condition=None):
        """Calculates the ratio of the two input values"""
        numerator = self.store.get(self.config["input"]["numerator"])
        denominator = self.store.get(self.config["input"]["denominator"])
        if numerator is Pyrate.INVALID_VALUE or denominator is Pyrate.INVALID_VALUE:
            self.put_invalid()
            return
        elif denominator == 0:
            self.store.put(self.name, float("inf"))
            return
            # print("WARNING: denominator = 0, Ratio is infinite. Check integration windows")
        
        Ratio = numerator / denominator
        self.store.put(self.name, Ratio)


# EOF
