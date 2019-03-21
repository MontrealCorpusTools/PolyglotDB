from polyglotdb.structure import Hierarchy

from ..types.parsing import *

from ..parsers import FaveParser


def inspect_fave(path):
    """
    Generate an :class:`~polyglotdb.io.parsers.fave.FaveParser`
    for a specified text file for parsing it as an FAVE text file

    Parameters
    ----------
    path : str
        Full path to text file

    Returns
    -------
    :class:`~polyglotdb.io.parsers.ilg.FaveParser`
        Autodetected parser for the text file
    """
    annotation_types = [OrthographyTier(FaveParser.word_label, 'word'),
                        OrthographyTier(FaveParser.phone_label, 'phone')]

    annotation_types[0].label = True
    annotation_types[1].label = True
    hierarchy = Hierarchy({'phone': 'word', 'word': None})

    return FaveParser(annotation_types, hierarchy)
