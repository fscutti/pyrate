""" Calculates the ratio of two charge windows. 
    Uses pre-calculated charges, set up as separate objects
    ChargeRatio = q1/q2

    Required parameters:
        charge1: (float) Charge ratio numerator (object), calculated by a 
                         previously defined charge algorithm
        charge2: (float) Charge ratio denominator (object) see above.
    
    Required states:
        execute:
            input: <Charge object 1>, <Charge object 2>
            output: SELF
    
    Example config:
    PromptDelayChargeRatio_CHX:
        algorithm:
            name: ChargeRatio
        execute:
            input: PromptCharge_CHX, DelayCharge_CHX
        charge1: PromptCharge_CHX
        charge2: DelayCharge_CHX
"""

from pyrate.core.Algorithm import Algorithm

class ChargeRatio(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):
        """ Calculates the ratio of the two input charges
        """
        q1 = self.store.get(config["charge1"])
        q2 = self.store.get(config["charge2"])
        if q2 == 0:
            ChargeRatio = float("inf")
            # print("WARNING: Q2 = 0, ChargeRatio is infinite. Check integration windows")
        else:
            ChargeRatio = q1/q2
        self.store.put(config["name"], ChargeRatio)

# EOF