""" This algorithm outputs a dictionary of path_in_output:[1d_plots] elements using ROOT.
Plots will be grouped under folders in the output ROOT file under paths which can eventually 
be specified.

Configuration:

     myObjectName:
         algorithm: 
             name: Make1DHistPlot
             folders:
               myFolder:
                   path: myPathInOutputROOTFile  - OPTIONAL. A default path will be built using myFolder -
                   regions: mySelection1, mySelection2 - OPTIONAL. Histograms will be filled with these selections in AND logic. -
                   variables:
                        myVar1: n_bins, x_low, x_high, x_title, y_title, ROOT_color 
                        myVar2: n_bins, x_low, x_high, x_title, y_title, ROOT_color 
                   overlay: regions - OPTIONAL. With this option the user can specifiy how to display overlaied histograms. -

The overlay option is not strictly required and works as follows: 

Not provided.      - A plot will be made for each variable, stacking all valid inputs relative to the AND of the declared regions. -
overlay: inputs    - A plot will be made for each variable, overlaying all valid inputs relative to the AND of the declared regions. -
overlay: someInput - If a specific input name is provided, this input will be overlaied against the stack of all other available. -
overlay: regions   - A plot will be made for each variable overlaying each declared region and all available inputs. -
overlay: variables - A plot will be made overlaying all available inputs and all available variables relative to the AND of the declared regions. -

ToDo: better adjust the style of the plots. Introduce ratio plots.

"""
import os
from copy import copy

from pyrate.core.Algorithm import Algorithm

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN

import ROOT as R

R.gStyle.SetOptStat(0)


class Make1DHistPlot(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def initialise(self, config):
        """Prepares histograms.
        If not found in the input already it will create new ones."""

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

                            if sr_name == "NOSEL":
                                continue

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

                        target_dir = config["name"].replace(",", "_").replace(":", "_")
                        path = os.path.join(target_dir, path)

                        self.make_plots_dict(plot_collection, obj_name, path, f_attr)

        # FN.pretty(plot_collection)

        canvas_collection = {}

        for f_path, p_dict in plot_collection.items():

            if not f_path in canvas_collection:
                canvas_collection[f_path] = []

            for p_name, m_dict in p_dict.items():

                l = copy(R.TLegend(0.1, 0.8, 0.9, 0.9))

                c = copy(R.TCanvas(p_name, "", 900, 800))

                c.SetTickx()
                c.SetTicky()

                c.cd()

                has_already_drawn = False
                h_stack = None

                for mode, h_list in m_dict.items():

                    if mode == "stack":
                        h_stack = copy(R.THStack("hs", ""))

                    for obj_name in h_list:
                        h = self.store.get(obj_name, "PERM")

                        l.AddEntry(h, obj_name, "pl")

                        if mode == "overlay":
                            h.Draw("same")
                            has_already_drawn = True

                        elif mode == "stack":
                            h_stack.Add(h)

                if h_stack:
                    if not has_already_drawn:
                        h_stack.Draw()
                    else:
                        h_stack.Draw("same")

                l = l.Clone()

                l.Draw()

                canvas_collection[f_path].append(c.Clone())

                c.Close()

        # FN.pretty(canvas_collection)

        self.store.put(config["name"], canvas_collection, "PERM")

    def get_var_dict(self, variable):
        """Build dictionary for variable attributes."""

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

    def get_hist_name(self, region, variable):
        """Builds histogram name."""
        return f"hist_{region}_{variable}"

    def get_object_name(self, input_name, histogram):
        """Builds object name, which is how histograms are identified on the PERM store."""
        return f"{input_name}:{histogram}"

    def get_ROOT_colors(self, my_color):
        """Get ROOT color."""

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

    def make_regions_list(self, folder):
        """Build list of selection regions considered for histogram filling."""

        overlay_regions = False
        regions_list = []

        if "overlay" in folder:
            overlay_regions = folder["overlay"] == "regions"

        if "regions" in folder:
            regions = ST.get_items(folder["regions"])

            regions_list = [
                "_".join(regions) if not overlay_regions else r for r in regions
            ]

        if not regions_list:
            return ["NOSEL"]

        return ST.remove_duplicates(regions_list)

    def make_hist(self, h_name, variable, folder):
        """Make histograms."""

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

    def make_plots_dict(self, plots, obj_name, path, folder):
        """Assign histogram content of plots."""

        i_name, h_name = obj_name.split(":")

        c_name = h_name.replace("hist", "plot")
        mode = "stack"

        if "overlay" in folder:

            if folder["overlay"] == "regions":
                c_name = "plot_" + h_name.rsplit("_", 1)[-1]
                mode = "overlay"

            elif folder["overlay"] == "variables":
                c_name = h_name.rsplit("_", 1)[0].replace("hist", "plot")
                mode = "overlay"

            elif folder["overlay"] == "inputs" or folder["overlay"] == i_name:
                mode = "overlay"

        if not path in plots:
            plots[path] = {}

        if not c_name in plots[path]:
            plots[path].update({c_name: {}})

        if not mode in plots[path][c_name]:
            plots[path][c_name].update({mode: [obj_name]})

        if not obj_name in plots[path][c_name][mode]:
            plots[path][c_name][mode].append(obj_name)


# EOF
