""" .
"""
import os
import sys
from copy import copy

import numpy as np
from scipy import stats

from pyrate.core.Algorithm import Algorithm

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN

import ROOT as R


class Make1DGraph(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def initialise(self, config):
        """Creates data structures."""

        i_name = self.store.get("INPUT:name", "TRAN")
        for region, var_type in config["algorithm"]["regions"].items():
            for v_type, variable in var_type.items():
                for v_name, v_attr in variable.items():

                    a_name = self.get_array_name(region, v_name)
                    g_name = self.get_graph_name(a_name)

                    obj_a_name = self.get_object_name(i_name, a_name)
                    obj_g_name = self.get_object_name(i_name, g_name)

                    g_attr = ST.get_items(v_attr)

                    n_bins, x_low, x_high, y_low, y_high = (
                        int(g_attr[0]),
                        float(g_attr[1]),
                        float(g_attr[2]),
                        float(g_attr[3]),
                        float(g_attr[4]),
                    )

                    # ----------------------
                    # prepare data structure
                    # ----------------------
                    a = {}

                    a["y_entries"] = [[] for i in range(n_bins + 1)]
                    a["x_axis"] = np.linspace(x_low, x_high, num=n_bins + 1)

                    # ----------------------
                    # prepare graph
                    # ----------------------
                    g = self.prepare_graph(obj_g_name, g_attr)

                    self.store.put(obj_a_name, a, "PERM")
                    self.store.put(obj_g_name, g, "PERM")

    def execute(self, config):
        """Fills data structures."""

        i_name = self.store.get("INPUT:name")

        for region, var_type in config["algorithm"]["regions"].items():
            for v_type, variable in var_type.items():
                for v_name, v_attr in variable.items():

                    a_name = self.get_array_name(region, v_name)

                    obj_a_name = self.get_object_name(i_name, a_name)

                    obj_counter = ":".join([obj_a_name, "counter"])

                    if not self.store.check(obj_counter):

                        weight = self.store.get(region)

                        if weight:

                            x_name, y_name = v_name.replace(" ", "").split(",")

                            x_var = self.store.get(x_name)
                            y_var = self.store.get(y_name)

                            # modify data structure event-by-event
                            a = self.store.get(obj_a_name, "PERM")

                            bin_idx = np.digitize(x_var, a["x_axis"])

                            # print(f"{x_var} within {a['x_axis'][bin_idx-1]} and {a['x_axis'][bin_idx]}")

                            a["y_entries"][bin_idx - 1].append(y_var)

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
                for v_name, v_attr in variable.items():

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
                                "canvas": R.TCanvas(p_name, "", 900, 800),
                                "graphs": [],
                            }

                        a_name = self.get_array_name(r_name, v_name)
                        obj_a_name = self.get_object_name(i_name, a_name)

                        g_name = self.get_graph_name(a_name)
                        obj_g_name = self.get_object_name(i_name, g_name)

                        a = self.store.get(obj_a_name, "PERM")
                        g = self.store.get(obj_g_name, "PERM")

                        self.fill_graph(g, a)

                        gather_in_inputs = r_name in p_name and v_name in p_name
                        gather_in_variables = (
                            i_name in p_name and r_name in p_name and v_type in p_name
                        )
                        gather_in_regions = i_name in p_name and v_name in p_name

                        if gather_in_inputs or gather_in_variables or gather_in_regions:
                            p_collection[p_entry]["graphs"].append(g)

        plots = {}
        for p_entry, p_dict in p_collection.items():

            p_dict["canvas"].cd()

            p_dict["canvas"].SetTickx()
            p_dict["canvas"].SetTicky()

            p_dict["canvas"].SetGridx()
            p_dict["canvas"].SetGridy()

            """
            if not "makeoverlay" in config["algorithm"]:

                p_name = p_dict["canvas"].GetName()

                h_stack = copy(R.THStack(p_name, p_name))

                for h in p_dict["graphs"]:
                    h_stack.Add(h)
                h_stack.Draw()

            #else:
            """

            for idx, g in enumerate(p_dict["graphs"]):

                if idx == 0:
                    g.Draw("aC*4")
                else:
                    g.Draw("4C*p,same")

            p_dict["canvas"].BuildLegend(0.1, 0.8, 0.9, 0.9)

            plots[p_entry] = p_dict["canvas"].Clone()

            p_dict["canvas"].Close()

        self.store.put(config["name"], plots, "PERM")

    def prepare_graph(self, g_name, g_attributes):

        g = copy(R.TGraphErrors(R.Int_t(g_attributes[0])))

        g.SetName(g_name)
        g.SetTitle("")

        x_title = g_name + "_x"
        y_title = g_name + "_y"

        g.SetLineWidth(3)

        if "color" in self.store.get("INPUT:config") or len(g_attributes) < 6:
            g.SetLineColor(
                self.get_ROOT_colors(self.store.get("INPUT:config")["color"])
            )
            g.SetFillColor(
                self.get_ROOT_colors(self.store.get("INPUT:config")["color"])
            )

        elif len(g_attributes) >= 6:
            g.SetLineColor(self.get_ROOT_colors(g_attributes[5]))
            g.SetFillColor(self.get_ROOT_colors(g_attributes[5]))

        if "linestyle" in self.store.get("INPUT:config"):
            g.SetLineStyle(self.store.get("INPUT:config")["linestyle"])

        if "fillstyle" in self.store.get("INPUT:config"):
            g.SetFillStyle(self.store.get("INPUT:config")["fillstyle"])

        if len(g_attributes) >= 8:
            x_title = g_attributes[6]
            y_title = g_attributes[7]

        g.GetXaxis().SetLimits(float(g_attributes[1]), float(g_attributes[2]))
        g.GetYaxis().SetLimits(float(g_attributes[3]), float(g_attributes[4]))

        g.GetXaxis().SetTitle(x_title)
        g.GetYaxis().SetTitle(y_title)

        return g

    def fill_graph(self, graph, array):

        n_points = len(array["x_axis"]) - 1

        # graph.SetPointX(0, graph.GetXaxis().GetXmin())
        # graph.SetPointY(0, graph.GetYaxis().GetXmin())
        # graph.SetPointError(0, 0, 0)

        for i in range(n_points):

            x_low, x_high = array["x_axis"][i : i + 2]

            x_value = np.mean([x_low, x_high])
            x_err = (x_high - x_low) / 2.0

            if array["y_entries"][i]:
                y = np.array(array["y_entries"][i])

                y_value = np.mean(y)
                y_err = np.std(y)

            else:
                y_value = 0.0
                y_err = 0.0

            graph.SetPointX(i, x_value)
            graph.SetPointY(i, y_value)
            graph.SetPointError(i, x_err, y_err)

        # graph.SetPointX(n_points + 1, graph.GetXaxis().GetXmax())
        # graph.SetPointY(n_points + 1, graph.GetYaxis().GetXmax())
        # graph.SetPointError(n_points, 0, 0)

    def get_graph_name(self, array_name):
        """Builds histogram name."""
        return array_name.replace("array", "graph")

    def get_array_name(self, region, variables):
        """Builds histogram name."""
        variables = variables.replace(",", "_vs_").replace(" ", "")
        return f"array_{region}_{variables}"

    def get_object_name(self, iname, histogram):
        """Builds object name, which is how histograms are identified on the PERM store."""
        return f"{iname}:{histogram}"

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


# EOF
