""" Make one-dimensional ROOT plot. The plot consists of a python dictionary 
named after the object, where entries are dictionaries having input names as 
keys and histograms as values.
"""

from pyrate.core.Algorithm import Algorithm

from pyrate.utils import strings as ST

import ROOT as R


class Make1DPlot(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def initialise(self, config):
        """Check if required histograms already exist in the input or the store.
        If they do, retrieve them and declare the object as ready. This will
        skip the execute step.
        """
        # ----------------------------------------------------------------------
        # Creates the main data structure which is the output of the object.
        # N.B.: do not call get on config["name"] if this does not already exist
        # on the store. It will generate a recursion loop. Always check first.
        # ----------------------------------------------------------------------
        # if not self.store.check(config["name"], "PERM"):
        #    histograms = {}
        #    self.store.put(config["name"], histograms, "PERM")
        # else:
        #    histograms = self.store.get(config["name"], "PERM")

        i_name = self.store.get("INPUT:name")

        for region, variable in config["algorithm"]["binning"].items():
            for v_name, v_bins in variable.items():

                h_name = "_".join(["hist", region, v_name])

                obj_name = ":".join([i_name, h_name])

                # if not i_name in histograms:
                #    histograms[i_name] = {}

                # histograms[i_name][h_name] = None

                # Only creates the object if it is not retrievable from the INPUT.
                h = self.store.get(obj_name, "PERM")

                # empty_histograms = 0

                if not h:
                    # empty_histograms += 1

                    binning = ST.get_items(v_bins)
                    h = R.TH1F(
                        h_name,
                        h_name,
                        int(binning[0]),
                        float(binning[1]),
                        float(binning[2]),
                    )
                    self.store.put(obj_name, h, "PERM")

                # histograms[i_name][h_name] = h

        # This is a criterion to tell the Run that the execute step can be avoided.
        # if not empty_histograms:
        #    self.store.put(config["name"], "READY")

    def execute(self, config):
        """Fills histograms."""
        # histograms = self.store.get(config["name"], "PERM")

        i_name = self.store.get("INPUT:name")

        for region, variable in config["algorithm"]["binning"].items():
            for v_name, v_bins in variable.items():

                h_name = "_".join(["hist", region, v_name])
                obj_name = ":".join([i_name, h_name])
                obj_counter = ":".join([obj_name, "counter"])

                if not self.store.check(obj_counter):
                    self.store.put(obj_counter, "done")
                    self.store.get(obj_name, "PERM").Fill(1, 1)

    def finalise(self, config):
        """Makes the plot."""
        pass


# EOF
