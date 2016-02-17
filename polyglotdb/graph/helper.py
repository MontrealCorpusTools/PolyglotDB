import json
import re

non_letter_finder = re.compile('\W')

type_attributes = ['transcription']

def value_for_cypher(value):
    if isinstance(value, str):
        return "'{}'".format(value)
    if isinstance(value, list):
        return json.dumps(value)
    else:
        return "{}".format(value)

def key_for_cypher(key):
    if non_letter_finder.search(key) is not None:
        return "`{}`".format(key)
    return key
