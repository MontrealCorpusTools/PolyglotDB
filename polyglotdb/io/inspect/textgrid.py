import os
import math
from praatio import tgio


from polyglotdb.structure import Hierarchy

from ..helper import guess_type, guess_trans_delimiter

from ..types.parsing import *

from ..parsers import TextgridParser


def calculate_probability(x, mean, stdev):
    """
    Calculates the probability that a given tier is a word or phone

    Parameters
    ----------
    x : float
        duration of the object in question
    mean : float
        mean duration of that type of object
    stdev : float
        standard deviation from mean
    """
    exponent = math.exp(-(math.pow(x - mean, 2) / (2 * math.pow(stdev, 2))))
    return (1 / (math.sqrt(2 * math.pi) * stdev)) * exponent


def word_probability(average_duration):
    """
    Calculates probability of tier being a word tier

    Parameters
    ----------
    average_duration : float
        the average duration of elements in the tier

    Returns
    -------
    float
        the probability that the tier is a word tier
    """
    mean = 0.2465409  # Taken from the Buckeye corpus
    sd = 0.03175723
    return calculate_probability(average_duration, mean, sd)


def segment_probability(average_duration):
    """
    Calculates probability of tier being a phone tier

    Parameters
    ----------
    average_duration : float
        the average duration of elements in the tier

    Returns
    -------
    float
        the probability that the tier is a phone tier
    """
    mean = 0.08327773  # Taken from the Buckeye corpus
    sd = 0.03175723  # Actually=0.009260103
    return calculate_probability(average_duration, mean, sd)


def uniqueLabels(tier):
    """
    Gets the label from the tier, removing duplicates

    Parameters
    ----------
    tier : IntervalTier
        the tier to collect labels from

    Returns
    -------
    set
        label from the tier
    """
    if isinstance(tier, tgio.IntervalTier):
        return set(x for _, _, x in tier.entryList)
    else:
        return set(x for _, x in tier.entryList)


def average_duration(tier):
    """
    Gets the average duration of elements in a tier

    Parameters
    ----------
    tier : IntervalTier
        the tier to get duration from

    Returns
    -------
    double
        average duration
    """

    if isinstance(tier, tgio.IntervalTier):
        return sum(float(end) - float(begin) for (begin, end, _) in tier.entryList) / len(tier.entryList)
    else:
        return float(tier.maxTime) / len(tier.entryList)


def averageLabelLen(tier):
    """
    Get the average label length in a tier

    Parameters
    ----------
    tier : IntervalTier
        the tier to collect labels from

    Returns
    -------
    double
        average label length
    """
    labels = uniqueLabels(tier)
    if not labels:
        return 0
    return sum(len(lab) for lab in labels) / len(labels)


def figure_linguistic_type(labels):
    """
    Gets linguistic type for labels

    Parameters
    ----------
    labels : list of lists
        the labels of a tier

    Returns
    -------

        the linguistic type
     """
    if len(labels) == 0:
        return None
    elif len(labels) == 1:
        return labels[0][0]
    label = min(labels, key=lambda x: x[1])
    return label[0]


def guess_tiers(tg):
    """
    Guesses whether tiers are words or segments

    Parameters
    ----------
    tg : TextGrid
        the textgrid object

    Returns
    -------
    tier_guesses : dict
        the tiers and their likelihoods
    hierarchy : `~polyglotdb.structure.Hierarchy`
        the hierarchy object
    """
    tier_properties = {}
    tier_guesses = {}
    for i, tier_name in enumerate(tg.tierNameList):
        ti = tg.tierDict[tier_name]
        if len(ti.entryList) == 0:
            continue
        ti.maxTime = tg.maxTimestamp
        tier_properties[ti.name] = (i, average_duration(ti))
    for k, v in tier_properties.items():
        if v is None:
            continue
        word_p = word_probability(v[1])
        phone_p = segment_probability(v[1])
        if word_p > phone_p:
            tier_guesses[k] = ('word', v[0])
        else:
            tier_guesses[k] = ('segment', v[0])
    word_labels = [(k, v[1]) for k, v in tier_guesses.items() if v[0] == 'word']
    phone_labels = [(k, v[1]) for k, v in tier_guesses.items() if v[0] == 'segment']
    word_type = figure_linguistic_type(word_labels)
    phone_type = figure_linguistic_type(phone_labels)
    for k, v in tier_guesses.items():
        if 'word' in k.lower() or v[0] == 'word':
            tier_guesses[k] = word_type
        else:
            tier_guesses[k] = phone_type
    h = {word_type: None}
    if phone_type is not None:
        h[phone_type] = word_type
    hierarchy = Hierarchy(h)
    return tier_guesses, hierarchy


