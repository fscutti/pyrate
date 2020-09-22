""" one-dimensional ROOT plot """

from pyrate.core.Algorithm import Algorithm


class Make2DPlot(Algorithm):
    __slots__ = ()

    def __init__(self, name, store):
        super().__init__(name, store)

    def execute(self, config):
        print("This is the MakePlot 2D algorithm")
