""" Logic functions.
"""
import os
from copy import copy
import mmap


def modus_ponens(p, q):
    """Implements the modus ponens logic table: p -> q"""
    if p:
        return q
    else:
        return not p


def find_env(path, env):
    """Checks existence of environment variable in path and eventually replaces it."""
    if env in path:
        path = path.replace(env, os.environ.get(env))
    return path


def find_files(paths, env=None):
    """Find all files under a list of paths. It also sorts the list."""
    files = []

    if not isinstance(paths, list):
        paths = [paths]

    for p in paths:

        if env and env in p:
            p = p.replace(env, os.environ.get(env))

        if not os.path.isfile(p):
            files.extend(
                os.path.join(p, f)
                for f in os.listdir(p)
                if os.path.isfile(os.path.join(p, f))
            )
        else:
            files.append(p)

    files.sort()

    return files


def get_nested_values(d):
    """Returns a generator over all values of a nested dictionary."""
    for v in d.values():
        if isinstance(v, dict):
            yield from get_nested_values(v)
        else:
            yield v


def flatten(l):
    """Flattens a list of lists."""
    return [item for sublist in l for item in sublist]


def nested(l):
    """Returns a nested dictionary where keys are taken from a list."""
    d = tmp = {}
    for k in l:
        tmp[k] = {}
        tmp = tmp[k]
    return d


def get_copy(o, copy):
    """Returns copy of object."""
    if copy:
        return copy(o)
    else:
        return o


def pretty(d, indent=0):
    """Prints dictionary with pre-defined intentation."""
    for key, value in d.items():
        print("\t" * indent + str(key))
        if isinstance(value, dict):
            pretty(value, indent + 1)
        else:
            if isinstance(value, list):
                print("\t" * (indent + 1))
                for idx, l in enumerate(value):
                    print("\t" * (indent + 1) + str(idx) + " : " + str(l))
            else:
                print("\t" * (indent + 1) + str(value))


def merge(target, probe, path=None, merge_list=False):
    """Merges probe into target."""
    if path is None:
        path = []

    for k in probe:
        if k in target:

            if isinstance(target[k], dict) and isinstance(probe[k], dict):
                merge(target[k], probe[k], path + [str(k)])

            elif target[k] == probe[k]:
                # same leaf value
                pass

            elif merge_list:
                # if a conflict exist but values are lists merge them upon request
                if isinstance(target[k], list) and isinstance(probe[k], list):
                    target[k].extend(probe[k])

                    target[k] = list(dict.fromkeys(target[k]))

            else:
                raise Exception("Conflict at %s" % ".".join(path + [str(k)]))
        else:
            target[k] = probe[k]
    return target


def intersect(probe, target):
    """Intersection of two nested dictionaries."""
    intersection = {}

    if probe == {}:
        intersection = target

    else:
        for k in set(target).intersection(set(probe)):

            p = probe[k]
            t = target[k]

            if isinstance(t, dict) and isinstance(p, dict):
                if p == {}:
                    intersection[k] = t
                else:
                    intersection[k] = intersect(p, t)

            elif not isinstance(t, dict) and p == {}:
                intersection[k] = t

            elif t == p:
                intersection[k] = t
            else:
                raise ValueError("values for common keys don't match")
    return intersection


def find(key, dictionary):
    """Find value of key in nested dictionary and returns a generator over the found arguments.
    Thank you, internet!
    https://stackoverflow.com/questions/9807634/find-all-occurrences-of-a-key-in-nested-dictionaries-and-lists
    """
    if hasattr(dictionary, "items"):
        for k, v in dictionary.items():
            if k == key:
                yield v

            if isinstance(v, dict):
                for result in find(key, v):
                    yield result

            elif isinstance(v, list):
                for d in v:
                    for result in find(key, d):
                        yield result


def check(key, dictionary):
    """Uses the find function to just check the existence of the key without returning the generator."""
    return bool([i for i in find(key, dictionary)])