def inspect_textgrid(path):
    """
    Generate a :class:`~polyglotdb.io.parsers.textgrid.TextgridParser` for a specified TextGrid file

    Parameters
    ----------
    path : str
        Full path to TextGrid file

    Returns
    -------
    :class:`~polyglotdb.io.parsers.textgrid.TextgridParser`
        Autodetected parser for the TextGrid file
    """
    trans_delimiters = ['.', ' ', ';', ',']
    textgrids = []
    if os.path.isdir(path):
        for root, subdirs, files in os.walk(path):
            for filename in files:
                if not filename.lower().endswith('.textgrid'):
                    continue
                textgrids.append(os.path.join(root, filename))
    else:
        textgrids.append(path)
    anno_types = []
    for t in textgrids:
        tg = tgio.openTextgrid(t)
        if len(anno_types) == 0:
            tier_guesses, hierarchy = guess_tiers(tg)
            for i, tier_name in enumerate(tg.tierNameList):
                ti = tg.tierDict[tier_name]
                if tier_name not in tier_guesses:
                    a = OrthographyTier('word', 'word')
                    a.ignored = True
                elif tier_guesses[tier_name] == 'segment':
                    a = SegmentTier(tier_name, tier_guesses[ti.name])
                else:
                    labels = uniqueLabels(ti)
                    cat = guess_type(labels, trans_delimiters)
                    if cat == 'transcription':
                        a = TranscriptionTier(ti.name, tier_guesses[ti.name])
                        a.trans_delimiter = guess_trans_delimiter(labels)
                    elif cat == 'numeric':
                        if isinstance(ti, tgio.IntervalTier):
                            raise (NotImplementedError)
                        else:
                            a = BreakIndexTier(ti.name, tier_guesses[ti.name])
                    elif cat == 'orthography':
                        if isinstance(ti, tgio.IntervalTier):
                            a = OrthographyTier(ti.name, tier_guesses[ti.name])
                        else:
                            a = TextOrthographyTier(ti.name, tier_guesses[ti.name])
                    elif cat == 'tobi':
                        a = TobiTier(tier_name, tier_guesses[ti.name])
                    elif cat == 'grouping':
                        a = GroupingTier(ti.name, tier_guesses[ti.name])
                    else:
                        print(tier_name)
                        print(cat)
                        raise (NotImplementedError)
                if not a.ignored:
                    if isinstance(ti, tgio.IntervalTier):
                        a.add(( (text.strip(), begin, end) for (begin, end, text) in ti.entryList), save=False)
                    else:
                        a.add(((text.strip(), time) for time, text in ti.entryList), save=False)
                anno_types.append(a)
        else:
            for i, tier_name in enumerate(tg.tierNameList):
                ti = tg.tierDict[tier_name]
                if anno_types[i].ignored:
                    continue
                if isinstance(ti, tgio.IntervalTier):
                    anno_types[i].add(( (text.strip(), begin, end) for (begin, end, text) in ti.entryList), save=False)
                else:
                    anno_types[i].add(((text.strip(), time) for time, text in ti.entryList), save=False)

    parser = TextgridParser(anno_types, hierarchy)
    return parser
