import json
import re

non_letter_finder = re.compile('\W')

def value_for_cypher(value):
    if isinstance(value, str):
        return "'{}'".format(value)
    if isinstance(value, list):
        return json.dumps(value)
    else:
        v = "{}".format(value)
        if isinstance(value, bool):
            v = v.lower()
        return v

def key_for_cypher(key):
    if non_letter_finder.search(key) is not None:
        return "`{}`".format(key)
    return key
