

def split_ons_coda_maxonset(string, onsets):
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
