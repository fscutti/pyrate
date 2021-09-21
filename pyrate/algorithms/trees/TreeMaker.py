""" Creates and fills a ROOT TTree.
https://root.cern.ch/doc/master/classTTree.html


myTreeObject:
       algorithm:
           name: TreeMaker
       trees:
         - my/folder/path/myTreeName:
               numbers:
                   int: myIntBranch1, myIntBranch2, ...
                   float: myFloatBranch1, myFloatBranch2, ...
               vectors:
                   int: myIntVectorBranch1, myIntVectorBranch2, ...
                   float: myFloatVectorBranch1, myFloatVectorBranch2, ...
         - my/folder/path/myOtherTreeName:
               etc ...
"""

#import psutil

import os
import sys
import ROOT as R
from array import array
from ctypes import c_longlong

from pyrate.core.Algorithm import Algorithm

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN


GB = 1e9
MB = 1e6

_T = {"float": {"python": "d", "root": "D"}, "int": {"python": "i", "root": "I"}}


class TreeMaker(Algorithm):
    # __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)
        self.tree_dict = None
        self.out_file = None

    def initialise(self, config):
        """Defines a tree dictionary."""

        out_file = self.store.get(f"OUTPUT:{config['name']}", "PERM")

        tree_dict = {}

        for tree in config["trees"]:
            for t_path_name, t_variables in tree.items():

                t_path = os.path.dirname(t_path_name)
                t_name = os.path.basename(t_path_name)

                if not t_path in tree_dict:
                    tree_dict[t_path] = {}

                tree_dict[t_path].update({t_name: {"instance": None, "branches": {}}})

                tree_dict[t_path][t_name]["instance"] = R.TTree(t_name, t_path_name)

                tree_dict[t_path][t_name]["instance"].SetMaxTreeSize((int(1 * MB)))

                if "numbers" in t_variables:
                    for v_type, v_list in t_variables["numbers"].items():

                        for v_name in ST.get_items(v_list):

                            b = array(_T[v_type]["python"], [0])

                            tree_dict[t_path][t_name]["branches"][v_name] = b

                            b_instance = tree_dict[t_path][t_name]["instance"].Branch(
                                v_name, b, f"{v_name}/{_T[v_type]['root']}"
                            )

                            b_instance.SetFile(out_file)

                if "vectors" in t_variables:
                    for v_type, v_list in t_variables["vectors"].items():

                        for v_name in ST.get_items(v_list):

                            if v_type == "float":
                                v_type = "double"

                            b = R.vector(v_type)()

                            tree_dict[t_path][t_name]["branches"][v_name] = b

                            b_instance = tree_dict[t_path][t_name]["instance"].Branch(
                                v_name, b
                            )

                            b_instance.SetFile(out_file)

        self.store.put("tree_dict:" + config["name"], tree_dict, "PERM")

    def execute(self, config):
        """Fills in the ROOT tree dictionary with event data."""

        event_idx = self.store.get("EVENT:idx")

        tree_dict = self.store.get("tree_dict:" + config["name"], "PERM")

        vectors = []

        for t_path in tree_dict:
            for t_name in tree_dict[t_path]:

                for b_name in tree_dict[t_path][t_name]["branches"]:

                    v_value = self.store.get(b_name)

                    if type(v_value).__name__ in ["list", "tuple"]:

                        # use assign here ...
                        for v in v_value:
                            tree_dict[t_path][t_name]["branches"][b_name].push_back(v)

                            vectors.append(
                                tree_dict[t_path][t_name]["branches"][b_name]
                            )

                    elif type(v_value).__name__ == "ndarray":
                        tree_dict[t_path][t_name]["branches"][b_name].assign(v_value)

                    else:
                        tree_dict[t_path][t_name]["branches"][b_name][0] = v_value

                tree_dict[t_path][t_name]["instance"].Fill()

                """ 
                if event_idx % 5000 == 0:

                    print()

                    load1, load5, load15 = psutil.getloadavg()
                    cpu_usage = (load15/os.cpu_count()) * 100
                    print("The CPU usage is : ", cpu_usage)
 
                    print('RAM memory used:', )
                    FN.pretty(dict(psutil.virtual_memory()._asdict()))
  
                    tree_size = tree_dict[t_path][t_name]["instance"].GetTotBytes() / MB
                    print(f"The size of tree {t_name} is {tree_size} MB")
                    print()
                """

        for v_instance in vectors:
            v_instance.clear()

        i_name = self.store.get("INPUT:name")
        e_max = self.store.get("INPUT:config")["eslices"]["emax"]

        if event_idx == e_max:
            self.store.put(config["name"], config["name"], "WRITTEN")
            #self.store.get(f"OUTPUT:{config['name']}", "PERM").Close()


# EOF
