import math

def norm_count_dict(counts, onset = True):
    if onset:
        notfound_factor = .05
        empty_factor = .5
    else:
        notfound_factor = .025
        empty_factor = .5
    tot_count = sum(counts.values())
    counts[None] = sum(counts.values()) * notfound_factor
    counts[tuple()] = sum(counts.values()) * notfound_factor * empty_factor
    counts = {k: math.log(v / sum(counts.values())) for k,v in counts.items()}
    return counts

def split_ons_coda_prob(string, onsets, codas):
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
