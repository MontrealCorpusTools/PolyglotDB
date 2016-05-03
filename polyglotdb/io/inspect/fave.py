
from polyglotdb.structure import Hierarchy

from ..types.parsing import *

from ..parsers import FaveParser

def inspect_fave(path):

    annotation_types = [OrthographyTier('word', 'word'),
                            OrthographyTier('phone', 'phone')]

    annotation_types[0].label = True
    annotation_types[1].label = True
    hierarchy = Hierarchy({'phone': 'word', 'word': None})

    return FaveParser(annotation_types, hierarchy)
