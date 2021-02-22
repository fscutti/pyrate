""" This algorithm outputs a dictionary of path_in_output:[1d_graphs] elements using ROOT.
Plots will be grouped under folders in the output ROOT file under paths which can eventually 
be specified. Plots are ROOT TProfile objects:
    https://root.cern.ch/doc/master/classTProfile.html#a521649c590ada6872c2e70809293a706

Configuration:

     myObjectName:
         algorithm: 
             name: Make1DProfilePlot
             folders:
               myFolder:
                   path: myPathInOutputROOTFile  - OPTIONAL. A default path will be built using myFolder -
                   regions: mySelection1, mySelection2 - OPTIONAL. Histograms will be filled with these selections in AND logic. -
                   variables:
                        myVar1,myVar2: n_bins_x, x_low, x_high, y_low, y_high, x_title, y_title, ROOT_color 
                        myVar3,myVar2: n_bins_x, x_low, x_high, y_low, y_high, x_title, y_title, ROOT_color 
                   overlay: regions - OPTIONAL. With this option the user can specifiy how to display overlaied graphs. -

The overlay option is not strictly required and works as follows: 

Not provided.      - A plot will be made for each variable, ovelraying all valid inputs relative to the AND of the declared regions. -
overlay: regions   - A plot will be made for each variable overlaying each declared region and all available inputs. -
overlay: variables - A plot will be made overlaying all available inputs and all available variables relative to the AND of the declared regions. -

ToDo: better adjust the style of the plots. Introduce ratio plots.

"""
import os
from copy import copy

from pyrate.core.Algorithm import Algorithm

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN
from pyrate.utils import ROOT_classes as CL

import ROOT as R

R.gStyle.SetOptStat(0)


