import tempfile

from conch import analyze_segments
from conch.analysis.segments import SegmentMapping, FileSegment
from conch.analysis.autovot import AutoVOTAnalysisFunction

from ..segments import generate_utterance_segments, generate_segments
from ...query.annotations.models import LinguisticAnnotation
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
            seg = FileSegment(sf["consonant_file_path"], sf["speech_begin"], sf["speech_end"], name=discourse)
            seg.properties["vot_marks"] = [(x["begin"], x["end"]) for x in stop_mapping[(discourse,)]]
            segment_mapping.segments.append(seg)

    output = analyze_segments(segment_mapping, vot_func, stop_check=stop_check, multiprocessing=multiprocessing)
    print(dir(output))
    #NOTE: possible that autovot conch integration doesn't check if nothing is returned for a given segment, 
    # do something to make sure len(output)==len(segment_mapping) in conch
    corpus_context.hierarchy.add_subannotation_type(corpus_context, "phone", "vot", properties=[("begin", float), ("end",float)])
    for discourse, discourse_output in output.items():
        #OUTPUT is not veing saved but vot_mark
        for (begin, end), stop in zip(discourse_output, stop_mapping[(discourse["name"], )]):
            model = LinguisticAnnotation(corpus_context)
            model.load(stop["id"])
            model.add_subannotation("vot", begin=begin, end=end)
            model.save()
