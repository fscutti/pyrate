""" Simple TGraphMaker for pyrate
    Makes a single TGraph or a TMultiGraph depending on the number of 
    Y values inserted. Optionally allows the creation of a TCanvas with the same
    information as the TGraph

    Required inputs:
        y: (str/list of objects) Array-like object(s) to be plotted in the TGraph
    
    Optional inputs:
        x: (str/) Array-like object For all Y's to be plotted against
    
    Optional parameters:
        path: (str) Default = "". The folder name/structure to store the TGraph
        x_step: (int/float) Default=1. If x is not provided and x_step is, 
                X will be defined as an array of length len(Y) with step size
                equal to x_step
        colour: (list of str/list of lists) Default = SABRE colours: 
                List of colours to be used in the plotting
                Supports lists of hex strings, or list of RGB lists
                If the list of colours is shorter than the list of Ys, then the colours
                will be cycled over
        canvas: (bool) Default = False. If canvas is True, will create a canvas
                object of the the name "<TGraphName>.canvas" with the TGraph(s)
                plotted on the canvas
    
    Example configs:
    
    ExampleTGraph:
        algorithm: TGraphMaker
        input:
            y: AverageWaveform_CH0
    
    AverageWaveforms:
        algorithm: TGraphMaker
        canvas: True
        colour: ["#ffffff", "#0000FF"]
        input:
            y: [AverageWaveform_CH0, AverageWaveform_CH1]

"""

import sys
import numpy as np

import ROOT

from pyrate.core.Algorithm import Algorithm

import pyrate.utils.strings as ST
from pyrate.utils import ROOT_utils
from pyrate.utils import enums

class TGraphMaker(Algorithm):
    __slots__ = ("file", "colour", "canvas", "graph")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)
    
    @property
    def input(self):
        """ Getter method for input objects
        """
        if self._input == {}:
            return {None: ""}
        return self._input

    @input.setter
    def input(self, inputs):
        """Setter method for input objects."""
        if hasattr(self, "_input"):
            # input has already been set
            return

        self._input = {None: set()}
        for input in inputs.values():
            for dependency in ST.pyrate_yaml_to_list(input):
                self._input[None].add(dependency)

    def initialise(self, condition=None):
        """ Initialise the TGraph information
        """
        self.file = self.store.get(f"OUTPUT:{self.name}")
        obj_name = self.name.split(":")[0]
        if "input" not in self.config:
            sys.exit(f"ERROR: TGraph object '{obj_name}', missing inputs")
        if "y" not in self.config["input"]:
            sys.exit(f"ERROR: TGraph object '{obj_name}' missing y information")
        
        if "colour" in self.config:
            self.colour = ST.pyrate_yaml_to_list(self.config["colour"])
        else:
            # Default SABRE colours
            self.colour = ["#000000", "#005378", "#f0746e", "#ccb90e", "#9af2d3", 
                           "#dc3977", "#089099", "#7c1d6f", "#90e267", "#ff9e00",
                           "#a6deff", "#cf99ea", "#01c785", "#66032c", "#ccff00",
                           "#ff7da7", "#1c94ea", "#00b000", "#e9002d"]
        self.colour = [ROOT_utils.get_ROOT_colors(c) for c in self.colour]

        self.canvas = None
        if "canvas" in self.config:
            self.canvas = bool(self.config["canvas"])

    def finalise(self, condition=None):
        """ Makes and fills the TGrahp
        """
        name = self.name.replace(':', '.')

        Ys = ST.pyrate_yaml_to_list(self.config["input"]["y"])

        if self.canvas:
            self.canvas = ROOT.TCanvas(f"{name}.canvas", name, 600, 400)
            self.canvas.SetTickx()
            self.canvas.SetTicky()
            self.canvas.cd()

        if len(Ys) > 1:
            self.graph = ROOT.TMultiGraph()

        for i, var_name in enumerate(Ys):
            Y = self.store.get(var_name)
            if type(Y) != np.ndarray:
                Y = np.array(Y)

            if "x" in self.config["input"]:
                X = self.store.get(self.config["input"]["x"])
            elif "x_step" in self.config:
                step = float(self.config["x_step"])
                X = np.arange(0, len(Y), step)
            else:
                X = np.arange(0, len(Y), 1) # Default with step of 1

            if len(Y) != len(X):
                sys.exit(f"ERROR: in TGraphMaker object {name}, lengths of x and y ({var_name}) do not match")
            X = X.astype(Y.dtype) # Crucial to convert X to the same type as Y

            if len(Ys) == 1:
                self.graph = ROOT.TGraph(len(Y), X, Y)
                self.graph.SetTitle(var_name)
                self.graph.SetName(name)
                self.graph.SetLineColor(self.colour[i%len(self.colour)])
            elif Y is not enums.Pyrate.NONE and len(Y) > 0:
                tgraph = ROOT.TGraph(len(Y), X, Y)
                tgraph.SetTitle(var_name)
                tgraph.SetLineColor(self.colour[i%len(self.colour)])
                self.graph.Add(tgraph)
                self.graph.SetName(name)

        path = ""
        if "path" in self.config:
            path = self.config["path"]

        if self.canvas:
            self.graph.Draw("AL")
            self.canvas.Modified()
            self.canvas.Update()
            self.canvas.BuildLegend(0.7,0.7,0.9,0.9)
            ROOT_utils.write(self.file, path, self.canvas)

        ROOT_utils.write(self.file, path, self.graph)
        del self.graph
        del self.canvas

# EOF
