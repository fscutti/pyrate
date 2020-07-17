""" Logic functions.
"""
import os

def modus_ponens(p,q):
    """ Implements the modus ponens logic table.
    """
    if p: return q
    else: return not p

def has_key(k,d):
    """ Checks if dictionary has key.
    """
    return k in d

def find_files(paths):
    """ Find all files under a list of paths. It also sorts the list.
    """
    files = []
    for p in paths: files.extend(os.path.join(p,f) for f in os.listdir(p) if os.path.isfile(os.path.join(p,f)))
    files.sort()
    return files


# EOF
