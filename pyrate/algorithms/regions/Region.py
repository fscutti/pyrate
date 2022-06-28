""" Standard Region algorithm.

mySelection:
        algorithm: Region
        scale: 42.
        input:
            selection:
                - "myVar1 >= 10."
                - "myVar2 < 0.1 || myVar1 >= 500."
                - "myWeight1, myWeight2"
                - "myCut1 && myCut2"

A region is represented by a dictionary with a integer indicating whether a selection 
is passed and a set of weights. The option is_subregion_of indicates whether the region
under consideration depends on other regions. Weight overlaps are checked and eliminated.
"""
import sys

from pyrate.core.Algorithm import Algorithm
from pyrate.utils import functions as FN


class Region(Algorithm):
    __slots__ = "passed"

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)
        self.passed = False

    def get_variables(self, cut):
        
        # this parses weights.
        #cut = cut.replace(",", "&&")
        
        # this parses cuts.
        cut = cut.replace(" ", ",")

        symbols = [
            ">=",
            "<=",
            ">",
            "<",
            "==",
            "!=",
            "||",
            "&&",
            "False",
            "True",
            "false",
            "true",
        ]

        for s in symbols:
            cut = cut.replace(s, ",").replace("(", "").replace(")", "")
        
        return set(v for v in cut.split(",") if not self.is_number(v))

    def check_var(self, v, c):
        return v in self.get_variables(c)

    def is_number(self, v):
        
        try:
            float(v)
            return True
        
        except ValueError:
            if v == "":
                return True
            else:
                return False
 
    def parse_input(self, selection):

        parsed = {}

        for s in selection:

            for cut in s.split("||"):

                conditions = cut.split("&&")

                for c_idx, c in enumerate(conditions):

                    variables = self.get_variables(c)

                    for v_idx, v in enumerate(variables):

                        while v in parsed:
                            v = ":" + v

                        if v_idx == len(variables) - 1:
                            parsed[v] = c

                            if c_idx == len(conditions) - 1:
                                parsed[v] += ";"

                        else:
                            parsed[v] = None

        return parsed

    def execute(self, condition):

        is_passed = eval(condition)

        value = int(is_passed)

        if "scale" in self.config:
            value *= float(scale)

        if "weights" in self.config["input"]:
            for w in self.config["input"]["weights"]:
                value *= self.store.get

        self.put(self.name, value)

        # interruptor condition.
        # warning this is not complete.
        if condition.endswith(";"):
            return True


# EOF
