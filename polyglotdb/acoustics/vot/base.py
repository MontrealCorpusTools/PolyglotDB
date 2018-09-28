import tempfile

from conch import analyze_segments
from conch.analysis.segments import SegmentMapping, FileSegment
from conch.analysis.autovot import AutoVOTAnalysisFunction

from ..segments import generate_utterance_segments, generate_segments
from ...exceptions import SpeakerAttributeError
from ..classes import Track, TimePoint
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
    if not corpus_context.hierarchy.has_type_subset('phone', stop_label):
        raise Exception('Phones do not have a "{}" subset.'.format(stop_label))
    stop_mapping = generate_segments(corpus_context, annotation_type='phone', subset='stops', padding=PADDING, file_type="consonant").grouped_mapping('discourse')
    segment_mapping = SegmentMapping()
    vot_func = AutoVOTAnalysisFunction(autovot_binaries_path = corpus_context.config.autovot_path ,\
            classifier_to_use= "/autovot/experiments/models/bb_jasa.classifier")
    for discourse in corpus_context.discourses:
        if (discourse,) in stop_mapping:
            sf = corpus_context.discourse_sound_file(discourse)
            seg = FileSegment(sf["consonant_file_path"], sf["speech_begin"], sf["speech_end"])
            seg.properties["vot_marks"] = [(x["begin"], x["end"]) for x in stop_mapping[(discourse,)]]
            segment_mapping.segments.append(seg)

    output = analyze_segments(segment_mapping, vot_func, stop_check=stop_check, multiprocessing=multiprocessing)