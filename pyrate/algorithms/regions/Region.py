""" Standard Region algorithm.

mySelection:
        algorithm: Region
        scale: 42.
        input:
            selection:
                - myVar1 >= 10.
                - myVar2 < 0.1 || myVar1 >= 500.
            weights: myWeight1, myWeight2

A region is represented by a dictionary with a integer indicating whether a selection 
is passed and a set of weights. The option is_subregion_of indicates whether the region
under consideration depends on other regions. Weight overlaps are checked and eliminated.
"""
import sys

from pyrate.core.Algorithm import Algorithm
from pyrate.utils import functions as FN


class Region(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def get_variables(self, cut):

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

        return set(v for v in cut.split(",") if v.isalpha())

    def check_var(self, v, c):
        return v in self.get_variables(c)

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

        self.put(self.name, value)
        

        # interruptor condition.
        if condition.endswith(";"):
            return True



    def execute(self, selection):
        """Computes region dictionary."""

        region = {"is_passed": 1, "weights": {}}

        selection = []
        if "selection" in self.config:
            selection = self.config["selection"]

        weights = []
        if "weights" in self.config:
            weights = self.config["weights"]

        supersets = []
        if "is_subregion_of" in self.config:
            supersets = self.config["is_subregion_of"]

        for s in supersets:
            super_region = self.store.get(s)

            region["is_passed"] *= super_region["is_passed"]

            for w_name, w_value in super_region["weights"].items():

                if not w_name in region["weights"]:
                    region["weigths"][w_name] = w_value

        if region["is_passed"]:

            AND = 1
            and_selection = selection

            for and_s in and_selection:

                OR = 0
                or_selection = and_s.split("||")

                for or_s in or_selection:

                    x, symbol, y = self.get_selection(or_s)

                    try:
                        x = eval(x)
                    except NameError:
                        x = self.store.get(x)
                    try:
                        y = eval(y)
                    except NameError:
                        y = self.store.get(y)

                    OR = eval(f"{x} {symbol} {y}")

                    if OR == 1:
                        break

                AND *= OR

                if AND == 0:
                    break

            region["is_passed"] *= AND

            if region["is_passed"]:

                for w_name in weights:

                    if "=" in w_name:
                        region["weights"][w_name] = float(
                            w_name.split("=")[-1].replace(" ", "")
                        )

                    else:
                        region["weights"][w_name] = self.store.get(w_name)

        self.store.put(self.name, region)

    def get_selection(self, selection):
        """Breaks down the selection criterion."""
        if " " in selection:
            selection = selection.replace(" ", "")

        for check in [">=", "<=", ">", "<", "==", "!="]:

            a, symbol, b = selection.partition(check)

            if symbol:
                return a, symbol, b

        sys.exit(f"ERROR: no symbol found for {selection}")


# EOF