def grab(key, dictionary):
    """This is just a wrapper around the find function, getting a single item as opposed to the iterator."""
    return [i for i in find(key, dictionary)][0]


def check_dict_in_list(list, dictionary):
    """Checks if a dictionary is found in a list of dictionaries."""
    for d in list:

        counter = 0

        for k, v in dictionary.items():

            if k in d:
                if d[k] == v:

                    counter += 1

        if counter == len(dictionary):
            return True

    return False


def get_color(my_color):
    """Given a pixel string it prepares a pixel dictionary."""
    my_color = my_color.replace(" ", "")

    my_color = {c.split(":")[0]: float(c.split(":")[1]) for c in my_color.split("|")}

    return my_color


def add_colors(my_color_list):
    """Adds color pixels from a list. Avoids white."""
    added_color = {"R": 0.0, "G": 0.0, "B": 0.0}

    for idx, my_color in enumerate(my_color_list):

        added_color["R"] += my_color["R"]
        added_color["G"] += my_color["G"]
        added_color["B"] += my_color["B"]

        is_white = sum([added_color[pixel] for pixel in ["R", "G", "B"]]) >= 2.9

        if is_white:
            added_color[["R", "G", "B"][idx % 3]] = 0.0

    return added_color


def iterable(obj):
    """Determines if an object is iterable or not"""
    try:
        iter(obj)
    except Exception:
        return False
    else:
        return True


def is_float(var):
    """Checks if a string can be converted to a float"""
    try:
        float(var)
        return True
    except:
        return False


def is_wc_ascii(filepath):
    """Determines if a file is a text wavecatcher file"""
    filepath = os.path.abspath(filepath)
    try:
        with open(filepath) as f:
            first_line = f.readline()
        if "=== DATA FILE SAVED WITH SOFTWARE VERSION:" in first_line:
            return True
    except UnicodeDecodeError:
        # Not ascii
        pass
    return False


def is_wd_ascii(filepath):
    """Determines if a file is an ASCII wavedump file"""
    filepath = os.path.abspath(filepath)
    try:
        with open(filepath) as f:
            first_line = f.readline()
            if "Record Length:" in first_line:
                return True
    except UnicodeDecodeError:
        pass
    return False


def is_bt(filepath, store, logger, structure):
    """Determines if a file is a bluetongue file"""
    filepath = os.path.abspath(filepath)
    from pyrate.readers.ReaderBlueTongueMMAP import ReaderBlueTongueMMAP

    try:
        reader = ReaderBlueTongueMMAP("BT_CHECK", store, logger, filepath, structure)
        # Read like the BlueTongue reader does
        # --------------------------------------------------------------------
        # Mimic the load() function without getting the file size as it's slow
        reader.is_loaded = True
        reader.f = open(reader.f, "rb")
        reader._idx = 0
        reader._mmf = mmap.mmap(reader.f.fileno(), length=0, access=mmap.ACCESS_READ)
        reader._event = 0
        reader._event_size = 0
        reader._header_size = 0
        # Hack to check if the board number is too high
        # if it's over 64, then something is really wrong
        current_pos = reader._mmf.tell()
        reader._hd = {"n_boards": reader._get_items(1, "I")[0]}
        if reader._hd["n_boards"] > 64:
            # Uh oh, something's not right, probably not a BT file
            return False
        reader._mmf.seek(current_pos)
        reader._set_header_dict()
        reader._set_event_dict()
        reader.f.close()
        # load() function over
        # ------------------------------------------------------------------
        if reader._event != reader._idx * reader._event_size + reader._header_size:
            reader._event = reader._idx * reader._event_size + reader._header_size
        reader._move(reader._event)
        t = grab("check_word", reader._ev)
        items_number, items_type, items_offset = t[0], t[1], t[2]
        reader._mmf.seek(items_offset, 1)
        cw = reader._get_items(items_number, items_type)[0]
        if cw == 65226:
            # All good!
            return True
    except:
        pass
    finally:
        try:
            reader.offload()
            del reader
        except:
            pass
    return False


# EOF
