import json
import re

non_letter_finder = re.compile('\W')


def value_for_cypher(value):
    """
    returns the value in cypher form

    Parameters
    ----------
    value : str, list, or boolean
       
    Returns
    -------
    v : str
        a string formatted for cypher
    """
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
    """
    Checks if key is a non-letter, if it is, turns it into a string

    Parameters
    ----------
    key : letter or non-letter
        
    Returns
    -------
    key : str
        key made into a string
    """
    key = key.replace("`",'')
    if non_letter_finder.search(key) is not None:
        return "`{}`".format(key)
    return key
