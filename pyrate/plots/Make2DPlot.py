""" one-dimensional ROOT plot """

from pyrate.core.Algorithm import Algorithm


class Make2DPlot(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):
        # print("This is the MakePlot 2D algorithm")
        pass
