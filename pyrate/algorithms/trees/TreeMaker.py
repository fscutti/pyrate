""" Creates and fills a ROOT TTree based on the config
https://root.cern.ch/doc/master/classTTree.html
https://root.cern/manual/trees/

    Required parameters:
        input:  Valid config of all the variables and their branch
                names sorted by the appropriate datatypes and fill-type
        
        Config requirememnts: TreeMaker uses a specialised config that maps out
            the shape and variables in the TTree. Each tree must state its
            filltype, either 'event' or 'single', which is filled either each 
            event, or once per job. Each variable must be specified as a
            'vector' or 'scalar' type, and finally the variable's data type.
            Objects can be listed as a comma separated string, and will be
            filled into the tree with the branch name the same as the 
            object name.
                e.g. 
                Tree1:
                    algorithm: TreeMaker
                    event:
                        float: Baseline_CH0, Charge_CH0, Skew_CH0
                        vector<int>: RawWaveform_CH0
            
            TreeMaker also supports custom branch names - branch names distinct
            from the object name they point to and store. To do this, instead of
            and object name, the TreeMaker must be passed a branch name and an
            object name pairing as follows: Branch_name: Object_name. 
            To use this functionality, objects must be listed in the tree with 
            yaml's list syntax (-). It also supports direct use of in-line
            dictionaries as per yaml parsing.
            The following example shows a range of possible syntaxes. Note that 
            within the list, regular comma separated string passing is still 
            possible.
                e.g.
                Tree1:
                    algorithm: TreeMaker
                    filltype: event
                    input:
                        float: 
                            - Baseline: Baseline_CH0                # Single custom branch
                            - {Charge: Charge_CH0, Skew: Skew_CH0}  # Multiple custom branches 
                            - CFDTime_CH0, Timestamp_CH0,           # Older comma separated strings still compatible
                                LeadingEdge_CH0
                        vector<float>: CorrectedWaveform: CorrectedWaveform_CH0
    
    Example config:
    
    TreeObject:
        algorithm: TreeMaker
        filltype: event
        input:
            vector<int>: RawWaveform_CH0
            vector<float>: CorrectedWaveform_CH0
            float: 
                - Baseline: Baseline_CH0
                - {Charge: Charge_CH0, Skew: Skew_CH0}
                - CFDTime_CH0, Timestamp_CH0,
                    LeadingEdge_CH0

"""

import sys
import ROOT as R
from array import array

from pyrate.core.Algorithm import Algorithm

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN
from pyrate.utils.ROOT_utils import _Type
from pyrate.utils import enums

GB = 1e9
MB = 1e6

class Branch:
    """Class to store branch information
    Name will be the name of the branch in the TTree
    var_name is an optional string to store the name of the variable on the
    store. If it exists, it will be used instead of 'name' to get the
    variable from the store.
    """

    def __init__(
        self, name, var_name=None, datatype=None, event_based=True, create_now=False
    ):
        self.name = name
        if not self.name.replace("_", "").isalnum():
            print(
                f"Warning: Branch name contains non-alphanumeric characters '{self.name}'"
            )

        # self.var_name will be name unless var_name passed in
        self.var_name = self.name if var_name is None else var_name

        if datatype == None:
            sys.exit(f"ERROR: in branch {self.name} - datatype not provided.")

        self._set_datatype(datatype)  # set the datatype and vector type
        self.event_based = event_based
        self.created = False
        self.linked = False
        if create_now:
            self.create()

    # def create(self, data, type_override=None):
    def create(self):
        # Check if what's being passed in is iterable (stored in array)
        # self.vector = FN.iterable(data)
        # Automatic type getting - WIP
        # Try to get the correct datatype
        # if self.vector:
        #     self.datatype = python_to_root_type(data, vector_type=self.vector)
        # else:
        #     self.datatype, self.nptype = python_to_root_type(data)
        if self.vector:
            self.data = R.vector(_Type[self.datatype]["vector"])()
            self.invalid_value = array(_Type[self.datatype]["python"])
        else:
            self.data = array(_Type[self.datatype]["python"], [0])
            # self.data = np.zeros(1, dtype=self.nptype)
            self.invalid_value = _Type[self.datatype]["invalid"]
        self.created = True

    def fill_branch(self, data):
        if not self.created:
            # Need to create all the branch machinery
            self.create(data)

        isiter = FN.iterable(data)
        if not isiter and self.vector == True:
            print(
                f"Error: input data is not iterable, but this branch ({self.name}) expects an array"
            )
            print(f"Input data type: {type(data)}, branch datatype: {self.datatype}")
            sys.exit(1)
        if isiter and not self.vector:
            print(
                f"Error: input data is iterable, but this branch ({self.name}) expects a single element"
            )
            print(f"Input data type: {type(data)}, branch datatype: {self.datatype}")
            sys.exit(1)
        assert isiter == self.vector
        if self.vector:
            # Clear just in case
            try:
                self.data[0]  # Test if we can access it
                self.data.clear()
            except:
                pass
            # for val in data: self.data.push_back(val) # old method
            if self.datatype == "string":
                # Special case for strings, we store a string in a string vector, where the first element contains the full string
                self.data.push_back(data)
            else:
                self.data.assign(data)
        else:
            self.data[0] = data

    def clear_vector(self):
        """Clears the vector of a branch. Only works if vector=True"""
        if not self.vector:
            return
        self.data.clear()

    def _set_datatype(self, datatype):
        """Parses the datatype, breaks up into type and
        vector mode
        """
        if datatype.startswith("vector"):
            # extract the datatype
            if datatype[-1].isalnum():
                self.datatype = datatype[7:]
            else:
                self.datatype = datatype[7:-1]
            self.vector = True
        else:
            self.datatype = datatype
            self.vector = False


