from ..types.content import (OrthographyAnnotationType, TranscriptionAnnotationType,
                             NumericAnnotationType)

from ..helper import guess_type

from ..parsers import CsvParser


def inspect_csv(path, num_lines=10, coldelim=None, transdelim=None):
    """
    Generate a :class:`~polyglotdb.io.parsers.csv.CsvParser`
    for a specified text file for parsing it as a column-delimited file

    Parameters
    ----------
    path : str
        Full path to text file
    num_lines: int, optional
        The number of lines to parse from the file
    coldelim: str, optional
        A prespecified column delimiter to use, will autodetect if not
        supplied
    transdelim : list, optional
        A prespecfied set of transcription delimiters to look for, will
        autodetect if not supplied

    Returns
    -------
    :class:`~polyglotdb.io.parsers.csv.CsvParser`
        Autodetected parser for the text file
    """
    if coldelim is not None:
        common_delimiters = [coldelim]
    else:
        common_delimiters = [',', '\t', ':', '|']
    if transdelim is not None:
        trans_delimiters = [transdelim]
    else:
        trans_delimiters = ['.', ' ', ';', ',']

    with open(path, 'r', encoding='utf-8') as f:
        lines = []
        head = f.readline().strip()
        for line in f.readlines():
            lines.append(line.strip())
            # for i in range(num_lines):
            #    line = f.readline()
            #    if not line:
            #        break
            #    lines.append(line)

    best = ''
    num = 1
    for d in common_delimiters:
        trial = len(head.split(d))
        if trial > num:
            num = trial
            best = d
    if best == '':
        raise (DelimiterError('The column delimiter specified did not create multiple columns.'))

    head = head.split(best)
    vals = {h: [] for h in head}

    for line in lines:
        l = line.strip().split(best)
        if len(l) != len(head):
            raise (PCTError('{}, {}'.format(l, head)))
        for i in range(len(head)):
            vals[head[i]].append(l[i])
    atts = []
    for h in head:
        cat = guess_type(vals[h][:num_lines], trans_delimiters)
        if cat == 'transcription':
            a = TranscriptionAnnotationType(h, 'word')
            for t in trans_delimiters:
                if t in vals[h][0]:
                    a.trans_delimiter = t
                    break
        elif cat == 'numeric':
            a = NumericAnnotationType(h, 'word')
        else:
            a = OrthographyAnnotationType(h, 'word')
        a.add(((x,) for x in vals[h]), save=False)
        atts.append(a)

    return CsvParser(atts, best)
