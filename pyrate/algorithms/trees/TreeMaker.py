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

import os
import ROOT as R
from array import array

from pyrate.core.Algorithm import Algorithm

from pyrate.utils import strings as ST

_T = {"float": {"python": "f", "root": "F"}, "int": {"python": "i", "root": "I"}}


class TreeMaker(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def initialise(self, config):
        """Defines a tree dictionary."""

        tree_dict = {}

        for tree in config["trees"]:
            for t_path_name, t_variables in tree.items():

                t_path = os.path.dirname(t_path_name)
                t_name = os.path.basename(t_path_name)

                if not t_path in tree_dict:
                    tree_dict[t_path] = {}

                tree_dict[t_path].update({t_name: {"instance": None, "branches": {}}})

                tree_dict[t_path][t_name]["instance"] = R.TTree(t_name, t_path_name)

                if "numbers" in t_variables:
                    for v_type, v_list in t_variables["numbers"].items():

                        for v_name in ST.get_items(v_list):

                            b = array(_T[v_type]["python"], [0])

                            tree_dict[t_path][t_name]["branches"][v_name] = b

                            tree_dict[t_path][t_name]["instance"].Branch(
                                v_name, b, f"{v_name}/{_T[v_type]['root']}"
                            )

                if "vectors" in t_variables:
                    for v_type, v_list in t_variables["vectors"].items():

                        for v_name in ST.get_items(v_list):

                            b = R.vector(v_type)()

                            tree_dict[t_path][t_name]["branches"][v_name] = b

                            tree_dict[t_path][t_name]["instance"].Branch(
                                v_name, b, f"{v_name}/{_T[v_type]['root']}"
                            )

        self.store.put("tree_dict:" + config["name"], tree_dict, "PERM")

    def execute(self, config):
        """Fills in the ROOT tree dictionary with event data."""

        tree_dict = self.store.get("tree_dict:" + config["name"], "PERM")

        vectors = []

        for t_path in tree_dict:
            for t_name in tree_dict[t_path]:

                for b_name in tree_dict[t_path][t_name]["branches"]:

                    v_value = self.store.get(b_name)

                    if type(v_value).__name__ in ["list", "tuple"]:

                        for v in v_value:
                            tree_dict[t_path][t_name]["branches"][b_name].push_back(v)

                            vectors.append(
                                tree_dict[t_path][t_name]["branches"][b_name]
                            )
                    else:
                        tree_dict[t_path][t_name]["branches"][b_name][0] = v_value

                tree_dict[t_path][t_name]["instance"].Fill()

        self.store.put("tree_dict:" + config["name"], tree_dict, "PERM")

        for v_instance in vectors:
            v_instance.clear()

    def finalise(self, config):
        """Flattens out the tree dictionary object in order to write it on the store."""

        tree_dict = self.store.get("tree_dict:" + config["name"], "PERM")
        tree_dict_flat = {}

        for t_path in tree_dict:
            tree_dict_flat[t_path] = []

            for t_name in tree_dict[t_path]:
                tree_dict_flat[t_path].append(tree_dict[t_path][t_name]["instance"])

        self.store.put(config["name"], tree_dict_flat, "PERM")


# EOF
