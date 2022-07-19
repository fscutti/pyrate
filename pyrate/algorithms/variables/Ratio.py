""" Calculates the ratio of two numbers e.g. charge. 
    Uses pre-calculated values, set up as separate objects
    Ratio = numerator/denominator

    Required parameters:
        numerator: (Number) Ratio numerator (object), calculated by a 
                         previously defined algorithm
        denominator: (Number) Ratio denominator (object) see above.
    
    Required states:
        execute:
            input: <Number object 1>, <Number object 2>
    
    Example config:
    PromptDelayChargeRatio_CHX:
        algorithm:
            name: Ratio
        execute:
            input: PromptCharge_CHX, DelayCharge_CHX
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
        numerator = self.store.get(self.config["numerator"])
        denominator = self.store.get(self.config["denominator"])
        if numerator is Pyrate.NONE or denominator is Pyrate.NONE:
            self.store.put(self.name, Pyrate.NONE)
            return
        elif denominator == 0:
            self.store.put(self.name, float("inf"))
            return
            # print("WARNING: denominator = 0, Ratio is infinite. Check integration windows")
        
        Ratio = numerator / denominator
        self.store.put(self.name, Ratio)


# EOF
