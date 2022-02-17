""" Generic calculator using DIjkstra's ShuntingYard algorithm.  Takes an infix equation string, converts it to a postfix (reverse polish notation) vector and solves.
    Input variables can be any string that can be converted to a float or a separate object.

    Required parameters:
        equation: (string) Infix equation string
        variables: List of variables used in the equation can be floats or objects in the store
    
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


class Calculator(Algorithm):
    __slots__ = ["opPrecedence", "eqnStr", "variables", "pnVec", "result"]

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)
        self.opPrecedence = {"(": -1, "+": 2, "-": 2, "*": 3, "/": 3}

    def initialise(self):
        self.eqnStr = self.config["equation"]
        self.variables = self.config["variables"]
        self.ShuntingYard()

    def execute(self):
        """Calculates the ratio of the two input charges"""
        self.calc()
        if len(self.result) == 1:
            self.store.put(self.name, float(self.result[0]))

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
        except ValueError:
            return False

    # -------------------------------------------------------------------
    def GetVariable(self, var):
        # Gets a string, if it's numeric return the float value, if it's a variable check the variable value
        # If the variable value is a number return the float otherwise get the value from the store
        if self.IsFloat(var):
            return float(var)
        else:
            var = self.variables[var]
            if self.IsFloat(var):
                return float(var)
            else:
                return float(self.store.get(var))

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

            self.result.append(str(res))