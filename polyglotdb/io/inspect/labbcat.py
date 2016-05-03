
from polyglotdb.structure import Hierarchy

from ..types.parsing import *

from ..parsers import LabbCatParser


def inspect_labbcat(path):

    annotation_types = [OrthographyTier('transcrip', 'word'),
                            OrthographyTier('segment', 'phone')]

    annotation_types[0].label = True
    annotation_types[1].label = True
    hierarchy = Hierarchy({'phone': 'word', 'word': None})

    return LabbCatParser(annotation_types, hierarchy)
