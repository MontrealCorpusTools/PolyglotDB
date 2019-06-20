from .maxonset import split_nonsyllabic_maxonset, split_ons_coda_maxonset

from .probabilistic import split_nonsyllabic_prob, split_ons_coda_prob


def syllabify(phones, syllabics, onsets, codas, algorithm='maxonset'):
    """
    Given a list of phones, groups them into syllables

    Parameters
    ----------
    phones : iterable
        an iterable of phones in the corpus
    syllabics : list
        a list of syllabic segments
    onsets : list
        a list of onsets 
    codas : list
        a list of codas
    algorithm : str
        the type of algorithm being used to determine syllables 
        Defaults to 'maxonset'

    Returns
    -------
    syllables : list
        a list of dictionaries which contain vowel, onset, coda, and label

    """

    vow_inds = [i for i, x in enumerate(phones) if x in syllabics]
    if len(vow_inds) == 0:
        if algorithm == 'probabilistic':
            split = split_nonsyllabic_prob(phones, onsets, codas)
        elif algorithm == 'maxonset':
            split = split_nonsyllabic_maxonset(phones, onsets)
        else:
            split=None
        label = '.'.join(phones)
        row = {'onset_id': phones[0],
               'break': split,
               'coda': phones[-1],
               'label': label}
        return [row]
    syllables = []
    for j, i in enumerate(vow_inds):
        cur_vow_id = phones[i]
        if j == 0:
            begin_ind = 0
            if i != 0:
                cur_ons_id = phones[begin_ind]
            else:
                cur_ons_id = None
        else:
            prev_vowel_ind = vow_inds[j - 1]
            cons_string = phones[prev_vowel_ind + 1:i]

            if algorithm == 'probabilistic':
                split = split_ons_coda_prob(cons_string, onsets, codas)
            elif algorithm == 'maxonset':
                split = split_ons_coda_maxonset(cons_string, onsets)
            else:
                split = None
            if split is None:
                cur_ons_id = None
                begin_ind = i
            else:
                begin_ind = prev_vowel_ind + 1 + split

        if j == len(vow_inds) - 1:
            end_ind = len(phones) - 1
            if i != len(phones) - 1:
                cur_coda_id = phones[end_ind]
            else:
                cur_coda_id = None
        else:
            foll_vowel_ind = vow_inds[j + 1]
            cons_string = phones[i + 1:foll_vowel_ind]
            if algorithm == 'probabilistic':
                split = split_ons_coda_prob(cons_string, onsets, codas)
            elif algorithm == 'maxonset':
                split = split_ons_coda_maxonset(cons_string, onsets)
            else:
                split = None
            if split is None:
                cur_coda_id = None
                end_ind = i
            else:
                end_ind = i + split
                cur_coda_id = phones[end_ind]
        label = '.'.join(phones[begin_ind:end_ind + 1])
        row = {
            'vowel': cur_vow_id, 'onset': cur_ons_id,
            'label': label,
            'coda': cur_coda_id}
        syllables.append(row)
    return syllables
