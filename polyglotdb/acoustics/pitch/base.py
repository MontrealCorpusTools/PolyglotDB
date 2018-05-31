import math
from datetime import datetime

from conch import analyze_segments
from conch.analysis.segments import SegmentMapping

from .helper import generate_pitch_function
from ..segments import generate_utterance_segments
from ...exceptions import SpeakerAttributeError
from ..classes import Track, TimePoint

from ..utils import PADDING


def analyze_utterance_pitch(corpus_context, utterance, source='praat', min_pitch=50, max_pitch=500,
                            **kwargs):
    if isinstance(utterance, str):
        utterance_id = utterance
    else:
        utterance_id = utterance.id
    padding = kwargs.pop('padding', None)
    if padding is None:
        padding = PADDING
    utt_type = corpus_context.hierarchy.highest
    statement = '''MATCH (s:Speaker:{corpus_name})-[r:speaks_in]->(d:Discourse:{corpus_name}),
                (u:{utt_type}:{corpus_name})-[:spoken_by]->(s),
                (u)-[:spoken_in]->(d)
                WHERE u.id = {{utterance_id}}
                RETURN u, d, r'''.format(corpus_name=corpus_context.cypher_safe_name, utt_type=utt_type)
    results = corpus_context.execute_cypher(statement, utterance_id=utterance_id)
    segment_mapping = SegmentMapping()
    for r in results:
        channel = r['r']['channel']
        file_path = r['d']['vowel_file_path']
        u = r['u']
        segment_mapping.add_file_segment(file_path, u['begin'], u['end'], channel, padding=padding)

    path = None
    if source == 'praat':
        path = corpus_context.config.praat_path
    elif source == 'reaper':
        path = corpus_context.config.reaper_path
    pitch_function = generate_pitch_function(source, min_pitch, max_pitch, path=path)

    track = Track()
    for seg in segment_mapping:
        output = pitch_function(seg)

        for k, v in output.items():
            if v['F0'] is None or v['F0'] <= 0:
                continue
            p = TimePoint(k)
            p.add_value('F0',  v['F0'])
            track.add(p)
    return track


def update_utterance_pitch_track(corpus_context, utterance, new_track):
    from ...corpus.audio import s_to_ms, to_nano
    if isinstance(utterance, str):
        utterance_id = utterance
    else:
        utterance_id = utterance.id
    today = datetime.utcnow()
    utt_type = corpus_context.hierarchy.highest
    phone_type = corpus_context.hierarchy.lowest
    statement = '''MATCH (s:Speaker:{corpus_name})-[r:speaks_in]->(d:Discourse:{corpus_name}),
                (u:{utt_type}:{corpus_name})-[:spoken_by]->(s),
                (u)-[:spoken_in]->(d),
                (p:{phone_type}:{corpus_name})-[:contained_by*]->(u)
                WHERE u.id = {{utterance_id}}
                SET u.pitch_last_edited = {{date}}
                RETURN u, d, r, s, collect(p) as p'''.format(corpus_name=corpus_context.cypher_safe_name,
                                                             utt_type=utt_type, phone_type=phone_type)
    results = corpus_context.execute_cypher(statement, utterance_id=utterance_id, date=today.timestamp())

    for r in results:
        channel = r['r']['channel']
        discourse = r['d']['name']
        speaker = r['s']['name']
        u = r['u']
        phones = r['p']

    client = corpus_context.acoustic_client()
    query = '''DELETE from "pitch"
                    where "discourse" = '{}' 
                    and "speaker" = '{}' 
                    and "time" >= {} 
                    and "time" <= {};'''.format(discourse, speaker, to_nano(u['begin']), to_nano(u['end']))
    result = client.query(query)

    data = []
    for data_point in new_track:
        speaker, discourse, channel = speaker, discourse, channel
        time_point, value = data_point['time'], data_point['F0']
        t_dict = {'speaker': speaker, 'discourse': discourse, 'channel': channel}
        label = None
        for i, p in enumerate(sorted(phones, key=lambda x: x['begin'])):
            if p['begin'] > time_point:
                break
            label = p['label']
            if i == len(phones) - 1:
                break
        else:
            label = None
        if label is None:
            continue
        fields = {'phone': label}
        try:
            if value is None:
                continue
            value = float(value)
        except TypeError:
            continue
        if value <= 0:
            continue
        fields['F0'] = value
        d = {'measurement': 'pitch',
             'tags': t_dict,
             'time': s_to_ms(time_point),
             'fields': fields
             }
        data.append(d)
    client.write_points(data, batch_size=1000, time_precision='ms')


