from polyglotdb.structure import Hierarchy

from ..types.parsing import *

from ..parsers import MfaParser


def inspect_mfa(path):
    """
    Generate an :class:`~polyglotdb.io.parsers.mfa.MfaParser`
    for a specified text file for parsing it as a MFA file

    Parameters
    ----------
    path : str
        Full path to text file

    Returns
    -------
    :class:`~polyglotdb.io.parsers.mfa.MfaParser`
        Autodetected parser for MFA
    """

    annotation_types = [OrthographyTier(MfaParser.word_label, 'word'),
                        OrthographyTier(MfaParser.phone_label, 'phone')]

    annotation_types[0].label = True
    annotation_types[1].label = True
    hierarchy = Hierarchy({'phone': 'word', 'word': None})

    return MfaParser(annotation_types, hierarchy)
