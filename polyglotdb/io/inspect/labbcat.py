from polyglotdb.structure import Hierarchy

from ..types.parsing import *

from ..parsers import LabbCatParser


def inspect_labbcat(path):
    """
    Generate an :class:`~polyglotdb.io.parsers.ilg.LabbCatParser`
    for a specified text file for parsing it as a LabbCat file

    Parameters
    ----------
    path : str
        Full path to text file

    Returns
    -------
    :class:`~polyglotdb.io.parsers.ilg.LabbCat`
        Autodetected parser for LabbCat
    """

    annotation_types = [OrthographyTier('transcrip', 'word'),
                        OrthographyTier('segment', 'phone')]

    annotation_types[0].label = True
    annotation_types[1].label = True
    hierarchy = Hierarchy({'phone': 'word', 'word': None})

    return LabbCatParser(annotation_types, hierarchy)
