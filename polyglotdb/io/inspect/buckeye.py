from polyglotdb.structure import Hierarchy

from ..types.parsing import *

from ..parsers import BuckeyeParser


def inspect_buckeye(word_path):
    """
    Generate a :class:`~polyglotdb.io.parsers.buckeye.BuckeyeParser`
    for the Buckeye corpus.

    Parameters
    ----------
    word_path : str
        Full path to text file

    Returns
    -------
    :class:`~polyglotdb.io.parsers.buckeye.BuckeyeParser`
        Auto-detected parser for the Buckeye corpus
    """
    annotation_types = [OrthographyTier('word', 'word'),
                        OrthographyTier('transcription', 'word'),
                        OrthographyTier('surface_transcription', 'word'),
                        OrthographyTier('category', 'word'),
                        SegmentTier('phone', 'phone')]
    #annotation_types[1].trans_delimiter = ' '
    #annotation_types[2].trans_delimiter = ' '
    annotation_types[2].type_property = False
    annotation_types[3].type_property = False
    hierarchy = Hierarchy({'phone': 'word', 'word': None})

    return BuckeyeParser(annotation_types, hierarchy)
