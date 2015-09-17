import json


def value_for_cypher(value):
    if isinstance(value, str):
        return "'{}'".format(value)
    if isinstance(value, list):
        return json.dumps(value)
    else:
        return "{}".format(value)

def key_for_cypher(key):
    if ' ' in key:
        return "`{}`".format(key)
    return key
