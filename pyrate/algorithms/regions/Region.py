""" Standard Region algorithm.

mySelection:
        algorithm: Region
        input:
            selection:
                - "myVar1 >= 10."
                - "myVar2 < 0.1 || myVar1 >= 500."
                - "myWeight1, myWeight2"
                - "myCut1 && myCut2"

"""
import sys

from pyrate.core.Algorithm import Algorithm
from pyrate.utils import functions as FN
from pyrate.utils import enums as EN


class Region(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def get_variables(self, cut):

        cut = cut.replace(" ", ",")

        # The logic operators && and || are not supported.
        symbols = [
            ">=",
            "<=",
            ">",
            "<",
            "==",
            "!=",
            "and",
            "or",
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
        return {selection: self.get_variables(selection)}

    def execute(self, condition):

        is_passed = 1

        for c in condition.split(","):

            for v in self.get_variables(c):

                c = c.replace(v, f"self.store.get('{v}')")

            is_passed *= eval(c)

        current_value = self.store.get(self.name)

        if current_value is not EN.Pyrate.NONE:
            current_value *= float(is_passed)

        self.store.put(self.name, is_passed)

        return bool(is_passed)


# EOF
