from polyglotdb.structure import Hierarchy

from ..types.parsing import SegmentTier, OrthographyTier

from ..parsers.timit import TimitParser


def inspect_timit(word_path):
    """
    Generate a :class:`~polyglotdb.io.parsers.timit.TimitParser`.

    Parameters
    ----------
    word_path : str
        Full path to text file

    Returns
    -------
    :class:`~polyglotdb.io.parsers.timit.TimitParser`
        Auto-detected parser for TIMIT
    """
    annotation_types = [OrthographyTier('word', 'word'),
                        SegmentTier('phone', 'phone')]
    hierarchy = Hierarchy({'phone': 'word', 'word': None})
    return TimitParser(annotation_types, hierarchy)
