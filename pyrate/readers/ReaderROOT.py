""" Reader of a ROOT file.
"""
import ROOT as R

from pyrate.core.Reader import Reader


class ReaderROOT(Reader):
    __slots__ = ["f", "_trees"]

    def __init__(self, name, store, logger, f):
        super().__init__(name, store, logger)
        self.f = f

    def load(self):
        self.f = R.TFile.Open(self.f)
        self._idx = 0
        self._trees = {}
        # self._is_loaded = True
        # self.get_n_events()

    def read(self, name):

        if "EVENT:" in name:
            path = name.rsplit(":", 2)

            variable = path[-1]
            tree = path[-2]
            folders = path[0].partition(":")[-1].replace(":", "/")
            if folders:
                folders += "/"
            tree_path = folders + tree

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

            self._read_variable(self._trees[tree_path]["tree"], variable)

        elif "INPUT:" in name:
            # if "PMT1_charge_waveform_" in name:
            #    self._read_hist(name)
            pass

    def next_event(self):
        """If the next event reading will not be valid it outputs -1."""

        if self._idx < self._n_events - 1:
            self._idx += 1
            # self._tree.GetEntry(self._idx)
            return self._idx
        else:
            return -1

    def get_idx(self):
        if self._idx:
            return self._idx
        else:
            self.logger.error(
                f"event index required but tree has not been loaded for {self.name} reading file {self.f}!"
            )

    def get_n_events(self):
        if self._n_events:
            return self._n_events
        else:
            # assert self._tree, "ERROR: tree not loaded for reader {}".format(self.name)
            # self._n_events = self._tree.GetEntries()
            pass

    def _read_hist(self, name):
        """Grabs histograms from the input file and puts them on the permanent store."""

        h = self.f.Get(name)

        if h:
            if not self.store.check(name, "PERM"):
                self.store.put(name, h, "PERM")
            else:
                self.store.get(name, "PERM").Add(h)

    def _read_variable(self, tree, name):
        """Reads a varable from a tree and puts it on the transient store."""

        self.store.put(name, getattr(tree, name), "TRAN")


# EOF