def analyze_pitch(corpus_context,
                  source='praat',
                  call_back=None,
                  stop_check=None):
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
    absolute_min_pitch = 55
    absolute_max_pitch = 480
    if not 'utterance' in corpus_context.hierarchy:
        raise (Exception('Must encode utterances before pitch can be analyzed'))
    segment_mapping = generate_utterance_segments(corpus_context, padding=PADDING).grouped_mapping('speaker')
    num_speakers = len(segment_mapping)
    algorithm = corpus_context.config.pitch_algorithm
    path = None
    if source == 'praat':
        path = corpus_context.config.praat_path
        # kwargs = {'silence_threshold': 0.03,
        #          'voicing_threshold': 0.45, 'octave_cost': 0.01, 'octave_jump_cost': 0.35,
        #          'voiced_unvoiced_cost': 0.14}
    elif source == 'reaper':
        path = corpus_context.config.reaper_path
        # kwargs = None
    pitch_function = generate_pitch_function(source, absolute_min_pitch, absolute_max_pitch,
                                             path=path)
    if algorithm == 'speaker_adjusted':
        speaker_data = {}
        if call_back is not None:
            call_back('Getting original speaker means and SDs...')
        for i, ((k,), v) in enumerate(segment_mapping.items()):
            if call_back is not None:
                call_back('Analyzing speaker {} ({} of {})'.format(k, i, num_speakers))
            output = analyze_segments(v, pitch_function, stop_check=stop_check)

            sum_pitch = 0
            sum_square_pitch = 0
            n = 0
            for seg, track in output.items():
                for t, v in track.items():
                    v = v['F0']

                    if v is not None and v > 0:  # only voiced frames

                        n += 1
                        sum_pitch += v
                        sum_square_pitch += v * v
            speaker_data[k] = [sum_pitch / n, math.sqrt((n * sum_square_pitch - sum_pitch * sum_pitch) / (n * (n - 1)))]

    for i, ((speaker,), v) in enumerate(segment_mapping.items()):
        if call_back is not None:
            call_back('Analyzing speaker {} ({} of {})'.format(speaker, i, num_speakers))
        if algorithm == 'gendered':
            min_pitch = absolute_min_pitch
            max_pitch = absolute_max_pitch
            try:
                q = corpus_context.query_speakers().filter(corpus_context.speaker.name == speaker)
                q = q.columns(corpus_context.speaker.gender.column_name('Gender'))
                gender = q.all()[0]['Gender']
                if gender is not None:
                    if gender.lower()[0] == 'f':
                        min_pitch = 100
                    else:
                        max_pitch = 400
            except SpeakerAttributeError:
                pass
            pitch_function = generate_pitch_function(source, min_pitch, max_pitch,
                                                     path=path)
        elif algorithm == 'speaker_adjusted':
            mean_pitch, sd_pitch = speaker_data[speaker]
            min_pitch = int(mean_pitch - 3 * sd_pitch)
            max_pitch = int(mean_pitch + 3 * sd_pitch)
            if min_pitch < absolute_min_pitch:
                min_pitch = absolute_min_pitch
            if max_pitch > absolute_max_pitch:
                max_pitch = absolute_max_pitch
            pitch_function = generate_pitch_function(source, min_pitch, max_pitch,
                                                     path=path)
        output = analyze_segments(v, pitch_function, stop_check=stop_check)
        corpus_context.save_pitch_tracks(output, speaker)
        corpus_context.hierarchy.add_token_properties(corpus_context, 'utterance', [('pitch_last_edited', int)])
        corpus_context.encode_hierarchy()
        today = datetime.utcnow()
        corpus_context.query_graph(corpus_context.utterance).set_properties(pitch_last_edited=today.timestamp())
