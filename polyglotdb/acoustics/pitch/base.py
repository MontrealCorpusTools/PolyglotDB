import math

from conch import analyze_segments
from conch.analysis.segments import SegmentMapping

from .helper import generate_pitch_function
from ..segments import generate_utterance_segments
from ...exceptions import SpeakerAttributeError

from ..utils import PADDING


def analyze_discourse_pitch(corpus_context, discourse, source='praat', min_pitch=50, max_pitch=500, with_pulses=False, **kwargs):
    print(kwargs)
    padding = kwargs.pop('padding', None)
    if padding is None:
        padding = PADDING
    statement = '''MATCH (s:Speaker:{corpus_name})-[r:speaks_in]->(d:Discourse:{corpus_name})
                WHERE d.name = {{discourse_name}}
                RETURN d, s, r'''.format(corpus_name=corpus_context.cypher_safe_name)
    results = corpus_context.execute_cypher(statement, discourse_name=discourse)
    segment_mapping = SegmentMapping()
    segment_to_speaker = {}
    for r in results:
        channel = r['r']['channel']
        speaker = r['s']['name']

        discourse = r['d']['name']
        file_path = r['d']['vowel_file_path']
        atype = corpus_context.hierarchy.highest
        prob_utt = getattr(corpus_context, atype)
        q = corpus_context.query_graph(prob_utt)
        q = q.filter(prob_utt.discourse.name == discourse)
        q = q.filter(prob_utt.speaker.name == speaker)
        utterances = q.all()
        for u in utterances:
            segment_mapping.add_file_segment(file_path, u.begin, u.end, channel, padding=padding)
            segment_to_speaker[segment_mapping[-1]] = speaker
    print(segment_mapping.segments)
    path = None
    if source == 'praat':
        path = corpus_context.config.praat_path
        # kwargs = {'silence_threshold': 0.03,
        #          'voicing_threshold': 0.45, 'octave_cost': 0.01, 'octave_jump_cost': 0.35,
        #          'voiced_unvoiced_cost': 0.14}
    elif source == 'reaper':
        path = corpus_context.config.reaper_path
    pitch_function = generate_pitch_function(source, min_pitch, max_pitch, path=path, with_pulses=with_pulses)
    track = []
    pulses = []
    for seg in segment_mapping:
        output = pitch_function(seg)
        if pulses:
            output, p = output
            pulses.extend(p)

        for k, v in output.items():
            track.append({'time': k, 'F0':v['F0'], 'speaker':segment_to_speaker[seg], 'channel':seg.channel, 'discourse':discourse})
    track = sorted(track, key=lambda x: x['time'])
    if pulses:
        return track, sorted(pulses)
    return track

def update_pitch_track(corpus_context, new_track):
    pass

def analyze_pitch(corpus_context,
                  source='praat',
                  call_back=None,
                  stop_check=None):
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
        for i, (k, v) in enumerate(segment_mapping.items()):
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

    for i, (speaker, v) in enumerate(segment_mapping.items()):
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
