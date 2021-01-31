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
        """."""
        i_name = self.store.get("INPUT:name", "TRAN")

        for f_name, f_attr in config["algorithm"]["folders"].items():
            for r_name in self.get_regions_list(f_attr):
                for v_name, v_attr in f_attr["variables"].items():

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
            for r_name in self.get_regions_list(f_attr):
                for v_name, v_attr in f_attr["variables"].items():

                    h_name = self.get_hist_name(r_name, v_name)
                    obj_name = self.get_object_name(i_name, h_name)

                    obj_counter = ":".join([obj_name, "counter"])

                    if not self.store.check(obj_counter):
                        
                        weight = 1

                        for sr_name in r_name.split("_"):
                            weight *= self.store.get(r_name)

                            if weight == 0: 
                                break
                            
                        if weight:
                            variable = self.store.get(v_name)
                            self.store.get(obj_name, "PERM").Fill(variable, weight)
                        
                            self.store.put(obj_counter, "done")

    def finalise(self, config):
        """Makes the plot."""

        if "gather" in config["algorithm"]:
            gather = config["algorithm"]["gather"]
        else:
            gather = False

        p_collection = {}

        inputs = ST.get_items(config["name"].split(":", -1)[-1])

        for r_name, var_type in config["algorithm"]["regions"].items():

            for v_type, variable in var_type.items():
                for v_name, v_specs in variable.items():

                    for i_name in inputs:

                        path, p_name = (
                            f"{config['name']}",
                            f"plot_{i_name}_{r_name}_{v_name}",
                        )

                        path = path.replace(":", "_").replace(",", "_")

                        if gather == "inputs":
                            path += f"/regions/{r_name}/{v_type}"
                            p_name = f"plot_{r_name}_{v_name}"

                        elif gather == "variables":
                            path += f"/inputs/{i_name}/regions/{r_name}/{v_type}"
                            p_name = f"plot_{i_name}_{r_name}_{v_type}"

                        elif gather == "regions":
                            path += f"/inputs/{i_name}/{v_type}"
                            p_name = f"plot_{i_name}_{v_name}"

                        p_entry = os.path.join(path, p_name)

                        if not p_entry in p_collection:
                            p_collection[p_entry] = {
                                "canvas": R.TCanvas(p_name, p_name, 900, 800),
                                "histograms": [],
                            }

                        h_name = self.get_hist_name(r_name, v_name)
                        obj_name = self.get_object_name(i_name, h_name)

                        h = self.store.get(obj_name, "PERM")

                        gather_in_inputs = r_name in p_name and v_name in p_name
                        gather_in_variables = (
                            i_name in p_name and r_name in p_name and v_type in p_name
                        )
                        gather_in_regions = i_name in p_name and v_name in p_name

                        if gather_in_inputs or gather_in_variables or gather_in_regions:
                            p_collection[p_entry]["histograms"].append(h)

        plots = {}
        for p_entry, p_dict in p_collection.items():
            p_dict["canvas"].cd()

            if not "makeoverlay" in config["algorithm"]:

                p_name = p_dict["canvas"].GetName()

                h_stack = copy(R.THStack(p_name, p_name))

                for h in p_dict["histograms"]:
                    h_stack.Add(h)
                h_stack.Draw()

            else:
                for h in p_dict["histograms"]:
                    h.Draw("same, hist")

            plots[p_entry] = p_dict["canvas"].Clone()

            p_dict["canvas"].Close()

        self.store.put(config["name"], plots, "PERM")

    def get_regions_list(self, folder):

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

        a = ST.get_items(variable)

        h = copy(R.TH1F(h_name, h_name, int(a[0]), float(a[1]), float(a[2])))

        h.GetXaxis().SetTitle(a[3])
        h.GetYaxis().SetTitle(a[4])

        color = None

        if "overlay" in folder:

            if folder["overlay"] == "regions":

                for idx, r_name in enumerate(self.get_regions_list(folder)):
                    if r_name in h_name:

                        if len(a) > 5:
                            color = self.get_ROOT_colors("+".join([a[5], str(idx)]))

            elif folder["overlay"] == "inputs":

                if "color" in self.store.get("INPUT:config"):
                    color = self.get_ROOT_colors(
                        self.store.get("INPUT:config")["color"]
                    )

            elif folder["overlay"] == "variables":

                if len(a) > 5:
                    color = self.get_ROOT_colors(a[5])

        if color:
            h.SetLineColor(color)
            h.SetMarkerColor(color)

        return h


# EOF
