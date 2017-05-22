from polyglotdb.structure import Hierarchy

from ..types.parsing import *

from ..parsers.partitur import PartiturParser


def inspect_partitur(path):
    """
    Generate an :class:`~polyglotdb.io.parsers.partitur.PartiturParser`
    for a specified text file for parsing it as a BAS Partitur file

    Parameters
    ----------
    path : str
        Full path to text file

    Returns
    -------
    :class:`~polyglotdb.io.parsers.paritur.PartiturParser`
        Autodetected parser for BAS Partitur
    """
    annotation_types = [OrthographyTier('word', 'word'),
                        OrthographyTier('transcription', 'word'),
                        OrthographyTier('phones', 'phone')]

    annotation_types[0].label = True
    annotation_types[1].label = False
    annotation_types[1].type_property = True
    annotation_types[2].label = True

    hierarchy = Hierarchy({'phone': 'word', 'word': None})

    return PartiturParser(annotation_types, hierarchy)
