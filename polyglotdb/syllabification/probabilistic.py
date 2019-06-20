import math


def norm_count_dict(counts, onset=True):
    """
    Updates a dictionary of onset or coda counts

    Parameters
    ----------
    counts : dict
        a dictionary of onset and coda counts
    onset : boolean
        Defaults to true
        determines whether looking for onset or coda counts
    
    Returns
    -------
    dict
        the updated dictionary
    """
    if onset:
        notfound_factor = .05
        empty_factor = .5
    else:
        notfound_factor = .025
        empty_factor = .5
    tot_count = sum(counts.values())
    counts[None] = sum(counts.values()) * notfound_factor
    counts[tuple()] = sum(counts.values()) * notfound_factor * empty_factor
    counts = {k: math.log(v / sum(counts.values())) for k, v in counts.items()}
    return counts


def split_ons_coda_prob(string, onsets, codas):
    """
    Guesses the split between onset and coda in a string

    Parameters
    ----------
    string : iterable
        the phones to search through
    onsets : iterable
        an iterable of possible onsets
    codas : iterable
        an iterable of possible codas

    Returns
    -------
    int
        best guess for the index in the string where the onset ends and coda begins
    """
    if len(string) == 0:
        return None
    max_prob = -10000
    best = None
    for i in range(len(string) + 1):
        prob = 0
        cod = tuple(string[:i])
        ons = tuple(string[i:])
        if ons not in onsets:
            prob += onsets[None]
        else:
            prob += onsets[ons]
        if cod not in codas:
            prob += codas[None]
        else:
            prob += codas[cod]
        if prob > max_prob:
            max_prob = prob
            best = i
    return best


def split_nonsyllabic_prob(string, onsets, codas):
    """
    Guesses split between onset and coda in list with no found syllabic segments

    Parameters
    ----------
    string : iterable
        the phones to search through
    onsets : iterable
        an iterable of possible onsets
    codas : iterable
        an iterable of possible codas

    Returns
    -------
    int
        best guess for the index in the string where the onset ends and coda begins
    """
    if len(string) == 0:
        return None
    max_prob = -10000
    best = None
    for i in range(len(string) + 1):
        prob = 0
        ons = tuple(string[:i])
        cod = tuple(string[i:])
        if ons not in onsets:
            prob += onsets[None]
        else:
            prob += onsets[ons]
        if cod not in codas:
            prob += codas[None]
        else:
            prob += codas[cod]
        if prob > max_prob:
            max_prob = prob
            best = i
    return best
