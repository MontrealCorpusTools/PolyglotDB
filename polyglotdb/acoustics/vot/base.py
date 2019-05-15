import tempfile

from uuid import uuid1
from conch import analyze_segments
from conch.analysis.segments import SegmentMapping, FileSegment
from conch.analysis.autovot import AutoVOTAnalysisFunction

from ..segments import generate_utterance_segments, generate_segments
from ...query.annotations.models import LinguisticAnnotation
from ...exceptions import SpeakerAttributeError
from ..classes import Track, TimePoint
from ..utils import PADDING


def analyze_vot(corpus_context, classifier, stop_label='stops',
                  vot_min=5,
                  vot_max=100,
                  window_min=-30,
                  window_max=30,
                  call_back=None,
                  stop_check=None, multiprocessing=False):
    """
    Analyze VOT for stops using a pretrained AutoVOT classifier.

    Parameters
    ----------
    corpus_context : :class:`~polyglotdb.corpus.AudioContext`
    classifier : str
        Path to an AutoVOT classifier model
    stop_label : str
        Label of subset to analyze
    vot_min : int
        Minimum VOT in ms
    vot_max : int
        Maximum VOT in ms
    window_min : int
        Window minimum in ms
    window_max : int
        Window maximum in Ms
    call_back : callable
        call back function, optional
    stop_check : callable
        stop check function, optional
    multiprocessing : bool
        Flag to use multiprocessing, otherwise will use threading
    """
    if not corpus_context.hierarchy.has_token_subset('phone', stop_label) and not corpus_context.hierarchy.has_type_subset('phone', stop_label):
        raise Exception('Phones do not have a "{}" subset.'.format(stop_label))

    already_encoded_vots = corpus_context.hierarchy.has_subannotation_type("vot")

    stop_mapping = generate_segments(corpus_context, annotation_type='phone', subset=stop_label, padding=PADDING, file_type="consonant", fetch_subannotations=True).grouped_mapping('discourse')
    segment_mapping = SegmentMapping()
    vot_func = AutoVOTAnalysisFunction(classifier_to_use=classifier,
            min_vot_length=vot_min,
            max_vot_length=vot_max,
            window_min=window_min,
            window_max=window_max
            )
    for discourse in corpus_context.discourses:
        if (discourse,) in stop_mapping:
            sf = corpus_context.discourse_sound_file(discourse)
            speaker_mapped_stops = {}
            for x in stop_mapping[(discourse,)]:
                if already_encoded_vots:
                    if has_vot:
                        stop_info = (x["begin"], x["end"], x["id"], x["subannotations"]["vot"]["id"])
                    else:
                        stop_info = (x["begin"], x["end"], x["id"], "new_vot")
                else:
                    stop_info = (x["begin"], x["end"], x["id"])
                if x["speaker"] in speaker_mapped_stops:
                    speaker_mapped_stops[x["speaker"]].append(stop_info)
                else:
                    speaker_mapped_stops[x["speaker"]] = [stop_info]
            for speaker in speaker_mapped_stops:
                segment_mapping.add_file_segment(sf["consonant_file_path"], \
                        sf["speech_begin"], sf["speech_end"], sf["channel"],\
                        name="{}-{}".format(speaker, discourse), vot_marks=speaker_mapped_stops[speaker])
    output = analyze_segments(segment_mapping.segments, vot_func, stop_check=stop_check, multiprocessing=multiprocessing)


    list_of_stops = []
    property_types = [("begin", float), ("end", float), ("confidence", float)]
    if already_encoded_vots:
        new_data = []
        updated_data = []
        for discourse, discourse_output in output.items():
            for (begin, end, confidence, stop_id, vot_id) in discourse_output:
                if vot_id == "new_vot":
                    new_data.append({"id":uuid1(),
                                     "begin":begin,
                                     "end":begin+end,
                                     "annotated_id":stop_id
                                     "confidence":confidence})
                else:
                    updated_data.append({"id":vot_id,
                                         "props":{"begin":begin,
                                             "end":begin+end,
                                             "confidence":confidence}})
        if updated_data:
            statement = """
            MATCH (n:{subannotation}:{corpus_name})
            SET n.{prop} = {default}
            """.format(subannotation=subannotation, corpus_name=c.cypher_safe_name, 
                    prop=prop, default=default)
            c.execute_cypher(statement)
        if new_data:
            #CREATE VOTs
            c.execute_cypher(statement)
    else:
        for discourse, discourse_output in output.items():
            for (begin, end, confidence, stop_id) in discourse_output:
                list_of_stops.append({"begin":begin,
                                      "end":begin+end,
                                      "id":uuid1(),
                                      "confidence":confidence,
                                      "annotated_id":stop_id})

        corpus_context.import_subannotations(list_of_stops, property_types, "vot", "phone")
