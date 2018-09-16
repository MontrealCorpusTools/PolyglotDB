import math
from datetime import datetime

from conch import analyze_segments
from conch.analysis.segments import SegmentMapping

from ..segments import generate_utterance_segments
from ...exceptions import SpeakerAttributeError
from ..classes import Track, TimePoint

from ..utils import PADDING


def analyze_vot(corpus_context,
                  source='praat',
                  call_back=None,
                  stop_check=None, multiprocessing=True):
    """

    Parameters
    ----------
    corpus_context : :class:`~polyglotdb.CorpusContext`
    source
    call_back
    stop_check

    Returns
    -------

    """
    if not 'utterance' in corpus_context.hierarchy:
        raise (Exception('Must encode utterances before pitch can be analyzed'))
    segment_mapping = generate_utterance_segments(corpus_context, padding=PADDING).grouped_mapping('speaker')
    num_speakers = len(segment_mapping)
    print(segment_mapping)
