import tempfile

from conch import analyze_segments
from conch.analysis.segments import SegmentMapping
from conch.analysis.autovot import AutoVOTAnalysisFunction

from ..segments import generate_utterance_segments
from ...exceptions import SpeakerAttributeError
from ..classes import Track, TimePoint
from .helper import convert_to_autovot_wav
from ..utils import PADDING


def analyze_vot(corpus_context,
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
        raise (Exception('Must encode utterances before pitch can be analyzed'))
    segment_mapping = generate_utterance_segments(corpus_context, padding=PADDING).grouped_mapping('speaker')
    number_of_speakers = len(segment_mapping)
    for speaker in segment_mapping:
        vot_func = AutoVOTAnalysisFunction(autovot_binaries_path = "/autovot/autovot/bin/auto_vot_decode.py",\
                classifier_to_use= "/autovot/experiments/models/bb_jasa.classifier")


        with tempfile.TemporaryDirectory() as tmpdirname:
            for seg in segment_mapping[speaker]:
                seg.properties["vot_marks"] = [(0, 0.1)]
                tmpfilename = "{}/{}".format(tmpdirname, seg.file_path)
                convert_to_autovot_wav(seg.file_path, tmpfilename)
                seg.file_path = tmpfilename
            output = analyze_segments(segment_mapping[speaker], vot_func, stop_check=stop_check, multiprocessing=multiprocessing)
        print(output)
