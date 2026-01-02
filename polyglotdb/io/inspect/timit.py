from polyglotdb.io.parsers.timit import TimitParser
from polyglotdb.io.types.parsing import OrthographyTier, SegmentTier
from polyglotdb.structure import Hierarchy


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
    annotation_types = [OrthographyTier("word", "word"), SegmentTier("phone", "phone")]
    hierarchy = Hierarchy({"phone": "word", "word": None})
    return TimitParser(annotation_types, hierarchy)
