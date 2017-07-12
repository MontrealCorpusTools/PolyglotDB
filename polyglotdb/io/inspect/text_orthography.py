import os

from ..types.parsing import TextOrthographyTier

from ..parsers import OrthographyTextParser


def inspect_orthography(path):
    """
    Generate a :class:`~polyglotdb.io.parsers.text_orthography.OrthographyTextParser`
    for a specified text file for parsing it as an orthographic text

    Parameters
    ----------
    path : str
        Full path to text file
    support_corpus_path : str, optional
        Full path to a corpus to look up transcriptions from spellings
        in the text

    Returns
    -------
    :class:`~polyglotdb.io.parsers.text_orthography.OrthographyTextParser`
        Autodetected parser for the text file
    """
    a = TextOrthographyTier('word', 'word')
    if os.path.isdir(path):
        for root, subdirs, files in os.walk(path):
            for filename in files:
                if not filename.lower().endswith('.txt'):
                    continue
                with open(os.path.join(root, filename),
                          encoding='utf-8-sig', mode='r') as f:
                    index = 0
                    for line in f.readlines():
                        trial = line.strip().split()

                        a.add(((x, index + i) for i, x in enumerate(trial)), save=False)
                        index += len(trial)
    else:
        index = 0
        with open(path, encoding='utf-8-sig', mode='r') as f:
            for line in f.readlines():
                trial = line.strip().split()

                a.add(((x, index + i) for i, x in enumerate(trial)), save=False)
                index += len(trial)
    annotation_types = [a]
    return OrthographyTextParser(annotation_types)
