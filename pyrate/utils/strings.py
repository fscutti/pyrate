"""General utility functions"""

#def find_tags(name, tags = []):
#    for t in tags

def get_items(s):
    return s.replace(" ","").split(",")

def get_items_from_list(l):
    items = []
    for s in l: items.extend(i for i in get_items(s))
    return items

def remove_tag_from_name(name, tag):
    name = name.split("/")[-1].split(".")[0]
    if name==tag: return tag
    else:         return name.replace(tag,"")


def remove_duplicates(l):
    return list(dict.fromkeys(l))




