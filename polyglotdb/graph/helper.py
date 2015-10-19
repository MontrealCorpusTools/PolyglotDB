import json


anchor_attributes = ['begin', 'end', 'duration']
type_attributes = ['label', 'transcription']

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
