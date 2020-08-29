""" Reader of a ROOT file.
"""
import ROOT as R
import numpy as np

from pyrate.utils import functions as FN

class ReaderROOT:
    __slots__ = ["f","treename","_tree","_nevents","_is_loaded","_idx","istore"]
    def __init__(self, f, treename = None, istore = None):
        self.f = f
        self.treename = treename
        self.istore = istore
        self._is_loaded = False

    def load(self):
        self.f = R.TFile.Open(self.f)
        if self.treename:
            self._tree = self.f.Get(self.treename)
            self._nevents = self._tree.GetEntries()
            self._idx = 0
            self._tree.GetEntry(self._idx)
        self._is_loaded = True
    
    def is_loaded(self):
        return self._is_loaded
    
    def is_finished(self):
        return self._idx == self._nevents - 1
    

    def get_next_event(self):
        """ If the next event reading will not be valid it outputs -1.
        """
        
        if self._idx < self._nevents - 1: 
            self._idx += 1
            self._tree.GetEntry(self._idx)
            return self._idx
        else:
            return -1


    def get_idx(self):
        if self._idx:
            return self._idx 
        else: 
            print("ERROR: tree not loaded")
    
    
    def get_n_events(self):
        if self._nevents:
            return self._nevents 
        else: 
            print("ERROR: tree not loaded")

    def get_previous_event(self):
        pass

    def get_split_event(self):
        pass

    def get_object(self, name):
        if "PMT1_charge_waveform_" in name: self._get_hist(name)
    
    def _get_hist(self, name):
         
        h = self.f.Get(name)

        if h:  
            if FN.has_key(name, self.istore): 
                self.istore[name].Add(h)
            else:
                self.istore[name] = h
   

