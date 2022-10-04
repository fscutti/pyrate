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
from pyrate.utils import ROOT_classes as CL
from pyrate.utils import ROOT_utils
from pyrate.utils import enums as EN


class Make1DHistPlot(Algorithm):
    __slots__ = ["histograms", "file"]

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)
        # Always avoid the top-level 'import ROOT'.
        import ROOT
        ROOT.gStyle.SetOptStat(0)
        ROOT.gROOT.SetBatch()

        self.histograms = {}

    def parse_input(self, input_string):
        return {None: set(input_string.split(",")[:1])}

    def initialise(self, condition=None):
        """Prepares histograms.
        If not found in the input already it will create new ones."""

        i_name = self.store.get("INPUT:name")
        self.file = self.store.get(f"OUTPUT:{self.name}")

        for f_name, f_attr in self.config["input"]["folders"].items():
            for v_string in f_attr["variables"]:

                v_name = v_string.split(",")[0]

                for r_name in self.make_regions_list(f_attr):

                    h_name = self.get_hist_name(r_name, v_name)

                    target_dir = self.name.replace(",", "_").replace(":", "_")
                    path = os.path.join(target_dir, f_name)

                    obj_name = self.get_object_name(i_name, h_name)

                    h = self.make_hist(h_name, v_string, f_attr)

                    # self.histograms[obj_name] = h

                    self.store.save(obj_name, h)

    def execute(self, condition=None):
        """Fills histograms."""
        i_name = self.store.get("INPUT:name")

        for f_name, f_attr in self.config["input"]["folders"].items():
            for v_string in f_attr["variables"]:

                v_name = v_string.split(",")[0]

                for r_name in self.make_regions_list(f_attr):

                    h_name = self.get_hist_name(r_name, v_name)
                    obj_name = self.get_object_name(i_name, h_name)

                    # IMPORTANT: filling an histogram has to be done only once per event
                    # but multiple algorithms might want to access this object. Therefore,
                    # in every algorithm trying to fill the histogram, we might want to introduce
                    # a counter on the transient store which flags whether this action has already
                    # been performed by some other algorithm.

                    obj_counter = ":".join([obj_name, "counter"])

                    if self.store.get(obj_counter) is EN.Pyrate.NONE:

                        region = {"r_weight": 1, "weights": {}}

                        for sr_name in r_name.split("_"):

                            if sr_name == "NOSEL":
                                continue

                            subregion = self.store.get(sr_name)

                            region["r_weight"] *= subregion

                            if not region["r_weight"]:
                                # Only fill the histogram if the selection is passed
                                break

                        if region["r_weight"]:

                            variable = self.store.get(v_name)

                            if variable is not EN.Pyrate.NONE:
                                self.store.get(obj_name).Fill(variable, region["r_weight"])

    def finalise(self, condition=None):
        """Makes the plot."""
        # Always avoid the top-level 'import ROOT'.
        import ROOT

        plot_collection = {}

        inputs = ST.get_items(self.name.split(":", -1)[-1])

        for f_name, f_attr in self.config["input"]["folders"].items():
            for v_string in f_attr["variables"]:

                v_name = v_string.split(",")[0]

                for r_name in self.make_regions_list(f_attr):

                    h_name = self.get_hist_name(r_name, v_name)

                    for i_name in inputs:

                        if i_name != self.store.get("INPUT:name"):
                            continue

                        obj_name = self.get_object_name(i_name, h_name)

                        path = f_name

                        # path = os.path.join(f_attr["path"], path)

                        target_dir = self.name.replace(",", "_").replace(":", "_")
                        path = os.path.join(target_dir, path)

                        self.make_plots_dict(
                            plot_collection,
                            obj_name,
                            i_name,
                            v_name,
                            r_name,
                            path,
                            f_attr,
                        )

        # FN.pretty(plot_collection)

        canvas_collection = self.store.get(self.name)

        if canvas_collection is EN.Pyrate.NONE:
            canvas_collection = {}

        for f_path, p_dict in plot_collection.items():

            if not f_path in canvas_collection:
                canvas_collection[f_path] = []

            for p_name, m_dict in p_dict.items():

                l_name, c_name = p_name.split("|")

                l = copy(ROOT.TLegend(0.1, 0.8, 0.9, 0.9))
                l.SetHeader(l_name)

                c = copy(ROOT.TCanvas(c_name, "", 900, 800))

                c.SetTickx()
                c.SetTicky()

                c.cd()

                h_stack = None
                x_stack_label, y_stack_label = None, None
                has_already_drawn = False

                for mode, h_list in m_dict.items():
                    for obj in h_list:

                        l_entry, obj_name = obj.split("|")

                        h = self.store.get(obj_name)

                        if mode == "stack" and not h_stack:

                            h_stack = copy(
                                ROOT.THStack(
                                    "h_stack",
                                    f";{h.GetXaxis().GetTitle()};{h.GetYaxis().GetTitle()}",
                                )
                            )

                        if mode == "stack":
                            l_entry = "stack:" + l_entry

                        l.AddEntry(h, l_entry, "pl")

                        if mode == "overlay":
                            h.Draw("same")
                            has_already_drawn = True

                        elif mode == "stack":

                            x_stack_label = h.GetXaxis().GetTitle()
                            y_stack_label = h.GetYaxis().GetTitle()

                            h_stack.Add(h)

                if h_stack:
                    if not has_already_drawn:
                        h_stack.Draw()
                    else:
                        h_stack.Draw("same")

                c.Modified()
                c.Update()

                l = l.Clone()

                l.Draw()

                canvas_collection[f_path].append(c.Clone())

                # IMPORTANT: the canvas has to be closed to avoid overalps with
                # open canvases with the same name afterward. ROOT has an obscure
                # memory management. We also have to clone the original.
                # N.B.: cloning the canvas at its creation would not work as there
                # might be other ROOT objects created in the process of drawing on it.
                c.Close()

        # FN.pretty(canvas_collection)

        # the True option is just a placeholder, this algorithm might need some
        # restructuring by putting the definition of the main object in the initialise function.
        
        self.store.save(self.name, canvas_collection)
        for name, canvas in canvas_collection:
            ROOT_utils.write(self.file, name, canvas)

    def get_var_dict(self, variable):
        """Build dictionary for variable attributes."""

        a = ST.get_items(variable)

        d = {
            "n_bins": int(a[1]),
            "x_low": float(a[2]),
            "x_high": float(a[3]),
            "x_label": a[4],
            "y_label": a[5],
            "color": None,
            "legend_entry": None,
        }

        if len(a) >= 7:
            d["color"] = a[6]

        if len(a) >= 8:
            d["legend_entry"] = a[7]

        return d

    def get_hist_name(self, region, variable):
        """Builds histogram name."""
        return f"hist_{region}_{variable}"

    def get_object_name(self, input_name, histogram):
        """Builds object name, which is how histograms are identified on the PERM store."""
        return f"{input_name}:{histogram}"

    def get_ROOT_colors(self, my_color):
        """Get ROOT color."""
        return CL.ColorFinder(my_color["R"], my_color["G"], my_color["B"]).match()

    def make_regions_list(self, folder):
        """Build list of selection regions considered for histogram filling."""

        overlay_regions = self.config["overlay"] == "regions"
        regions_list = []

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
        # Always avoid the top-level 'import ROOT'.
        import ROOT

        var = self.get_var_dict(variable)

        # Why copy the following object? Because there might be already an object
        # with the same name in the ROOT object list. Another way: h.SetDirectory(0)
        h = copy(ROOT.TH1F(h_name, h_name, var["n_bins"], var["x_low"], var["x_high"]))

        h.GetXaxis().SetTitle(var["x_label"])
        h.GetYaxis().SetTitle(var["y_label"])

        color_list = []

        if "color" in self.store.get("INPUT:config"):
            color_list.append(FN.get_color(self.store.get("INPUT:config")["color"]))

        if self.config["overlay"] == "variables":

            if var["color"]:
                color_list.append(FN.get_color(var["color"]))

        elif self.config["overlay"] == "inputs":
            pass

        elif self.config["overlay"] == "regions":

            for idx, r_name in enumerate(self.make_regions_list(folder)):
                if r_name in h_name:

                    pixels = ["R", "G", "B"]

                    primary = pixels[idx % 3]
                    others = [p for p in pixels if p != primary]

                    color_list.append({primary: 0.7, others[0]: 0.0, others[1]: 0.0})

        color = FN.add_colors(color_list)
        ROOT_color = self.get_ROOT_colors(color)

        h.SetLineColor(ROOT_color)
        h.SetMarkerColor(ROOT_color)

        return h

    def make_plots_dict(self, plots, obj_name, i_name, v_name, r_name, path, folder):
        """Assign histogram content of plots."""

        c_name = obj_name.replace(f"{i_name}:hist", "plot_1d")
        l_entry = i_name
        l_name = ",".join([r_name, v_name])
        mode = "stack"

        if self.config["overlay"] == "regions":
            c_name = "plot_1d_" + v_name
            l_entry = ",".join([i_name, r_name])
            l_name = v_name
            mode = "overlay"

        elif self.config["overlay"] == "variables":
            c_name = obj_name.replace(f"{i_name}:hist", "plot_1d").replace(
                f"_{v_name}", ""
            )
            l_entry = ",".join([i_name, v_name])
            l_name = r_name
            mode = "overlay"

        elif self.config["overlay"] == "inputs" or self.config["overlay"] == i_name:
            mode = "overlay"

        c_name = "|".join([l_name, c_name])
        e_name = "|".join([l_entry, obj_name])

        if not path in plots:
            plots[path] = {}

        if not c_name in plots[path]:
            plots[path].update({c_name: {}})

        if not mode in plots[path][c_name]:
            plots[path][c_name].update({mode: [e_name]})

        if not e_name in plots[path][c_name][mode]:
            plots[path][c_name][mode].append(e_name)


# EOF
