""" Reader of a ROOT file.
"""
import ROOT as R

from pyrate.core.Reader import Reader


class ReaderROOT(Reader):
    __slots__ = ["f", "structure", "_trees"]

    def __init__(self, name, store, logger, f, structure):
        super().__init__(name, store, logger)
        self.f = f
        self.structure = structure

    def load(self):
        self.f = R.TFile.Open(self.f)
        self._idx = 0
        self._trees = {}

    def read(self, name):
        if name.startswith("EVENT:"):

            if "GROUP:" in name:
                k, n = 3, 2
            else:
                k, n = 1, 2

            # To do: try to use a list here
            path, (
                tree,
                variable,
            ) = self._break_path(name, k, n)

            tree_path = path + tree

            # ------------------------------------------
            # Update the status of the trees.
            # ------------------------------------------
            try:
                if self._trees[tree_path]["idx"] != self._idx:
                    self._trees[tree_path]["idx"] = self._idx
                    self._trees[tree_path]["tree"].GetEntry(self._idx)

            except KeyError:
                self._trees[tree_path] = {
                    "idx": self._idx,
                    "tree": self.f.Get(tree_path),
                }
                self._trees[tree_path]["tree"].GetEntry(self._idx)

            self._read_variable(name, self._trees[tree_path]["tree"], variable)

        elif name.startswith("INPUT:"):
            # To do: break name appropriately to retrieve histogram in the right path.
            self._read_hist(name) 

    def set_n_events(self):
        """Reads number of events in the main tree of the file."""
        if not self._n_events:
            self._n_events = self.f.Get(self.structure["tree"]).GetEntries()

    def set_next_event(self):
        """If the next event reading will not be valid it outputs -1."""

        if self._idx < self._n_events - 1:
            self._idx += 1
        else:
            self._idx = -1
        return self._idx

    def _read_hist(self, name):
        """Grabs histograms from the input file and puts them on the permanent store."""
        
        # if not object will be retrieved the histogram will be None.
        self.store.put(name, None, "PERM")

        h = self.f.Get(name)

        if h:
            if not self.store.get(name, "PERM"):
                self.store.put(name, h, "PERM", replace=True)
            else:
                self.store.get(name, "PERM").Add(h)

    def _read_variable(self, name, tree, variable):
        """Reads a varable from a tree and puts it on the transient store."""
        self.store.put(name, getattr(tree, variable), "TRAN")

    def _break_path(self, name, k, n):
        """Breaks a given path excluding the INPUT/EVENT/:/GROUP prefix
        using the k index. NB: Always retrieve elements of tuple
        as (1, 2, ..., n,)."""

        t = name.split(":")

        return "".join([f + "/" for f in t[k : len(t) - n]]), tuple(t[-n:])


# EOF
