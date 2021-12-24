#!/usr/bin/env python3
# Script to take in a pyrate config and expand out all objects based on channels
# Generated script to be fed into pyrate
# Mike Mews 2021

import os
import sys
import yaml
import argparse
from copy import deepcopy

# Added in iterable and get_items to allow script to run as a standalone
def iterable(obj):
    """ Determines if an object is iterable or not
    """
    try:
        iter(obj)
    except Exception:
        return False
    else:
        return True

# Credit to Federico Scutti for the orignal form of this function
def get_items(s):
    """Gets comma-separated items in a string as a list."""
    items = []
    if not s:
        return ['']
    for i in str(s).split(","):
        if not '"' in i:
            items.append(i.replace(" ", ""))
        else:
            items.append(i.replace('"', ""))
    return items

def replace_str(obj, s, r):
    """ Alters a dictionary's keys AND values if they are equal to the search
        object 's' and replaces them with the object 'r'
        Typcial use: searches nested dictionaries for a string "chx" and
        replaces it with "ch5"
    """
    for k, v in list(obj.items()):
        if iterable(k) and s in k:
            obj[k.replace(s, r)] = obj.pop(k)
        if iterable(v) and s in v:
            obj[k] = v.replace(s, r)
        if isinstance(v, dict):
            replace_str(v, s, r)

def find_object(obj, s):
    """ Searches for a thing inside a dictionary
        Looks for any instance of the object in the key or value
        Returns the object the found value is contained in.
    """
    # if key in obj: return obj[key]
    if obj == s:
        # We found it!
        return obj

    if isinstance(obj, dict):
        # Dictionary case
        for k, v in obj.items():
            if k == s or v == s:
                # We found it in the keys!
                return obj, k
            if retval := find_object(v, s):
                return retval

    if isinstance(obj, list):
        # List case
        for i in obj:
            if i == s:
                return obj
            if retval := find_object(i, s):
                return retval
    return False

def expand_list(lst, s, r):
    """ Expands a list of items each containing a key 's' with new values
        replacing s with a channel.
    """
    ret_value = []
    for v in lst:
        if v and s in v:
            ret_value.append(v.replace(s, r))
    return ret_value

# ------------------------------------------------------------------------------
# Read in the file(s) required to be converted
# ------------------------------------------------------------------------------

parser = argparse.ArgumentParser(description="Command line options for channel maker")
parser.add_argument("-f", "--files",
                    help="List of config files",
                    nargs="+",
                    required=True)

parser.add_argument("-c", "--channels",
                    help="List of channels",
                    nargs="+",
                    required=True)

parser.add_argument("-o", "--output",
                    help="Output file",
                    nargs="+",
                    required=True)

parser.add_argument("-p", "--outpath",
                    help="Output path",
                    required=False)

args = parser.parse_args()

infiles = args.files
channels = args.channels
outfile = args.output[0]
if args.outpath:
    outfile = os.path.join(os.path.abspath(args.outpath), outfile)

# Sanity check
for f in infiles:
    if not os.path.exists(f):
        sys.exit(f"ERROR: cannot find '{f}'")

# Here we mimic the pyrate job class as required
configs = {}
configs["global"] = {"objects": {}}
for infile in infiles:
    configs[infile] = yaml.full_load(open(infile, "r"))
    for object in configs[infile]["objects"]:
        if object in configs["global"]["objects"]:
            sys.exit(f"ERROR: {object} (from {infile}) has already been defined by a previous config file.")
    configs["global"]["objects"].update(configs[infile]["objects"])

# ------------------------------------------------------------------------------
# Expand out the channel based objects
# ------------------------------------------------------------------------------

channel_keys = ["CHX", "chx", "ch_x", "Channel_X"]
channel_formats = ["CH{}", "ch{}", "ch_{}", "Channel_{}"]
channel_kf = zip(channel_keys, channel_formats)

for obj_name in list(configs["global"]["objects"].keys()):
    # Find all the objects with a channel marker in the name
    obj = configs["global"]["objects"][obj_name]
    if any([k in obj_name for k in channel_keys]):
        # Ok we want to make channel version of this object
        for channel in channels:
            # New object
            channel_obj = deepcopy(obj)
            new_name = obj_name
            for ch_k, ch_f in zip(channel_keys, channel_formats):
                # New name
                new_name = new_name.replace(ch_k, ch_f.format(channel))
                # Format the string
                replace_str(channel_obj, ch_k, ch_f.format(channel))

            configs['global']['objects'][new_name] = channel_obj
    
        # Remove the original object
        del configs["global"]["objects"][obj_name]

    # Need to search objects that aren't to be duplicated but contain things
    # that need to be duplicated
    # Special case for objects like those using the TreeMaker algorithm
    elif found := find_object(obj, "channels"):
        channel_obj = found[0]
        # Find the object containing the channels
        found_above = find_object(configs["global"]["objects"], channel_obj)
        obj_container = found_above[0]
        key = found_above[1]
        obj_channels = channel_obj["channels"]
        if type(obj_channels) == str:
            if obj_channels == "global":
                # Ok, using global channels
                obj_channels = channels
            else:
                obj_channels = get_items(obj_channels)

        # We also need to deal with the dependencies
        # And ALL the cases
        states = ["initialise", "execute", "finalise"]
        ios = ["input", "output"]
        for state in states:
            for io in ios:
                if state in obj and io in obj[state]:
                    dep_list = get_items(obj[state][io])
                    if '' in dep_list: dep_list.remove('')
                    for ch in channels:
                        for ch_k, ch_f in zip(channel_keys, channel_formats):
                            # Add in the channel equivalents
                            dep_list += expand_list(dep_list, ch_k, ch_f.format(ch))
                    # Now remove all the old keys, make sure it's unique
                    dep_list = [s for s in dep_list if not any([ch_k in s for ch_k in channel_keys])]
                    if dep_list:
                        obj[state][io] = ", ".join(dep_list)
                    else:
                        obj[state][io] = None

        for channel in obj_channels:
            # Ok, now we need to search through the entire object, find any
            # channel strings 'CHX' and replace it with the right number
            # New object
            new_channel_obj = deepcopy(channel_obj)

            new_name = obj_name
            new_key = key
            for ch_k, ch_f in zip(channel_keys, channel_formats):
                # New name
                new_name = new_name.replace(ch_k, ch_f.format(channel))
                new_key = new_key.replace(ch_k, ch_f.format(channel))
                # Format the string
                replace_str(new_channel_obj, ch_k, ch_f.format(channel))

            # Remove channels from the object
            del new_channel_obj["channels"]

            # Store the new object
            obj_container[new_key] = new_channel_obj


        # Remove the original object
        del obj_container[key]

# Ok, now we have all the complicated channels stuff, lets make a new config 
# file containing it all
with open(outfile, 'w') as f:
    yaml.dump(configs["global"], f, 
    default_flow_style=False, indent=4, explicit_start=True)

#EOF