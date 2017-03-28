import os

from ..helper import (guess_type, guess_trans_delimiter,
                      ilg_text_to_lines, most_frequent_value, calculate_lines_per_gloss)

from ..types.parsing import (TextOrthographyTier, TextTranscriptionTier,
                             TextMorphemeTier)

from ..parsers import IlgParser


def inspect_ilg(path, number=None):
    """
    Generate an :class:`~polyglotdb.io.parsers.ilg.IlgParser`
    for a specified text file for parsing it as an interlinear gloss text file

    Parameters
    ----------
    path : str
        Full path to text file
    number : int, optional
        Number of lines per gloss, if not supplied, it is auto-detected

    Returns
    -------
    :class:`~polyglotdb.io.parsers.ilg.IlgParser`
        Autodetected parser for the text file
    """
    trans_delimiters = ['.', ';', ',']
    lines = {}
    if os.path.isdir(path):
        numbers = {}
        for root, subdirs, files in os.walk(path):
            for filename in files:
                if not filename.lower().endswith('.txt'):
                    continue
                p = os.path.join(root, filename)
                lines[p] = ilg_text_to_lines(p)
                numbers[p] = calculate_lines_per_gloss(lines[p])
        number = most_frequent_value(numbers)
    else:
        lines[path] = ilg_text_to_lines(path)
        number = calculate_lines_per_gloss(lines[path])
        p = path
    annotation_types = []
    for i in range(number):
        name = 'Line {}'.format(i + 1)
        labels = lines[p][i][1]
        cat = guess_type(labels, trans_delimiters)
        if i == 0 and cat == 'orthography':
            a = TextOrthographyTier('word', 'word')
        else:
            if cat == 'transcription':
                a = TextTranscriptionTier('transcription', 'word')
                a.trans_delimiter = guess_trans_delimiter(labels)
            elif cat == 'morpheme':
                a = TextMorphemeTier('morpheme', 'word')
            else:
                raise (NotImplementedError)
        annotation_types.append(a)
    for k, v in lines.items():
        if k == p:
            continue
        for i in range(number):
            labels = lines[k][i][1]
            annotation_types[i].add(((x, j) for j, x in enumerate(labels)), save=False)

    return IlgParser(annotation_types)
