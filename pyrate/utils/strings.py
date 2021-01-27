"""General utility functions"""

import os


def remove_duplicates(l):
    """Creates list from dictionary keys."""
    return list(dict.fromkeys(l))


def get_items(s):
    """Gets comma-separated items in a string as a list."""
    items = []

    for i in str(s).split(","):
        if not "\"" in i:
            items.append(i.replace(" ", ""))
        else:
            items.append(i.replace("\"", ""))

    return items


def get_items_from_list(l):
    """Gets comma-separated items in lists of strings as a list."""
    items = []
    for s in l:
        items.extend(i for i in get_items(s))
    return items


def remove_tag_from_name(name, tag):
    """Removes a tag from a name given as a string."""
    name = name.split("/")[-1].split(".")[0]
    if name == tag:
        return tag
    else:
        return name.replace(tag, "")


def get_tags(f):
    """Breaks down a file name into its tags and returns them as a list."""
    if "/" in f:
        f = f.split("/")[-1]
    if "." in f:
        f = f.split(".")[0]
    if "_" in f:
        f = f.split("_")
    if ":" in f:
        f = f.split(":")
    return f


def check_tag(s, l):
    """Checks if any string in the list l is contained in string s."""
    for i in l:
        if s in i:
            return True
    return False


# EOF
