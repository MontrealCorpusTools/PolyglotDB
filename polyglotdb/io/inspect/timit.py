
from ..types.parsing import SegmentTier, OrthographyTier

from ..parsers.timit import TimitParser

def inspect_timit(word_path):
    """
    Generate a list of AnnotationTypes for TIMIT

    Parameters
    ----------
    word_path : str
        Full path to text file

    Returns
    -------
    list of AnnotationTypes
        Auto-detected AnnotationTypes for TIMIT
    """
    annotation_types = [OrthographyTier('word', 'word'),
                       SegmentTier('surface_transcription', 'surface_transcription')]
    hierarchy = {'surface_transcription':'word', 'word': None}
    return TimitParser(annotation_types, hierarchy)
