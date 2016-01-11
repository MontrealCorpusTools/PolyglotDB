
import os

from textgrid import TextGrid, IntervalTier

from ..helper import guess_type, guess_trans_delimiter

from ..types.parsing import *

from ..parsers import TextgridParser

def uniqueLabels(tier):
    try:
        return set(x.mark for x in tier.intervals)
    except AttributeError:
        return set(x.mark for x in tier.points)


def averageLabelLen(tier):
    labels = uniqueLabels(tier)
    return sum(len(lab) for lab in labels)/len(labels)

def guess_tiers(tg):
    tier_properties = {}
    tier_guesses = {}
    for i,t in enumerate(tg.tiers):
        tier_properties[t.name] = (i, len(t), averageLabelLen(t), len(uniqueLabels(t)))
    max_labels = max(tier_properties.values(), key = lambda x: x[1])
    for k,v in tier_properties.items():
        if v == max_labels:
            tier_guesses[k] = (k, 'segment')
        else:
            tier_guesses[k] = (k, 'word')
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
                if tier_guesses[ti.name][1] == 'segment':
                    a = SegmentTier(ti.name, tier_guesses[ti.name][0])
                else:
                    labels = uniqueLabels(ti)
                    cat = guess_type(labels, trans_delimiters)
                    if cat == 'transcription':
                        a = TranscriptionTier(ti.name, tier_guesses[ti.name][0])
                        a.trans_delimiter = guess_trans_delimiter(labels)
                    elif cat == 'numeric':
                        raise(NotImplementedError)
                    elif cat == 'orthography':
                        if isinstance(ti, IntervalTier):
                            a = OrthographyTier(ti.name, tier_guesses[ti.name][0])
                        else:
                            a = TextOrthographyTier(ti.name, tier_guesses[ti.name][0])
                    elif cat == 'tobi':
                        a = TobiTier(ti.name, tier_guesses[ti.name][0])
                    else:
                        print(cat)
                        raise(NotImplementedError)
                    print(cat)
                try:
                    print(ti.name)
                    a.add(((x.mark.strip(), x.minTime, x.maxTime) for x in ti), save = False)
                except AttributeError:
                    a.add(((x.mark.strip(), x.time) for x in ti), save = False)
                anno_types.append(a)
        else:
            for i, ti in enumerate(tg.tiers):
                try:
                    anno_types[i].add(((x.mark.strip(), x.minTime, x.maxTime) for x in ti), save = False)
                except AttributeError:
                    anno_types[i].add(((x.mark.strip(), x.time) for x in ti), save = False)
    parser = TextgridParser(anno_types, hierarchy)
    return parser
