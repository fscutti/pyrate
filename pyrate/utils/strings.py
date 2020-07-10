"""General utility functions"""

#def find_tags(name, tags = []):
#    for t in tags

def get_items(s):
    return s.replace(" ","").split(",")


def remove_tag_from_name(name, tag):
    name = name.split("/")[-1]
    return name.replace(tag,"")


