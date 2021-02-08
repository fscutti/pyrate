""" .
"""
import os
from copy import copy

from pyrate.core.Algorithm import Algorithm

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN

import ROOT as R


class Make1DHistPlot(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def initialise(self, config):
        """Prepares histograms."""
        i_name = self.store.get("INPUT:name", "TRAN")

        for f_name, f_attr in config["algorithm"]["folders"].items():
            for v_name, v_attr in f_attr["variables"].items():
                for r_name in self.make_regions_list(f_attr):

                    h_name = self.get_hist_name(r_name, v_name)

                    path = ""
                    if "path" in f_attr:
                        path = f_attr["path"]

                    h = self.store.copy("INPUT:" + os.path.join(path, h_name), "TRAN")

                    obj_name = self.get_object_name(i_name, h_name)

                    if not h:
                        h = self.make_hist(h_name, v_attr, f_attr)

                    self.store.put(obj_name, h, "PERM")

    def execute(self, config):
        """Fills histograms."""
        i_name = self.store.get("INPUT:name")

        for f_name, f_attr in config["algorithm"]["folders"].items():
            for v_name, v_attr in f_attr["variables"].items():
                for r_name in self.make_regions_list(f_attr):

                    h_name = self.get_hist_name(r_name, v_name)
                    obj_name = self.get_object_name(i_name, h_name)

                    obj_counter = ":".join([obj_name, "counter"])

                    if not self.store.check(obj_counter):

                        r_weight = 1

                        for sr_name in r_name.split("_"):
                            sr_weight = self.store.get(sr_name)
                            r_weight *= sr_weight

                            if r_weight == 0:
                                break

                        if r_weight:
                            variable = self.store.get(v_name)
                            self.store.get(obj_name, "PERM").Fill(variable, r_weight)

                            self.store.put(obj_counter, "done")

    def finalise(self, config):
        """Makes the plot."""

        plot_collection = {}

        inputs = ST.get_items(config["name"].split(":", -1)[-1])

        for f_name, f_attr in config["algorithm"]["folders"].items():
            for v_name, v_attr in f_attr["variables"].items():
                for r_name in self.make_regions_list(f_attr):

                    h_name = self.get_hist_name(r_name, v_name)

                    for i_name in inputs:
                        obj_name = self.get_object_name(i_name, h_name)

                        path = f_name

                        if "path" in f_attr:
                            path = os.path.join(f_attr["path"], path)

                        self.make_plots_dict(plot_collection, h_name, path, f_attr)
        
        # make plots
        # this can also be done in the make_plots_dict function.
        print(plot_collection)

    def make_regions_list(self, folder):

        regions_list = []
        overlay_regions = False

        if "overlay" in folder:
            overlay_regions = folder["overlay"] == "regions"

        if "regions" in folder:
            regions = ST.get_items(folder["regions"])

            regions_list = [
                "_".join(regions) if not overlay_regions else r for r in regions
            ]

        return regions_list

    def get_hist_name(self, region, variable):
        """Builds histogram name."""
        return f"hist_{region}_{variable}"

    def get_object_name(self, input_name, histogram):
        """Builds object name, which is how histograms are identified on the PERM store."""
        return f"{input_name}:{histogram}"

    def get_ROOT_colors(self, my_color):

        ROOT_color_name = "kBlack"
        ROOT_color_mod = ""
        color = 1

        if "+" in my_color:
            ROOT_color_name, ROOT_color_mod = my_color.split("+")
            color = getattr(R, ROOT_color_name) + R.Int_t(ROOT_color_mod)

        elif "-" in my_color:
            ROOT_color_name, ROOT_color_mod = my_color.split("-")
            color = getattr(R, ROOT_color_name) - R.Int_t(ROOT_color_mod)
        else:
            color = getattr(R, my_color)

        return int(color)

    def make_hist(self, h_name, variable, folder):

        var = self.get_var_dict(variable)

        h = copy(R.TH1F(h_name, h_name, var["n_bins"], var["x_low"], var["x_high"]))

        h.GetXaxis().SetTitle(var["x_label"])
        h.GetYaxis().SetTitle(var["y_label"])

        color = None

        if "overlay" in folder:

            if folder["overlay"] == "regions":

                for idx, r_name in enumerate(self.make_regions_list(folder)):
                    if r_name in h_name:

                        if var["color"]:
                            color = self.get_ROOT_colors(
                                "+".join([var["color"], str(idx)])
                            )

            elif folder["overlay"] == "inputs":

                if "color" in self.store.get("INPUT:config"):
                    color = self.get_ROOT_colors(
                        self.store.get("INPUT:config")["color"]
                    )

            elif folder["overlay"] == "variables":

                if var["color"]:
                    color = self.get_ROOT_colors(var["color"])

        if color:
            h.SetLineColor(color)
            h.SetMarkerColor(color)

        return h

    def make_plots_dict(self, plots, h_name, path, folder):

        c_name = None

        mode = "overlay"

        if "overlay" in folder:

            if folder["overlay"] == "regions":
                c_name = f"{mode}_" + h_name.rsplit("_", 1)[-1]

            elif folder["overlay"] == "variables":
                c_name = h_name.rsplit("_", 1)[0].replace("hist", mode)
            
            elif folder["overlay"] == "inputs":
                c_name = h_name.replace("hist", mode)

        if not c_name:

            mode = "stack"

            c_name = h_name.replace("hist", mode)

        if not c_name in plots:
            plots[os.path.join(path, c_name)] = [h_name]
        else:
            plots[os.path.join(path, c_name)].append(h_name)

    def get_var_dict(self, variable):

        a = ST.get_items(variable)

        d = {
            "n_bins": int(a[0]),
            "x_low": float(a[1]),
            "x_high": float(a[2]),
            "x_label": a[3],
            "y_label": a[4],
            "color": None,
            "legend_entry": None,
        }

        if len(a) >= 6:
            d["color"] = a[5]

        if len(a) >= 7:
            d["legend_entry"] = a[6]

        return d


# EOF