class Make1DProfilePlot(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def initialise(self, config):
        """Prepares graphs.
        If not found in the input already it will create new ones."""

        i_name = self.store.get("INPUT:name", "TRAN")

        for f_name, f_attr in config["algorithm"]["folders"].items():
            for v_name, v_attr in f_attr["variables"].items():
                for r_name in self.make_regions_list(f_attr):

                    g_name = self.get_graph_name(r_name, v_name)

                    path = ""
                    if "path" in f_attr:
                        path = f_attr["path"]

                    target_dir = config["name"].replace(",", "_").replace(":", "_")
                    path = os.path.join(target_dir, path)

                    g = self.store.copy("INPUT:" + os.path.join(path, g_name), "TRAN")

                    obj_name = self.get_object_name(i_name, g_name)

                    if not g:
                        g = self.make_graph(g_name, v_attr, f_attr)

                    self.store.put(obj_name, g, "PERM")

    def execute(self, config):
        """Fills graphs."""
        i_name = self.store.get("INPUT:name")

        for f_name, f_attr in config["algorithm"]["folders"].items():
            for v_name, v_attr in f_attr["variables"].items():
                for r_name in self.make_regions_list(f_attr):

                    g_name = self.get_graph_name(r_name, v_name)
                    obj_name = self.get_object_name(i_name, g_name)

                    obj_counter = ":".join([obj_name, "counter"])

                    if not self.store.check(obj_counter):

                        region = {"r_weight": 1, "weights": {}}

                        for sr_name in r_name.split("_"):

                            if sr_name == "NOSEL":
                                continue

                            subregion = self.store.get(sr_name)

                            region["r_weight"] *= subregion["is_passed"]

                            if not region["r_weight"]:
                                break

                            else:
                                for w_name, w_value in subregion["weights"].items():
                                    if not w_name in region["weights"]:

                                        region["weights"][w_name] = w_value

                                        region["r_weight"] *= w_value

                        if region["r_weight"]:

                            v_x_name, v_y_name = v_name.replace(" ", "").split(",")

                            x_variable = self.store.get(v_x_name)
                            y_variable = self.store.get(v_y_name)

                            self.store.get(obj_name, "PERM").Fill(
                                x_variable, y_variable, region["r_weight"]
                            )

                            self.store.put(obj_counter, "done")

    def finalise(self, config):
        """Makes the plot."""

        plot_collection = {}

        inputs = ST.get_items(config["name"].split(":", -1)[-1])

        for f_name, f_attr in config["algorithm"]["folders"].items():
            for v_name, v_attr in f_attr["variables"].items():
                for r_name in self.make_regions_list(f_attr):

                    g_name = self.get_graph_name(r_name, v_name)

                    for i_name in inputs:
                        obj_name = self.get_object_name(i_name, g_name)

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

                for mode, g_list in m_dict.items():
                    for obj_name in g_list:

                        g = self.store.get(obj_name, "PERM")

                        l.AddEntry(g, obj_name, "pl")

                        g.Draw("same")

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
            "n_bins_x": int(a[0]),
            "x_low": float(a[1]),
            "x_high": float(a[2]),
            "y_low": float(a[3]),
            "y_high": float(a[4]),
            "x_label": a[5],
            "y_label": a[6],
            "color": None,
            "legend_entry": None,
        }

        if len(a) >= 8:
            d["color"] = a[7]

        if len(a) >= 9:
            d["legend_entry"] = a[9]

        return d

    def get_graph_name(self, region, variable):
        """Builds graph name."""
        variable = variable.replace(",", "_").replace(" ", "")
        return f"graph_{region}_{variable}"

    def get_object_name(self, input_name, graph):
        """Builds object name, which is how graphs are identified on the PERM store."""
        return f"{input_name}:{graph}"

    def get_ROOT_colors(self, my_color):
        """Get ROOT color.
        https://root-forum.cern.ch/t/how-to-form-a-color-t-from-a-tcolor/25013
        The following ways have been tried but are problematic:
        # color = CL.Color(my_color["R"], my_color["G"], my_color["B"], f"{my_color['R'], my_color['G'], my_color['B']}")
        # setattr(R, color.name, color)

        # _c = R.TColor()
        # color = _c.GetColor(my_color["R"], my_color["G"], my_color["B"])
        """
        return CL.ColorFinder(my_color["R"], my_color["G"], my_color["B"]).match()

    def make_regions_list(self, folder):
        """Build list of selection regions considered for graph filling."""

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

    def make_graph(self, g_name, variable, folder):
        """Make graphs."""

        var = self.get_var_dict(variable)

        g = copy(
            R.TProfile(
                g_name,
                g_name,
                var["n_bins_x"],
                var["x_low"],
                var["x_high"],
                var["y_low"],
                var["y_high"],
            )
        )

        g.GetXaxis().SetTitle(var["x_label"])
        g.GetYaxis().SetTitle(var["y_label"])

        color_list = []

        if "color" in self.store.get("INPUT:config"):
            color_list.append(FN.get_color(self.store.get("INPUT:config")["color"]))

        if "overlay" in folder:

            if folder["overlay"] == "variables":

                if var["color"]:
                    color_list.append(FN.get_color(var["color"]))

            elif folder["overlay"] == "inputs":
                pass

            elif folder["overlay"] == "regions":

                for idx, r_name in enumerate(self.make_regions_list(folder)):
                    if r_name in g_name:

                        pixels = ["R", "G", "B"]

                        primary = pixels[idx % 3]
                        others = [p for p in pixels if p != primary]

                        color_list.append(
                            {primary: 0.7, others[0]: 0.0, others[1]: 0.0}
                        )

        color = FN.add_colors(color_list)
        ROOT_color = self.get_ROOT_colors(color)

        g.SetLineColor(ROOT_color)
        g.SetMarkerColor(ROOT_color)
        # g.SetFillColor(ROOT_color)

        return g

    def make_plots_dict(self, plots, obj_name, path, folder):
        """Assign graph content of plots."""

        i_name, g_name = obj_name.split(":")

        c_name = g_name.replace("graph", "profile_1d")

        mode = "overlay"

        if "overlay" in folder:

            if folder["overlay"] == "regions":
                c_name = "profile_1d_" + g_name.rsplit("_", 1)[-1]

            elif folder["overlay"] == "variables":
                c_name = g_name.rsplit("_", 1)[0].replace("graph", "profile_1d")

            elif folder["overlay"] == "inputs" or folder["overlay"] == i_name:
                pass

        if not path in plots:
            plots[path] = {}

        if not c_name in plots[path]:
            plots[path].update({c_name: {}})

        if not mode in plots[path][c_name]:
            plots[path][c_name].update({mode: [obj_name]})

        if not obj_name in plots[path][c_name][mode]:
            plots[path][c_name][mode].append(obj_name)


# EOF
