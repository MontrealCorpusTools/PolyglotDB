def split_ons_coda_maxonset(string, onsets):
    """
    Finds the split between onset and coda in a string

    Parameters
    ----------
    string : iterable
        the phones to search through
    onsets : iterable
        an iterable of possible onsets

    Returns
    -------
    int
        the index in the string where the onset ends and coda begins
    """
    if len(string) == 0:
        return None
    for i in range(len(string) + 1):
        cod = tuple(string[:i])
        ons = tuple(string[i:])
        if ons not in onsets:
            continue
        return i
    return None


def split_nonsyllabic_maxonset(string, onsets):
    """
    Finds split between onset and coda in list with no found syllabic segments

    Parameters
    ----------
    string : iterable
        the phones to search through
    onsets : iterable
        an iterable of possible onsets

    Returns
    -------
    int
        the index in the string where the onset ends and coda begins
    """
    if len(string) == 0:
        return None
    for i in range(len(string), -1, -1):
        ons = tuple(string[:i])
        cod = tuple(string[i:])
        if ons not in onsets:
            continue
        else:
            return i
    return None
