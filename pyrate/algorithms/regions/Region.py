""" Standard Region algorithm.
"""
import sys

from pyrate.core.Algorithm import Algorithm


class Region(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):
        """Computes region weight. If selection criteria are not satisfied the loop is interrupted.
        If the region is a subset of another set of regions their cumulative weight is added to
        the current.
        *******************************************************************************************
        WARNING: the weights overlap b/w subregions and their superset is NON CHECKED. It is the
        user responsibility to avoid overlaps.
        *******************************************************************************************
        """

        region = 1

        selection = []
        if "selection" in config:
            selection = config["selection"]

        weights = []
        if "weights" in config:
            weights = config["weights"]

        supersets = []
        if "is_subregion_of" in config:
            supersets = config["is_subregion_of"]

        for s in supersets:
            region *= self.store.get(s)

        if region:

            AND = 1
            and_selection = selection

            for and_s in and_selection:

                OR = 0
                or_selection = and_s.split("||")

                for or_s in or_selection:

                    variable_name, symbol, cut_value = self.get_selection(or_s)
                    variable_value = self.store.get(variable_name)

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

            region *= AND

            if region:

                for w in weights:

                    weight_value = self.store.get(w)
                    region *= weight_value

        self.store.put(config["name"], region)

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
