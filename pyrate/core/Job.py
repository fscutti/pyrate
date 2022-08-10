""" This class will handle a set of configurations and launch several 
instances of a Run homogeneous in purpose and structure.
"""

import os
import re
import sys
import yaml
import json
import pyclbr
import logging
from copy import deepcopy

from itertools import groupby

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN
from pyrate.utils.ROOT_classes import _Type

from pyrate.core.Run import Run


class Job:
    def __init__(self, name, config, log_level):
        self.name = name
        self.config = config
        self.log_level = log_level

    def setup(self):
        """Build global Job configuration and instantiate Run objects.
        The keys of the following dictionary will be distributed to the Run.
        """

        self.job = {
            "no_progress_bar": self.config["no_progress_bar"],
            "alg_timing": self.config["alg_timing"],
            "logger": None,
            "inputs": {},
            "configs": {},
            "outputs": {},
        }

        # ----------------------------
        # Setup the logger if required
        # ----------------------------
        self.job["logger"] = logging.getLogger("pyrate")
        if self.log_level is None and self.job["alg_timing"] != True:
            logging.disable(logging.CRITICAL)
        else:
            if self.job["alg_timing"]:
                self.job["logger"].setLevel(logging.INFO)
            else:
                self.job["logger"].setLevel(getattr(logging, self.log_level))

        # --------------------------
        # Build global configuration
        # --------------------------

        for i_name, i_attr in self.config["inputs"].items():

            # This dictionary contains all input information. The file list contains lists
            # which can have more than one element in the case of multiple channels declared in the group.
            self.job["inputs"][i_name] = {"files": []}

            # Files are collected looking for tags separated by underscores. Sevaral options are available
            # to collect tags.
            # 1) any: (REQUIRED) collect a file if it contains any of these tags.
            # 2) all: collect a file if it contains all of these tags.
            # 3) gropus: if a file starts with any of the tags declared here it will be considered as part of a group.
            #
            # Files can also be added providing their full path under the 'path' field. Notice that if the 'samples' options
            # are ALSO provided, all files added in this way will be selected according to the 'tags' rules as usual.

            for f in FN.find_files(i_attr["path"], "PYRATE"):

                if "samples" in i_attr:
                    self.job["inputs"][i_name]["files"].extend(
                        f
                        for s in ST.get_items(i_attr["samples"]["tags"]["any"])
                        if s in ST.get_tags(f)
                        and FN.modus_ponens(
                            "all" in i_attr["samples"]["tags"],
                            all(
                                t in ST.get_tags(f)
                                for t in ST.get_items(
                                    i_attr["samples"]["tags"].get("all", False)
                                )
                            ),
                        )
                        and FN.modus_ponens(
                            "groups" in i_attr["samples"]["tags"],
                            any(
                                c in ST.get_tags(f)
                                for c in ST.get_items(
                                    i_attr["samples"]["tags"].get("groups", False)
                                )
                            ),
                        )
                    )

                else:
                    self.job["inputs"][i_name]["files"].append(f)

            # removing duplicates from the list of files. At this stage no groups are built yet.
            self.job["inputs"][i_name]["files"] = ST.remove_duplicates(
                self.job["inputs"][i_name]["files"]
            )

            # Group files using the first tag found in their name.
            self.job["inputs"][i_name]["files"] = [
                list(f)
                for j, f in groupby(
                    self.job["inputs"][i_name]["files"],
                    lambda a: a.partition("_")[0]
                    if FN.find("groups", i_attr)
                    else None,
                )
            ]

            if not self.job["inputs"][i_name]["files"]:
                sys.exit(
                    f"ERROR: no input files found for input {i_name} under path {i_attr['path']}"
                )

            # Add all remaining attributes.
            self.job["inputs"][i_name].update(i_attr)

        self.job["configs"]["global"] = {"objects": {}}
        tags = {}
        forbidden_tags = [f"<{t}>" for t in _Type]

        for c_name, c_attr in self.config["configs"].items():

            self.job["configs"][c_name] = {"files": []}

            for f in FN.find_files(c_attr["path"], "PYRATE"):
                self.job["configs"][c_name]["files"].extend(
                    f
                    for n in ST.get_items(c_attr["tags"]["any"])
                    if n in ST.get_tags(f)
                    and FN.modus_ponens(
                        "all" in c_attr["tags"],
                        all(
                            t in ST.get_tags(f)
                            for t in ST.get_items(c_attr["tags"].get("all", False))
                        ),
                    )
                    and f.lower().endswith(".yaml")
                )

            for f in self.job["configs"][c_name]["files"]:
                self.job["configs"][c_name].update(yaml.full_load(open(f, "r")))

            self.job["configs"]["global"]["objects"].update(
                self.job["configs"][c_name]["objects"]
            )

            for k in self.job["configs"][c_name]:
                if re.findall("<.*>", k) or re.findall("\$.*\$", k):
                    # found a tag:
                    if k in forbidden_tags:
                        sys.exit(f"ERROR: tag {k} is a forbidden tag.")
                    tags[k] = self.job["configs"][c_name][k]

        # Deal with object duplication
        # Loop through all objects and find any that need duplicating
        # For now, they must have a tag in their name, as object names must be
        # unique.
        objects_to_dup = {}
        for obj_name, obj in self.job["configs"]["global"]["objects"].items():
            for tag in tags:
                if tag in obj_name:
                    objects_to_dup[obj_name] = obj
        # clear out the found objects
        for obj_name in objects_to_dup:
            del self.job["configs"]["global"]["objects"][obj_name]

        # Duplicate the object
        for obj_name, obj in objects_to_dup.items():
            # First find all the relevant tags
            obj_str = json.dumps(obj)
            used_tags = {tag for tag in tags if tag in obj_str or tag in obj_name}

            # Categories all the tags, as we want to do different things
            tag_type = {"<>":[], "$$":[]}
            for tag in used_tags:
                tag_type["<>"] += re.findall("<.*>", tag)
                tag_type["$$"] += re.findall("\$.*\$", tag)

            # Let's do all the direct drop find/replaces now
            for tag in tag_type["$$"]:
                obj_str = obj_str.replace(f'"{tag}"', str(tags[tag]))
                obj_name = obj_name.replace(f'"{tag}"', str(tags[tag]))
            
            # Now we'll do handle the in-parallel tags
            # The name *must* be updated, if there is no tag in the name we exit
            if not any([tag in obj_name for tag in tag_type["<>"]]):
                sys.exit(f"No valid tag found in object {obj_name}. Must contain a <tag> style tag.")
            tag_list_lengths = [len(tags[tag]) for tag in used_tags]
            if not tag_list_lengths[:-1]==tag_list_lengths[1:]:
                print(f"WARNING: <tag> type lists are not equal length for object {obj_name}")
            shortest = min(tag_list_lengths)
            for i in range(shortest):
                new_name = obj_name
                new_obj = obj_str
                for tag in tag_type["<>"]:
                    new_name = new_name.replace(tag, str(tags[tag][i]))
                    new_obj = new_obj.replace(tag, str(tags[tag][i]))
                
                # Insert the new object back into the global config
                self.job["configs"]["global"]["objects"][new_name] = json.loads(new_obj)

        for o_name, o_attr in self.config["outputs"].items():

            self.job["outputs"][o_name] = {"files": None}

            o_attr["file"]["path"] = FN.find_env(o_attr["file"]["path"], "PYRATE")

            outdir = os.path.dirname(os.path.abspath(o_attr["file"]["path"]))

            if not os.path.exists(outdir):
                sys.exit("ERROR: Output directory does not exist, please create it.")

            if not os.path.isdir(outdir):
                sys.exist("ERROR: Output path is a file, not a directory.")

            self.job["outputs"][o_name]["files"] = os.path.join(
                o_attr["file"]["path"], o_name + o_attr["file"]["format"]
            )

            for target in o_attr["targets"]:
                for t_name, t_attr in target.items():

                    if t_attr == "all":
                        samples = ST.remove_duplicates(self.job["inputs"])
                    else:
                        samples = ST.get_items(target[t_name])

                    samples.sort()

                    s_names = ",".join(samples)

                target[t_name] = samples

                target[":".join([t_name, s_names])] = target.pop(t_name)

            self.job["outputs"][o_name].update(o_attr)

        # -----------------------
        # Instantiate Run object
        # -----------------------
        self.run = Run(f"{self.name}_run", self.job)

        self.run.setup()

    def launch(self):
        """Launch Run objects. """
        self.run.launch()


# EOF
