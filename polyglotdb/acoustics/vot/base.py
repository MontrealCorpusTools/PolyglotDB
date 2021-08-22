
from uuid import uuid1
from conch import analyze_segments
from conch.analysis.segments import SegmentMapping
from conch.analysis.autovot import AutoVOTAnalysisFunction

from ..segments import generate_segments
from ..utils import PADDING


def get_default_for_type(t):
    if t == float:
        return 0.0
    elif t == str:
        return ""
    elif t == int:
        return 0
    elif t == bool:
        return False
    return None


def analyze_vot(corpus_context, classifier, stop_label='stops',
                  vot_min=5,
                  vot_max=100,
                  window_min=-30,
                  window_max=30,
                  overwrite_edited=False,
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
    overwrite_edited:
        Whether to updated VOTs which have the property, edited set to True
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
                    if "vot" in x["subannotations"]:
                        vot = x["subannotations"]["vot"]
                    else:
                        vot = None 

                    if vot is not None:
                        #Skip "edited" vots unless we're given the go-ahead to overwrite them
                        if not overwrite_edited and hasattr(vot, "edited") and vot.edited:
                            continue

                        stop_info = (x["begin"], x["end"], x["id"], x["subannotations"]["vot"].id)
                    else:
                        stop_info = (x["begin"], x["end"], x["id"], "new_vot")
                else:
                    stop_info = (x["begin"], x["end"], x["id"])

                if x["speaker"] in speaker_mapped_stops:
                    speaker_mapped_stops[x["speaker"]].append(stop_info)
                else:
                    speaker_mapped_stops[x["speaker"]] = [stop_info]
            for speaker in speaker_mapped_stops:
                channel = corpus_context.get_channel_of_speaker(speaker, discourse)
                segment_mapping.add_file_segment(sf["consonant_file_path"],
                        0, sf["duration"], channel,
                        name="{}-{}".format(speaker, discourse), vot_marks=speaker_mapped_stops[speaker])
    output = analyze_segments(segment_mapping.segments, vot_func, stop_check=stop_check, multiprocessing=multiprocessing)


    if already_encoded_vots:
        new_data = []
        updated_data = []
        custom_props = [(prop, get_default_for_type(val)) for prop, val in corpus_context.hierarchy.subannotation_properties["vot"] \
                if prop not in ["begin", "id", "end", "confidence"]]
        all_props = [x[0] for x in custom_props]+["id", "begin", "end", "confidence"]

        for discourse, discourse_output in output.items():
            for (begin, end, confidence, stop_id, vot_id) in discourse_output:
                if vot_id == "new_vot":
                    props = {"id":str(uuid1()),
                             "begin":begin,
                             "end":begin+end,
                             "annotated_id":stop_id,
                             "confidence":confidence}
                    for prop, val in custom_props:
                        props[prop] = val
                    new_data.append(props)
                else:
                    props = {"id":vot_id,
                             "props":{"begin":begin,
                                 "end":begin+end,
                                 "confidence":confidence}}
                    for prop, val in custom_props:
                        props["props"][prop] = val
                    updated_data.append(props)
        if updated_data:
            statement = """
            UNWIND {{data}} as d
            MERGE (n:vot:{corpus_name} {{id: d.id}})
            SET n += d.props
            """.format(corpus_name=corpus_context.cypher_safe_name)
            corpus_context.execute_cypher(statement, data=updated_data)

        if new_data:
            default_node = ", ".join(["{}: d.{}".format(p, p) for p in all_props])
            statement = """
            UNWIND {{data}} as d
            MATCH (annotated:phone:{corpus_name} {{id: d.annotated_id}})
            CREATE (annotated) <-[:annotates]-(annotation:vot:{corpus_name}
                {{{default_node}}})
            """.format(corpus_name=corpus_context.cypher_safe_name, default_node=default_node)
            corpus_context.execute_cypher(statement, data=new_data)
    else:
        list_of_stops = []
        property_types = [("begin", float), ("end", float), ("confidence", float)]
        for discourse, discourse_output in output.items():
            for (begin, end, confidence, stop_id) in discourse_output:
                list_of_stops.append({"begin":begin,
                                      "end":begin+end,
                                      "id":uuid1(),
                                      "confidence":confidence,
                                      "annotated_id":stop_id})

        corpus_context.import_subannotations(list_of_stops, property_types, "vot", "phone")
