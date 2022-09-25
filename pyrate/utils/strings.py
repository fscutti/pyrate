"""General utility functions"""

def remove_duplicates(l):
    """Creates list from dictionary keys."""
    return list(dict.fromkeys(l))


def read_list(input):
    """ Parses a pyrate yaml config list
    """
    if type(input) == str:
        return get_items(input)
    elif type(input) != list:
        return [input]
    return input

def get_items(s, no_duplicates=True):
    """Gets comma-separated items in a string as a list."""
    items = []

    if not s:
        return [""]

    for i in str(s).split(","):
        if not '"' in i:
            items.append(i.replace(" ", ""))
        else:
            items.append(i.replace('"', ""))

    if no_duplicates:
        return remove_duplicates(items)
    else:
        return items


def get_items_fast(s):
    return [i.replace(" ", "") for i in str(s).split(",")]


def get_items_from_list(l):
    """Gets comma-separated items in lists of strings as a list."""
    items = []
    for s in l:
        items.extend(i for i in get_items(s))
    return items

def pyrate_yaml_to_list(input):
    """ Parses a pyrate yaml config list
    """
    if type(input) == str:
        return get_items(input)
    elif type(input) != list:
        return [input]
    return input

def remove_tag_from_name(name, tag):
    """Removes a tag from a name given as a string."""
    name = name.split("/")[-1].split(".")[0]
    if name == tag:
        return tag
    else:
        return name.replace(tag, "")

def replace_clean(s, t, v):
    """ Replaces tag t in string s with value v cleanly
        (if there's quotes around it, clears them)
    """
    v = str(v).replace('\'', "\"")
    return s.replace(f' "{t}"', f" {v}").replace(str(t), v)


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
