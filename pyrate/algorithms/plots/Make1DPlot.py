""" Make one-dimensional ROOT plot. The plot consists of a python dictionary 
named after the object, where entries are dictionaries having input names as 
keys and histograms as values. This algorithm requires the definition of regions
implementing a selection. If the region is passed it fills the histograms with 
the corresponding region weight.
"""
import os

from pyrate.core.Algorithm import Algorithm

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN

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
        i_name = self.store.get("INPUT:name", "TRAN")

        for region, var_type in config["algorithm"]["regions"].items():
            for v_type, variable in var_type.items():
                for v_name, v_bins in variable.items():

                    h_name = self.get_hist_name(region, v_name)

                    # WARNING: if the histogram is not present in the input the value of
                    # h is None. Notice that the input name is not guaranteed to be in the
                    # name of the histogram so this is an operation on the TRAN store.
                    # Later, if found, the histogram will need to be put on the PERM store.
                    h = self.store.copy("INPUT:" + h_name, "TRAN")
                    # The object is unique and has been saved on the TRAN store. When later
                    # it will be put on the PERM store it will anyway disappear from it after
                    # the TRAN store is cleared after every target loop. Therefore above we
                    # don't simply use the self.store.get instruction but self.store.copy
                    # to copy the object and prevent it from being deleted.

                    # Only creates the object if it is not retrievable from the INPUT.
                    if not h:
                        binning = ST.get_items(v_bins)
                        h = R.TH1F(
                            h_name,
                            h_name,
                            int(binning[0]),
                            float(binning[1]),
                            float(binning[2]),
                        )

                        # put the object on the store with a different name which
                        # includes the input name, as our final plot will be a stack
                        # potentially including histograms from different samples.
                        obj_name = self.get_object_name(i_name, h_name)
                        self.store.put(obj_name, h, "PERM")

        # ----------------------------------------------------------------------
        # This would be the place to puth the a config['name'] object on the store,
        # should this be ready for the finalise step.
        # ----------------------------------------------------------------------

    def execute(self, config):
        """Fills histograms."""
        i_name = self.store.get("INPUT:name")

        for region, var_type in config["algorithm"]["regions"].items():
            for v_type, variable in var_type.items():
                for v_name, v_bins in variable.items():

                    weight = self.store.get(region)

                    if weight:

                        h_name = self.get_hist_name(region, v_name)
                        obj_name = self.get_object_name(i_name, h_name)
                        obj_counter = ":".join([obj_name, "counter"])

                        if not self.store.check(obj_counter):
                            self.store.put(obj_counter, "done")
                            variable = self.store.get(v_name)
                            self.store.get(obj_name, "PERM").Fill(variable, weight)

    def finalise(self, config):
        """Makes the plot."""

        plots = {}

        inputs = ST.get_items(config["name"].split(":", -1)[-1])

        for region, var_type in config["algorithm"]["regions"].items():
            for v_type, variable in var_type.items():
                for v_name, v_bins in variable.items():

                    path = f"region/{region}/{v_type}"
                    p_name = f"plot_{region}_{v_name}"

                    p_entry = os.path.join(path, p_name)

                    plots[p_entry] = R.THStack(p_name, p_name)

                    # ------------------------
                    # Fill the stack
                    # ------------------------
                    for i_name in inputs:

                        h_name = self.get_hist_name(region, v_name)
                        obj_name = self.get_object_name(i_name, h_name)

                        h = self.store.get(obj_name, "PERM")
                        plots[p_entry].Add(h)

        # One should create a canvas here...

        self.store.put(config["name"], plots, "PERM")

    def get_hist_name(self, region, variable):
        """Builds histogram name."""
        return f"hist_{region}_{variable}"

    def get_object_name(self, iname, histogram):
        """Builds object name, which is how histograms are identified on the PERM store."""
        return f"{iname}:{histogram}"


# EOF
