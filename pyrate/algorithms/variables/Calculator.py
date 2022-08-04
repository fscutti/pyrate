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

        self.constantVars = {}
        self.storeVars = {}

        for var, val in self.variables.items():

            if FN.is_float(val):
                self.constantVars[var] = float(val)
            else:
                self.storeVars[var] = val

        # capture some of the local variables and add the constant input variables
        self.locals = {}
        self.locals["self"] = locals()["self"]
        self.locals.update(self.constantVars)

        # capture the globals
        self.globals = globals()

    def execute(self, condition=None):
        # update variables from the store
        for storeVariable in self.storeVars:

            self.locals[storeVariable] = self.store.get(
                self.storeVars[storeVariable]
            )

            if self.locals[storeVariable] is Pyrate.INVALID_VALUE:
                self.put_invalid()
                return

        result = eval(self.executeMe, self.globals, self.locals)

        self.store.put(self.name, result)


# EOF
