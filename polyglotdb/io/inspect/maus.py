from polyglotdb.structure import Hierarchy

from ..types.parsing import *

from ..parsers import MausParser


def inspect_maus(path):
    """
    Generate an :class:`~polyglotdb.io.parsers.maus.MausParser`
    for a specified text file for parsing it as a MAUS file

    Parameters
    ----------
    path : str
        Full path to text file

    Returns
    -------
    :class:`~polyglotdb.io.parsers.maus.MausParser`
        Autodetected parser for MAUS TextGrids
    """

    annotation_types = [OrthographyTier(MausParser.word_label, 'word'),
                        OrthographyTier(MausParser.phone_label, 'phone')]

    annotation_types[0].label = True
    annotation_types[1].label = True
    hierarchy = Hierarchy({'phone': 'word', 'word': None})

    return MausParser(annotation_types, hierarchy)
