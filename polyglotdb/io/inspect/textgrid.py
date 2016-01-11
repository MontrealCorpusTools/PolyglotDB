
import os
import math

from textgrid import TextGrid, IntervalTier

from ..helper import guess_type, guess_trans_delimiter

from ..types.parsing import *

from ..parsers import TextgridParser


def calculate_probability(x, mean, stdev):
    exponent = math.exp(-(math.pow(x-mean,2)/(2*math.pow(stdev,2))))
    return (1 / (math.sqrt(2*math.pi) * stdev)) * exponent

def word_probability(average_duration):
    mean = 0.2465409 # Taken from the Buckeye corpus
    sd = 0.03175723
    return calculate_probability(average_duration, mean, sd)

def segment_probability(average_duration):
    mean = 0.08327773 # Taken from the Buckeye corpus
    sd = 0.009260103
    return calculate_probability(average_duration, mean, sd)


def uniqueLabels(tier):
    try:
        return set(x.mark for x in tier.intervals)
    except AttributeError:
        return set(x.mark for x in tier.points)

def average_duration(tier):

    if isinstance(tier, IntervalTier):
        return sum(x.maxTime - x.minTime for x in tier) / len(tier)
    else:
        return tier.maxTime/ len(tier)

def averageLabelLen(tier):
    labels = uniqueLabels(tier)
    if not labels:
        return 0
    return sum(len(lab) for lab in labels)/len(labels)

def guess_tiers(tg):
    tier_properties = {}
    tier_guesses = {}
    for i,t in enumerate(tg.tiers):
        if len(t) == 0:
            continue
        t.maxTime = tg.maxTime
        tier_properties[t.name] = (i, average_duration(t))
    for k,v in tier_properties.items():
        if v is None:
            continue
        word_p = word_probability(v[1])
        phone_p = segment_probability(v[1])
        if word_p > phone_p:
            tier_guesses[k] = (k, 'word')
        else:
            tier_guesses[k] = (k, 'segment')
    hierarchy = {'phone': 'word', 'word': None}
    return tier_guesses, hierarchy

def inspect_textgrid(path):
    """
    Generate a list of AnnotationTypes for a specified TextGrid file

    Parameters
    ----------
    path : str
        Full path to TextGrid file

    Returns
    -------
    list of AnnotationTypes
        Autodetected AnnotationTypes for the TextGrid file
    """
    trans_delimiters = ['.',' ', ';', ',']
    textgrids = []
    if os.path.isdir(path):
        for root, subdirs, files in os.walk(path):
            for filename in files:
                if not filename.lower().endswith('.textgrid'):
                    continue
                textgrids.append(os.path.join(root,filename))
    else:
        textgrids.append(path)
    anno_types = []
    for t in textgrids:
        tg = TextGrid()
        tg.read(t)
        if len(anno_types) == 0:
            tier_guesses, hierarchy = guess_tiers(tg)
            print(hierarchy, tier_guesses)
            for ti in tg.tiers:
                if ti.name not in tier_guesses:
                    a = OrthographyTier('word', 'word')
                    a.ignored = True
                elif tier_guesses[ti.name][1] == 'segment':
                    a = SegmentTier(ti.name, tier_guesses[ti.name][0])
                else:
                    labels = uniqueLabels(ti)
                    cat = guess_type(labels, trans_delimiters)
                    if cat == 'transcription':
                        a = TranscriptionTier(ti.name, tier_guesses[ti.name][0])
                        a.trans_delimiter = guess_trans_delimiter(labels)
                    elif cat == 'numeric':
                        if isinstance(ti, IntervalTier):
                            raise(NotImplementedError)
                        else:
                            a = BreakIndexTier(ti.name, tier_guesses[ti.name][0])
                    elif cat == 'orthography':
                        if isinstance(ti, IntervalTier):
                            a = OrthographyTier(ti.name, tier_guesses[ti.name][0])
                        else:
                            a = TextOrthographyTier(ti.name, tier_guesses[ti.name][0])
                    elif cat == 'tobi':
                        a = TobiTier(ti.name, tier_guesses[ti.name][0])
                    elif cat == 'grouping':
                        a = GroupingTier(ti.name, tier_guesses[ti.name][0])
                    else:
                        print(ti.name)
                        print(cat)
                        raise(NotImplementedError)
                if not a.ignored:
                    try:
                        a.add(((x.mark.strip(), x.minTime, x.maxTime) for x in ti), save = False)
                    except AttributeError:
                        a.add(((x.mark.strip(), x.time) for x in ti), save = False)
                anno_types.append(a)
        else:
            for i, ti in enumerate(tg.tiers):
                if anno_types[i].ignored:
                    continue
                try:
                    anno_types[i].add(((x.mark.strip(), x.minTime, x.maxTime) for x in ti), save = False)
                except AttributeError:
                    anno_types[i].add(((x.mark.strip(), x.time) for x in ti), save = False)
    parser = TextgridParser(anno_types, hierarchy)
    return parser
