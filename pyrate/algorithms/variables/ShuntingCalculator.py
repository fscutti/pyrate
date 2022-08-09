""" Generic calculator using DIjkstra's ShuntingYard algorithm.  Takes an infix equation string, converts it to a postfix (reverse polish notation) vector and solves.
    Input variables can be any string that can be converted to a float or a separate object.

    Required parameters:
        equation: (string) Infix equation string
    
    Required inputs:
        variables: Variables with keys linked to the equation
    
    Example config:

    PromptDelayChargeRatio_CHX:
        algorithm: ShuntingCalculator
        equation: A+(A+B)*(C+D)
        input:
            A: 1
            B: 11.5
            C: PromptCharge_CHX
            D: 3e-1
"""

from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate
import pyrate.utils.functions as FN
import pyrate.utils.strings as ST

class Calculator(Algorithm):
    __slots__ = ["opPrecedence", "eqnStr", "variables", "pnVec", "result"]

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)
        self.opPrecedence = {"(": -1, "+": 2, "-": 2, "*": 3, "/": 3}

    @property
    def input(self):
        """Getter method for input objects."""
        return self._input

    @input.setter
    def input(self, config_input):
        """Setter method for input objects."""
        if self._input == {}:
            for dependency in FN.get_nested_values(config_input):
                if self.IsFloat(dependency):
                    continue
                if not isinstance(dependency, list):
                    variables = set(ST.get_items(str(dependency)))
                    self._update_input(None, variables)

                else:
                    for string in dependency:
                        for condition, variables in self.parse_input(string).items():
                            self._update_input(condition, variables)

    def initialise(self, condition=None):
        """Initialises the equation and variables to be calculated"""
        self.eqnStr = self.config["equation"]
        self.variables = self.config["input"]
        self.ShuntingYard()

    def execute(self, condition=None):
        """Calculates a generic equation"""
        self.calc()
        if len(self.result) == 1:
            self.store.put(self.name, self.result[0])

    # -------------------------------------------------------------------
    def Arithmetic(self, op, varL, varR):
        # Basic arithmetic, performs and operation on 2 numbers and returns the result
        res = 0
        if op == "+":
            res = varL + varR
        elif op == "-":
            res = varL - varR
        elif op == "*":
            res = varL * varR
        elif op == "/":
            res = varL / varR
        return res

    # -------------------------------------------------------------------
    def IsFloat(self, var):
        # Checks if a string can be converted to a float
        try:
            float(var)
            return True
        except:
            return False

    # -------------------------------------------------------------------
    def GetVariable(self, var):
        # Gets a string, if it's numeric return the float value, if it's a variable check the variable value
        # If the variable value is a number return the float otherwise get the value from the store
        if self.IsFloat(var):
            return float(var)
        
        var = self.variables[var]
        if self.IsFloat(var):
            return float(var)
            
        var = self.store.get(var)
        if self.IsFloat(var):
            return float(var)
        
        return Pyrate.NONE

    # -------------------------------------------------------------------
    def ShuntingYard(self):
        # Dijkstra's ShuntingYard algorithm.  Converts an infix string to a postfix vector
        self.pnVec = []
        opVec = []
        for i in range(len(self.eqnStr)):
            c = self.eqnStr[i]
            if c == " ":
                continue
            elif c == "(":
                opVec.append(c)
            elif c == ")":
                while len(opVec) > 0:
                    op = opVec.pop()
                    if op != "(":
                        self.pnVec.append(op)
                    else:
                        break
            elif c in self.opPrecedence:
                while len(opVec) > 0:
                    op = opVec.pop()
                    if self.opPrecedence[op] >= self.opPrecedence[c]:
                        self.pnVec.append(op)
                    else:
                        opVec.append(op)
                        break
                opVec.append(c)
            else:
                self.pnVec.append(c)

        while len(opVec) > 0:
            self.pnVec.append(opVec.pop())

    # -------------------------------------------------------------------
    def calc(self):
        # Calculates the result of a postfix vector equation.
        self.result = []
        for i in self.pnVec:
            res = i
            if i in self.opPrecedence:
                varL = self.result.pop()
                varR = self.result.pop()
                varL = self.GetVariable(varL)
                varR = self.GetVariable(varR)
                res = self.Arithmetic(i, varL, varR)
            else:
                # If i is a variable
                res = self.GetVariable(i)
                if res is Pyrate.NONE:
                    self.result = [Pyrate.NONE]
                    return

            self.result.append(res)
