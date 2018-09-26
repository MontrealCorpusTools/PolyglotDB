import tempfile

from conch import analyze_segments
from conch.analysis.segments import SegmentMapping
from conch.analysis.autovot import AutoVOTAnalysisFunction

from ..segments import generate_utterance_segments, generate_segments
from ...exceptions import SpeakerAttributeError
from ..classes import Track, TimePoint
from .helper import convert_to_autovot_wav
from ..utils import PADDING


def analyze_vot(corpus_context,
                  stop_label='stops',
                  call_back=None,
                  stop_check=None, multiprocessing=False):
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
        raise (Exception('Must encode utterances before VOT can be analyzed'))
    if not corpus_context.hierarchy.has_type_subset('phone', stop_label):
        raise Exception('Phones do not have a "{}" subset.'.format(stop_label))
    segment_mapping = generate_utterance_segments(corpus_context, padding=PADDING, file_type="consonant").grouped_mapping('speaker')
    #TODO: for some strange reason the keys are ("utterance_id",) not just "utterance_id", probably should be fixed
    stop_mapping = generate_segments(corpus_context, annotation_type='phone', subset='stops', padding=PADDING, file_type="consonant").grouped_mapping('utterance_id')
    number_of_speakers = len(segment_mapping)
    for speaker in segment_mapping:
        vot_func = AutoVOTAnalysisFunction(autovot_binaries_path = corpus_context.config.autovot_path ,\
                classifier_to_use= "/autovot/experiments/models/bb_jasa.classifier")
        for seg in segment_mapping[speaker]:
            if (seg["utterance_id"],) in stop_mapping:
                seg.properties["vot_marks"] = [(x["begin"], x["end"]) for x in stop_mapping[(seg["utterance_id"],)]]
            else:
                seg.properties["vot_marks"] = []
        output = analyze_segments(segment_mapping[speaker], vot_func, stop_check=stop_check, multiprocessing=multiprocessing)