class Tree:
    """Class to store tree information
    Build your Tree structure first, then call create() to make the
    TTree structure accordingly
    """

    def __init__(
        self, name, outfile, path=None, branch_list=[], event=False, create_now=True
    ):
        self.name = name
        self.outfile = outfile
        self.path = path if path != None else self.name
        self.TTree = None
        self.created = False
        self.event = event  # Type of TTree, to be updated with each event loop or not
        self.branches = {}
        if branch_list:
            for branch in branch_list:
                self.add_branch(branch)
        if create_now:
            self.create()

    def add_branch(self, branch):
        """Adds branch to the tree storage"""
        if branch.name in self.branches:
            # Uh oh, branch already in branch list
            sys.exit(
                f"Error: A branch with the name '{branch.name}' already exists in this Tree ({self.name}).\n"
                "Please rename the new incoming branch (or don't add the same branch twice?)"
            )
        self.branches[branch.name] = branch
        if self.created:
            # TTree already created, so we better link this new branch
            if branch.linked:
                # uh oh, branch already linked to a TTree
                sys.exit(f"Error: branch ({branch.name}) already linked to a TTree")
            self.link_branch(branch)

    def create(self):
        """Actually makes the trees structure in the structure and adds all the
        branches into the tree. Typically called by the detector class
        """
        # Make sure we're linked to the correct file
        self.outfile.cd()
        self.TTree = R.TTree(self.name, self.name)
        # self.TTree.SetMaxTreeSize((int(1 * MB)))
        self.created = True

    def link_all_branches(self):
        """Links all the branches. Requires that the branches all be created
        properly
        """
        for branch_name in self.branches:
            branch = self.branches[branch_name]
            if not branch.linked:
                self.link_branch(branch)

    def link_branch(self, branch):
        """Links branch to the TTree. Requires TTree to be created"""
        if not self.TTree:
            self.create()
        if branch.linked:
            sys.exit("Error: Branch already linked")
        if not branch.created:
            sys.exit(
                f"Error initialising Tree - branch '{branch.name}' hasn't been created yet. Fill it with some data or create it manually."
            )
        if branch.vector:
            branch_instance = self.TTree.Branch(
                branch.name, self.branches[branch.name].data
            )
        else:
            branch_instance = self.TTree.Branch(
                branch.name,
                self.branches[branch.name].data,
                branch.name + "/" + _Type[branch.datatype]["root"],
            )
        branch_instance.SetFile(self.outfile)
        branch.linked = True

    def fill_branch(self, branch_name, data):
        """Runs the fill branch comamnd, filling branch_name with data"""
        if branch_name not in self.branches:
            sys.exit(f"Error filling branch: '{branch_name}' not in Tree '{self.name}'")
        if not self.branches[branch_name].created:
            # Need to create the branch
            self.branches[branch_name].create(data)
        # Now we can check if the branch has been linked
        if not self.branches[branch_name].linked:
            self.link_branch(self.branches[branch_name])
        self.branches[branch_name].fill_branch(data)

    def fill(self):
        """Runs the Fill function on the TTree
        Clears the branch variables
        """
        self.TTree.Fill()
        # Now it's been filled we better clear the vectors
        for branch in self.branches:
            # Only do it if necessary
            if self.branches[branch].vector:
                self.branches[branch].clear_vector()

    def remove_branch(self, branch):
        """Removes branch to the tree storage
        Does not remove the TBranch from the TTree as this isnt possible.
        Won't be accessed anymore (hopefully)
        """
        del self.branches[branch.name]

    def set_branches(self, branch_names, status=1):
        """Sets the branch status of a list of branches"""
        for branch_name in branch_names:
            self.TTree.SetBranchStatus(branch_name, status)

    def enable_branches(self, branch_names):
        """Enables all the branches in the input list"""
        self.set_branches(branch_names, status=1)

    def disable_branches(self, branch_names):
        """Disables all the branches in the input list"""
        self.set_branches(branch_names, status=0)


