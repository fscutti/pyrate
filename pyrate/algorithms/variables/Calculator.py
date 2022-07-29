""" Generic calculator using python eval.

    Required parameters:
        equation: (string) Infix equation string
        variables: List of variables used in the equation can be python values or objects in the store
    
    Required states:
        initialise:
            input:
        execute:
            input:
    
    Example config:
    PromptDelayChargeRatio_CHX:
        algorithm:
            name: Calculator
        equation: A+(A+B)*(C+D)
        variables:
          A: 1
          B: 11.5
          C: PromptCharge_CHX
          D: 3e-1
        initialise:
            input:
        execute:
            input: PromptCharge_CHX
"""

from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate

import sys
import math
import numpy
import scipy

class Calculator(Algorithm):
    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self):
        self.executeMe = compile(self.config["equation"], '<string>', 'eval')

        executeVars = []
        if self.config["execute"]["input"]:
            executeVars = self.config["execute"]["input"].split(", ")

        self.variables = self.config["variables"]
        variables = self.variables
        constantVars = {}
        self.storeVariables = {}
        for variable in variables:
            if variables[variable] in executeVars:
                self.storeVariables[variable] = variables[variable]
            else:
                constantVars[variable] = variables[variable]

        #capture some of the local variables and add the constant input variables
        self.locals = {}
        self.locals['self'] = locals()['self']
        self.locals.update(constantVars)

        #capture the globals
        self.globals = globals()


    def execute(self):
        #update variables from the store
        for storeVariable in self.storeVariables:
            self.locals[storeVariable] = self.store.get(self.storeVariables[storeVariable])
            if self.locals[storeVariable] is Pyrate.NONE:
                self.store.put(self.name, Pyrate.NONE)
                return

        result = eval(self.executeMe, self.globals, self.locals)
        self.store.put(self.name, result)

