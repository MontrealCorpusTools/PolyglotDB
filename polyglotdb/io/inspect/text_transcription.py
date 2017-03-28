import os

from ..types.parsing import TextTranscriptionTier

from ..helper import guess_trans_delimiter

from ..parsers import TranscriptionTextParser


def inspect_transcription(path):
    """
    Generate a :class:`~polyglotdb.io.parsers.text_transcription.TranscriptionTextParser`
    for a specified text file for parsing it as a transcribed text

    Parameters
    ----------
    path : str
        Full path to text file

    Returns
    -------
    :class:`~polyglotdb.io.parsers.text_transcription.TranscriptionTextParser`
        Autodetected parser for the text file
    """
    trans_delimiters = ['.', ';', ',']

    a = TextTranscriptionTier('transcription', 'word')

    if os.path.isdir(path):
        for root, subdirs, files in os.walk(path):
            for filename in files:
                if not filename.lower().endswith('.txt'):
                    continue
                with open(os.path.join(root, filename),
                          encoding='utf-8-sig', mode='r') as f:
                    num_annotations = 0
                    for line in f.readlines():
                        trial = line.strip().split()
                        if a.trans_delimiter is None:
                            a.trans_delimiter = guess_trans_delimiter(trial)

                        a.add(((x, num_annotations + i) for i, x in enumerate(trial)), save=False)
                        num_annotations += len(trial)
    else:
        with open(path, encoding='utf-8-sig', mode='r') as f:
            num_annotations = 0
            for line in f.readlines():
                trial = line.strip().split()
                if a.trans_delimiter is None:
                    a.trans_delimiter = guess_trans_delimiter(trial)

                a.add(((x, num_annotations + i) for i, x in enumerate(trial)), save=False)
                num_annotations += len(trial)
    annotation_types = [a]
    return TranscriptionTextParser(annotation_types)
