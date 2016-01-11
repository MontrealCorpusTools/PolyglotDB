

from ..types.parsing import *

from ..parsers import BuckeyeParser

def inspect_buckeye(word_path):
    """
    Generate a list of AnnotationTypes for the Buckeye corpus

    Parameters
    ----------
    word_path : str
        Full path to text file

    Returns
    -------
    list of AnnotationTypes
        Auto-detected AnnotationTypes for the Buckeye corpus
    """
    annotation_types = [OrthographyTier('word', 'word'),
                            TranscriptionTier('transcription', 'word'),
                            OrthographyTier('category', 'word'),
                            SegmentTier('surface_transcription', 'surface_transcription')]
    annotation_types[1].trans_delimiter = ' '
    annotation_types[-1].type_property = False
    hierarchy = {'surface_transcription': 'word', 'word': None}

    return BuckeyeParser(annotation_types, hierarchy, make_transcription = False)
