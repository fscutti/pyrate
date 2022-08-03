""" Generic calculator using python eval.

    Required parameters:
        equation: (string) Infix equation string
    
    Required inputs:
        variables: Variables with keys linked to the equation
    
    Example config:

    PromptDelayChargeRatio_CHX:
        algorithm: Calculator
        equation: A+(A+B)*(C+D)
        input:
            variables:
              - "A= 1; B= 11.5; C= PromptCharge_CHX; D= 3e-1;"
"""

from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate
import pyrate.utils.functions as FN
import pyrate.utils.strings as ST

import sys
import math
import numpy
import scipy


class Calculator(Algorithm):
    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def get_variables(self, s):

        values, variables = set(), set()

        for v in s.replace(" ", "").split(";"):
            variable, value = v.split("=")

            values.add(value)
            variables.add(variable)

        return variables, values

    def parse_input(self, initialisation):

        return {
            initialisation: set(
                v for v in self.get_variables(initialisation)[1] if not FN.is_float(v)
            )
        }

    def initialise(self, condition):
        self.executeMe = compile(self.config["equation"], "<string>", "eval")

        variables, values = self.get_variables(condition)

        self.variables = {var: val for var, val in zip(variables, values)}

        constantVars = {}
        self.storeVariables = {}

        for var, val in self.variables.items():

            if FN.is_float(val):
                self.storeVariables[var] = val

            else:
                constantVars[var] = val

        # capture some of the local variables and add the constant input variables
        self.locals = {}
        self.locals["self"] = locals()["self"]
        self.locals.update(constantVars)

        # capture the globals
        self.globals = globals()

    def execute(self, condition=None):
        # update variables from the store
        for storeVariable in self.storeVariables:

            self.locals[storeVariable] = self.store.get(
                self.storeVariables[storeVariable]
            )

            if self.locals[storeVariable] is Pyrate.NONE:
                self.store.put(self.name, Pyrate.NONE)

                return

        result = eval(self.executeMe, self.globals, self.locals)

        self.store.put(self.name, result)


# EOF
