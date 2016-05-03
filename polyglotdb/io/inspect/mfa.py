
from polyglotdb.structure import Hierarchy

from ..types.parsing import *

from ..parsers import MfaParser

def inspect_mfa(path):

    annotation_types = [OrthographyTier('words', 'word'),
                            OrthographyTier('phones', 'phone')]

    annotation_types[0].label = True
    annotation_types[1].label = True
    hierarchy = Hierarchy({'phone': 'word', 'word': None})

    return MfaParser(annotation_types, hierarchy)