class TreeMaker(Algorithm):
    __slots__ = ("file", "tree")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    @property
    def input(self):
        """Getter method for input objects."""
        if self._input == {}:
            return {None: ""}
        return self._input

    @input.setter
    def input(self, config_input):
        """Sets the input approrpriately for TreeMaker"""
        if hasattr(self, "_input"):
            # input has already been set
            return

        self._input = {}
        for dependency in FN.expand_nested_values(config_input):
            variables = set(ST.get_items(str(dependency)))
            self._update_input(None, variables)

    def initialise(self, condition=None):
        """Defines a tree dictionary."""
        out_file = self.store.get(f"OUTPUT:{self.name}")
        self.file = out_file

        name = self.name.split(":")[0]
        t_path = self.config["path"] if "path" in self.config else ""
        event_based = False if self.config["filltype"] == "single" else True

        self.tree = Tree(
            name, out_file, path=t_path, event=event_based, create_now=True
        )

        for datatype, variables in self.config["input"].items():
            # New check to handle lists of vars
            variables_list = self._parse_tree_vars(variables)
            for b_name, var_name in variables_list:
                # loop over individual variables
                new_branch = Branch(
                    b_name,
                    var_name=var_name,
                    datatype=datatype,
                    create_now=True,
                )
                # Add the new branch to the TTree
                self.tree.add_branch(new_branch)

    def execute(self, condition=None):
        """Fills in the ROOT tree dictionary with event data."""
        # Fill all the branches in the trees if they're event-based
        if self.tree.event:
            for branch_name in self.tree.branches:
                value = self.store.get(self.tree.branches[branch_name].var_name)
                # Handle invalid values using internal Pyrate.NONE
                if value is enums.Pyrate.NONE:
                    # No valid value to store, storing the closest invalid value
                    value = self.tree.branches[branch_name].invalid_value

                # Fill the branch with the value
                self.tree.branches[branch_name].fill_branch(value)

            # Save all the values into the Tree
            self.tree.fill()

            # some line like that to indicate that the writer has to
            # call write on the object.
            self.store.save(self.name, enums.Pyrate.WRITTEN)

    def finalise(self, condition=None):
        """Fill in the single/run-based variables"""
        # Fill all the branches in the trees if they're run-based
        if not self.tree.event:
            # Only want to fill the branches that are run-based
            for branch_name in self.tree.branches:
                value = self.store.get(self.tree.branches[branch_name].var_name)

                # Handle invalid values using internal Pyrate.NONE
                if value is enums.Pyrate.NONE:
                    # No valid value to store, storing the closest invalid value
                    value = self.tree.branches[branch_name].invalid_value

                # Fill the branch with the value
                self.tree.branches[branch_name].fill_branch(value)
            # Save all the values into the Tree
            self.tree.fill()

        # Write the objects to the file - this is the most important step
        self.file.Write("", R.TObject.kOverwrite)

        # Store itself on the store with SKIP_WRITE code to show we have nothing
        # to return.
        self.store.save(self.name, enums.Pyrate.WRITTEN)

    def _parse_tree_vars(self, variables):
        """Dedicated function to just parse the tree lists/dicts/strings"""
        if type(variables) == dict:
            # Just a single dictionary here
            variables = [variables]
        if type(variables) == list:
            # Dealing with a list
            retlist = []
            for entry in variables:
                if type(entry) == str:
                    var_names = list(filter(None, ST.get_items(entry)))
                    retlist += list(zip(var_names, var_names))
                elif type(entry) == list:
                    retlist += list(zip(entry, entry))
                elif type(entry) == dict:
                    retlist += list(entry.items())
                else:
                    retlist += [entry]
            return retlist
        else:
            # old style
            var_names = list(filter(None, ST.get_items(variables)))
            return list(zip(var_names, var_names))


# EOF
