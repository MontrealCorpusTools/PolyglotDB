import os
import re
import librosa
from datetime import datetime
from decimal import Decimal

from influxdb import InfluxDBClient

from polyglotdb.query.discourse import DiscourseInspector
from ..acoustics import analyze_pitch, analyze_formant_tracks, analyze_vowel_formant_tracks, analyze_intensity, \
    analyze_script, analyze_utterance_pitch, update_utterance_pitch_track, analyze_vot
from ..acoustics.classes import Track, TimePoint
from .syllabic import SyllabicContext

from ..acoustics.utils import load_waveform, generate_spectrogram


def sanitize_formants(value):
    try:
        f1 = value['F1'][0]
    except TypeError:
        f1 = value['F1']
    if f1 is None:
        f1 = 0
    try:
        f2 = value['F2'][0]
    except TypeError:
        f2 = value['F2']
    if f2 is None:
        f2 = 0
    try:
        f3 = value['F3'][0]
    except TypeError:
        f3 = value['F3']
    if f3 is None:
        f3 = 0
    return float(f1), float(f2), float(f3)


def generate_filter_string(discourse, begin, end, channel, num_points, kwargs):
    extra_filters = ['''"{}" = '{}' '''.format(k, v) for k, v in kwargs.items()]
    filter_string = '''WHERE "discourse" = '{}'
                            AND "time" >= {}
                            AND "time" <= {}
                            AND "channel" = '{}'
                            '''
    if extra_filters:
        filter_string += '\nAND {}'.format('\nAND '.join(extra_filters))
    if num_points:
        duration = end - begin
        time_step = duration / (num_points - 1)
        begin -= time_step / 2
        end += time_step / 2
        time_step *= 1000
        filter_string += '\ngroup by time({}ms) fill(null)'.format(int(time_step))
    filter_string = filter_string.format(discourse, to_nano(begin), to_nano(end), channel)
    return filter_string


def to_nano(seconds):
    if not isinstance(seconds, Decimal):
        seconds = Decimal(seconds).quantize(Decimal('0.001'))
    return int(seconds * Decimal('1e9'))


def s_to_ms(seconds):
    if not isinstance(seconds, Decimal):
        seconds = Decimal(seconds).quantize(Decimal('0.001'))
    return int(seconds * Decimal('1e3'))


def to_seconds(time_string):
    try:
        d = datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%S.%fZ')
        s = 60 * 60 * d.hour + 60 * d.minute + d.second + d.microsecond / 1e6
    except:
        try:
            d = datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%SZ')
            s = 60 * 60 * d.hour + 60 * d.minute + d.second + d.microsecond / 1e6
        except:
            m = re.search('T(\d{2}):(\d{2}):(\d+)\.(\d+)?', time_string)
            p = m.groups()

            s = 60 * 60 * int(p[0]) + 60 * int(p[1]) + int(p[2]) + int(p[3][:6]) / 1e6

    s = Decimal(s).quantize(Decimal('0.001'))
    return s


class AudioContext(SyllabicContext):
    """
    Class that contains methods for dealing with audio files for corpora
    """

    def load_audio(self, discourse, file_type):
        sound_file = self.discourse_sound_file(discourse)
        if file_type == 'consonant':
            path = os.path.expanduser(sound_file.consonant_file_path)
        elif file_type == 'vowel':
            path = os.path.expanduser(sound_file.vowel_file_path)
        elif file_type == 'low_freq':
            path = os.path.expanduser(sound_file.low_freq_file_path)
        else:
            path = os.path.expanduser(sound_file.file_path)
        signal, sr = librosa.load(path, sr=None)
        return signal, sr

    def analyze_pitch(self, source='praat', stop_check=None, call_back=None, multiprocessing=True):
        analyze_pitch(self, source, stop_check, call_back, multiprocessing=multiprocessing)

    def analyze_utterance_pitch(self, utterance, source='praat', **kwargs):
        return analyze_utterance_pitch(self, utterance, source, **kwargs)

    def update_utterance_pitch_track(self, utterance, new_track):
        return update_utterance_pitch_track(self, utterance, new_track)

    def analyze_vot(self,
            stop_label="stops",
            stop_check=None,
            call_back=None,
            multiprocessing=False,
            classifier="/autovot/experiments/models/bb_jasa.classifier",
            vot_min=5,
            vot_max=100,
            window_min=-30,
            window_max=30):
        analyze_vot(self, stop_label=stop_label, stop_check=stop_check,\
                call_back=call_back, multiprocessing=multiprocessing,\
                vot_min=vot_min, vot_max=vot_max, window_min=window_min,\
                window_max=window_max, classifier=classifier)

    def analyze_formant_tracks(self, source='praat', stop_check=None, call_back=None, multiprocessing=True):
        analyze_formant_tracks(self, source, stop_check, call_back, multiprocessing=multiprocessing)

    def analyze_vowel_formant_tracks(self, source='praat', stop_check=None, call_back=None, vowel_label='vowel',
                                     multiprocessing=True):
        analyze_vowel_formant_tracks(self, source, stop_check, call_back, vowel_label,
                                     multiprocessing=multiprocessing)

    def analyze_intensity(self, source='praat', stop_check=None, call_back=None, multiprocessing=True):
        analyze_intensity(self, source, stop_check, call_back, multiprocessing=multiprocessing)

    def analyze_script(self, phone_class, script_path, duration_threshold=0.01, arguments=None, stop_check=None,
                       call_back=None, multiprocessing=True):
        analyze_script(self, phone_class, script_path, duration_threshold=duration_threshold, arguments=arguments,
                       stop_check=stop_check, call_back=call_back, multiprocessing=multiprocessing)

    def genders(self):
        res = self.execute_cypher(
            '''MATCH (s:Speaker:{corpus_name}) RETURN s.gender as gender'''.format(corpus_name=self.cypher_safe_name))
        genders = set()
        for s in res:
            g = s['gender']
            if g is None:
                g = ''
            genders.add(g)
        return sorted(genders)

    def reset_acoustics(self, call_back=None, stop_check=None):
        self.acoustic_client().drop_database(self.corpus_name)
        if self.hierarchy.acoustics:
            self.hierarchy.acoustics = set()
            self.encode_hierarchy()

    def reset_pitch(self):
        self.acoustic_client().query('''DROP MEASUREMENT "pitch";''')
        if 'pitch' in self.hierarchy.acoustics:
            self.hierarchy.acoustics.remove('pitch')
            self.encode_hierarchy()

    def reset_formants(self):
        self.acoustic_client().query('''DROP MEASUREMENT "formants";''')
        if 'formants' in self.hierarchy.acoustics:
            self.hierarchy.acoustics.remove('formants')
            self.encode_hierarchy()

    def reset_intensity(self):
        self.acoustic_client().query('''DROP MEASUREMENT "intensity";''')
        if 'intensity' in self.hierarchy.acoustics:
            self.hierarchy.acoustics.remove('intensity')
            self.encode_hierarchy()

    def acoustic_client(self):
        client = InfluxDBClient(**self.config.acoustic_conncetion_kwargs)
        databases = client.get_list_database()
        if self.corpus_name not in databases:
            client.create_database(self.corpus_name)
        return client

    def inspect_discourse(self, discourse, begin=None, end=None):
        """
        Get a discourse inspecter object for a discourse

        Parameters
        ----------
        discourse : str
            Name of the discourse
        begin : float, optional
            Beginning of the initial cache
        end : float, optional
            End of the initial cache

        Returns
        -------
        :class:`~polyglotdb.graph.discourse.DiscourseInspector`
            DiscourseInspector for the specified discourse
        """
        return DiscourseInspector(self, discourse, begin, end)

    def load_waveform(self, discourse, file_type='consonant', begin=None, end=None):
        sf = self.discourse_sound_file(discourse)
        if file_type == 'consonant':
            file_path = sf['consonant_file_path']
        elif file_type == 'vowel':
            file_path = sf['vowel_file_path']
        elif file_type == 'low_freq':
            file_path = sf['low_freq_file_path']
        else:
            file_path = sf['file_path']
        return load_waveform(file_path, begin, end)

    def generate_spectrogram(self, discourse, file_type='consonant', begin=None, end=None):
        signal, sr = self.load_waveform(discourse, file_type, begin, end)
        return generate_spectrogram(signal, sr)

    def discourse_audio_directory(self, discourse):
        """
        Return the directory for the stored audio files for a discourse
        """
        return os.path.join(self.config.audio_dir, discourse)

    def discourse_sound_file(self, discourse):
        statement = '''MATCH (d:Discourse:{corpus_name}) WHERE d.name = {{discourse_name}} return d'''.format(
            corpus_name=self.cypher_safe_name)
        results = self.execute_cypher(statement, discourse_name=discourse).records()
        for r in results:
            d = r['d']
            break
        else:
            raise Exception('Could not find discourse {}'.format(discourse))
        return d

    def utterance_sound_file(self, utterance_id, type='consonant'):
        q = self.query_graph(self.utterance).filter(self.utterance.id == utterance_id).columns(
            self.utterance.begin.column_name('begin'),
            self.utterance.end.column_name('end'),
            self.utterance.discourse.name.column_name('discourse'))
        utterance_info = q.all()[0]
        path = os.path.join(self.discourse_audio_directory(utterance_info['discourse']),
                            '{}_{}.wav'.format(utterance_id, type))
        if os.path.exists(path):
            return path
        fname = self.discourse_sound_file(utterance_info['discourse'])["consonant_file_path"]
        data, sr = librosa.load(fname, sr=None, offset=utterance_info['begin'],
                                duration=utterance_info['end'] - utterance_info['begin'])
        librosa.output.write_wav(path, data, sr)
        return path

    def has_all_sound_files(self):
        """
        Check whether all discourses have a sound file

        Returns
        -------
        bool
            True if a sound file exists for each discourse name in corpus,
            False otherwise
        """
        if self._has_all_sound_files is not None:
            return self._has_all_sound_files
        discourses = self.discourses
        for d in discourses:
            sf = self.discourse_sound_file(d)
            if sf is None:
                break
            if not os.path.exists(sf.file_path):
                break
        else:
            self._has_all_sound_files = True
        self._has_all_sound_files = False
        return self._has_all_sound_files

    @property
    def has_sound_files(self):
        """
        Check whether any discourses have a sound file

        Returns
        -------
        bool
            True if there are any sound files at all, false if there aren't
        """

        if self._has_sound_files is None:
            self._has_sound_files = False
            for d in self.discourses:
                sf = self.discourse_sound_file(d)
                if sf['file_path'] is not None:
                    self._has_sound_files = True
                    break
        return self._has_sound_files

    def get_utterance_intensity(self, utterance_id, discourse, speaker):
        client = self.acoustic_client()
        Intensity_name = "Intensity"
        rel_name = Intensity_name + '_relativized'

        columns = '"time", "{}", "{}"'.format(Intensity_name, rel_name)
        query = '''select {} from "intensity"
                        WHERE "utterance_id" = '{}'
                        AND "discourse" = '{}'
                        AND "speaker" = '{}';'''.format(columns, utterance_id, discourse, speaker)
        result = client.query(query)
        track = Track()
        for r in result.get_points('intensity'):
            s = to_seconds(r['time'])
            p = TimePoint(s)
            p.add_value(Intensity_name, r[Intensity_name])
            p.add_value(rel_name, r[rel_name])
            track.add(p)
        return track

    def get_intensity(self, discourse, begin, end, channel=0, relative=False, relative_time=False, **kwargs):
        """
        Get intensity for a given discourse and time range

        Parameters
        ----------
        discourse : str
            Name of the discourse
        begin : float
            Beginning of time range
        end : float
            End of time range
        relative : bool
            Flag for retrieving relative intensity instead of absolute intensity
        relative_time : bool
            Flag for retrieving relative time instead of absolute time
        kwargs : kwargs
            Tags to filter on

        Returns
        -------
        list
            List of results with fields for ``time`` and ``intensity``
        """
        begin = Decimal(begin).quantize(Decimal('0.001'))
        end = Decimal(end).quantize(Decimal('0.001'))
        num_points = kwargs.pop('num_points', 0)
        filter_string = generate_filter_string(discourse, begin, end, channel, num_points, kwargs)
        client = self.acoustic_client()
        Intensity_name = "Intensity"
        if relative:
            Intensity_name += '_relativized'
        if num_points:
            columns = 'mean("{}")'.format(Intensity_name)
        else:
            columns = '"time", "{}"'.format(Intensity_name)
        query = '''select {} from "intensity"
                        {};'''.format(columns, filter_string)
        result = client.query(query)
        track = Track()
        for r in result.get_points('intensity'):
            s = to_seconds(r['time'])
            if relative_time:
                s = (s - begin) / (end - begin)
            p = TimePoint(s)
            p.add_value("Intensity", r[Intensity_name])
            track.add(p)
        return track

    def get_utterance_formants(self, utterance_id, discourse, speaker):
        client = self.acoustic_client()
        formant_names = ["F1", "F2", "F3", "B1", "B2", "B3"]
        columns = '"time", {}'.format(', '.join('"{0}", "{0}_relativized"'.format(x) for x in formant_names))
        result = client.query('''select {} from "formants"
                        WHERE "utterance_id" = '{}'
                        AND "discourse" = '{}'
                        AND "speaker" = '{}';'''.format(columns, utterance_id, discourse, speaker))
        track = Track()
        for r in result.get_points('formants'):
            s = to_seconds(r['time'])
            p = TimePoint(s)
            for f in formant_names:
                rel_name = f + '_relativized'
                p.add_value(f, r[f])
                p.add_value(rel_name, r[rel_name])
            track.add(p)
        return track

    def get_formants(self, discourse, begin, end, channel=0, relative=False, relative_time=False, **kwargs):
        """
        Get formants for a given discourse and time range

        Parameters
        ----------
        discourse : str
            Name of the discourse
        begin : float
            Beginning of time range
        end : float
            End of time range
        relative : bool
            Flag for retrieving relative formants instead of absolute formants
        relative_time : bool
            Flag for retrieving relative time instead of absolute time
        kwargs : kwargs
            Tags to filter on

        Returns
        -------
        list
            List of results with fields for ``time``, ``F1``, ``F2``, and ``F3``
        """
        begin = Decimal(begin).quantize(Decimal('0.001'))
        end = Decimal(end).quantize(Decimal('0.001'))
        num_points = kwargs.pop('num_points', 0)
        filter_string = generate_filter_string(discourse, begin, end, channel, num_points, kwargs)
        client = self.acoustic_client()
        formant_names = ["F1", "F2", "F3", "B1", "B2", "B3"]
        if relative:
            for i in range(6):
                formant_names[i] += '_relativized'
        if num_points:
            columns = ', '.join('mean("{}")'.format(x) for x in formant_names)
        else:
            columns = '"time", {}'.format(', '.join('"{}"'.format(x) for x in formant_names))
        result = client.query('''select {} from "formants"
                        {};'''.format(columns, filter_string))
        track = Track()
        for r in result.get_points('formants'):
            s = to_seconds(r['time'])
            if relative_time:
                s = (s - begin) / (end - begin)
            p = TimePoint(s)
            for f in formant_names:
                p.add_value(f.split('_')[0], r[f])
            track.add(p)
        return track

    def get_utterance_pitch(self, utterance_id, discourse, speaker):
        client = self.acoustic_client()
        F0_name = "F0"
        rel_name = "F0_relativized"

        columns = '"time", "{}", "{}"'.format(F0_name, rel_name)
        query = '''select {} from "pitch"
                        WHERE "utterance_id" = '{}'
                        AND "discourse" = '{}'
                        AND "speaker" = '{}';'''.format(columns, utterance_id, discourse, speaker)
        result = client.query(query)
        track = Track()
        for r in result.get_points('pitch'):
            s = to_seconds(r['time'])
            p = TimePoint(s)
            p.add_value(F0_name, r[F0_name])
            p.add_value(rel_name, r[rel_name])
            track.add(p)
        return track

    def get_pitch(self, discourse, begin, end, channel=0, relative=False, relative_time=False, **kwargs):
        """
        Get pitch for a given discourse and time range

        Parameters
        ----------
        discourse : str
            Name of the discourse
        begin : float
            Beginning of time range
        end : float
            End of time range
        channel : int
            Channel of track
        relative : bool
            Flag for retrieving relative pitch instead of absolute pitch
        relative_time : bool
            Flag for retrieving relative time instead of absolute time
        kwargs : kwargs
            Tags to filter on

        Returns
        -------
        list
            List of results with fields for ``time`` and ``F0``
        """
        begin = Decimal(begin).quantize(Decimal('0.001'))
        end = Decimal(end).quantize(Decimal('0.001'))
        num_points = kwargs.pop('num_points', 0)
        filter_string = generate_filter_string(discourse, begin, end, channel, num_points, kwargs)
        client = self.acoustic_client()
        F0_name = "F0"
        if relative:
            F0_name += '_relativized'
        if num_points:
            columns = 'mean("{}")'.format(F0_name)
            F0_name = 'mean'
        else:
            columns = '"time", "{}"'.format(F0_name)
        query = '''select {} from "pitch"
                        {};'''.format(columns, filter_string)

        result = client.query(query)
        track = Track()
        for r in result.get_points('pitch'):
            s = to_seconds(r['time'])
            if relative_time:
                s = (s - begin) / (end - begin)
            p = TimePoint(s)
            p.add_value('F0', r[F0_name])

            track.add(p)
        return track

    def _save_measurement_tracks(self, measurement, tracks, speaker):
        if measurement not in ['formants', 'pitch', 'intensity']:
            raise (NotImplementedError('Only pitch, formants, and intensity can be currently saved.'))
        data = []

        for seg, track in tracks.items():
            if not len(track.keys()):
                continue
            file_path, begin, end, channel, utterance_id = seg.file_path, seg.begin, seg.end, seg.channel, seg[
                'utterance_id']
            res = self.execute_cypher(
                'MATCH (d:Discourse:{corpus_name}) where d.low_freq_file_path = {{file_path}} OR '
                'd.vowel_file_path = {{file_path}} OR '
                'd.consonant_file_path = {{file_path}} '
                'RETURN d.name as name'.format(
                    corpus_name=self.cypher_safe_name), file_path=file_path)
            for r in res:
                discourse = r['name']
            phone_type = getattr(self, self.phone_name)
            min_time = min(track.keys())
            max_time = max(track.keys())
            if seg['annotation_type'] == 'phone':
                set_label = seg['label']
            else:
                set_label = None
                q = self.query_graph(phone_type).filter(phone_type.discourse.name == discourse)
                q = q.filter(phone_type.end >= min_time).filter(phone_type.begin <= max_time)
                q = q.columns(phone_type.label.column_name('label'),
                              phone_type.begin.column_name('begin'),
                              phone_type.end.column_name('end')).order_by(phone_type.begin)
                phones = [(x['label'], x['begin'], x['end']) for x in q.all()]
            for time_point, value in track.items():
                if set_label is None:
                    label = None
                    for i, p in enumerate(phones):
                        if p[1] > time_point:
                            break
                        label = p[0]
                        if i == len(phones) - 1:
                            break
                    else:
                        label = None
                else:
                    label = set_label
                if label is None:
                    continue
                t_dict = {'speaker': speaker, 'discourse': discourse, 'channel': channel}
                fields = {'phone': label, 'utterance_id': utterance_id}
                if measurement == 'formants':
                    F1, F2, F3 = sanitize_formants(value)
                    if F1 > 0:
                        fields['F1'] = F1
                    if F2 > 0:
                        fields['F2'] = F2
                    if F3 > 0:
                        fields['F3'] = F3
                elif measurement == 'pitch':
                    try:
                        if value['F0'] is None:
                            continue
                        value = float(value['F0'])
                    except TypeError:
                        try:
                            value = float(value[0])
                        except TypeError:
                            try:
                                value = float(value)
                            except ValueError:
                                continue
                    if value <= 0:
                        continue
                    fields['F0'] = value
                elif measurement == 'intensity':
                    try:
                        if value['Intensity'] is None:
                            continue
                        value = float(value['Intensity'])
                    except TypeError:
                        try:
                            value = float(value[0])
                        except TypeError:
                            try:
                                value = float(value)
                            except ValueError:
                                continue
                    fields['Intensity'] = value
                d = {'measurement': measurement,
                     'tags': t_dict,
                     'time': s_to_ms(time_point),
                     'fields': fields
                     }
                data.append(d)
        self.acoustic_client().write_points(data, batch_size=1000, time_precision='ms')

    def _save_measurement(self, sound_file, track, measurement, **kwargs):
        if not len(track.keys()):
            return
        if isinstance(sound_file, str):
            sound_file = self.discourse_sound_file(sound_file)
        if sound_file is None:
            return

        if measurement not in ['formants', 'pitch', 'intensity']:
            raise (NotImplementedError('Only pitch, formants, and intensity can be currently saved.'))
        if kwargs.get('channel', None) is None:
            kwargs['channel'] = 0
        data = []
        tag_dict = {}
        if isinstance(sound_file, str):
            kwargs['discourse'] = sound_file
        else:
            kwargs['discourse'] = sound_file['name']
        utterance_id = kwargs.pop('utterance_id', None)
        tag_dict.update(kwargs)
        phone_type = getattr(self, self.phone_name)
        min_time = min(track.keys())
        max_time = max(track.keys())
        q = self.query_graph(phone_type).filter(phone_type.discourse.name == kwargs['discourse'])
        q = q.filter(phone_type.end >= min_time).filter(phone_type.begin <= max_time)
        q = q.columns(phone_type.label.column_name('label'),
                      phone_type.begin.column_name('begin'),
                      phone_type.end.column_name('end'),
                      phone_type.speaker.name.column_name('speaker')).order_by(phone_type.begin)
        phones = [(x['label'], x['begin'], x['end'], x['speaker']) for x in q.all()]
        for time_point, value in track.items():
            label = None
            speaker = None
            for i, p in enumerate(phones):
                if p[1] > time_point:
                    break
                label = p[0]
                speaker = p[-1]
                if i == len(phones) - 1:
                    break
            else:
                label = None
                speaker = None
            if speaker is None:
                continue
            t_dict = {'speaker': speaker}
            t_dict.update(tag_dict)
            fields = {'phone': label}
            if utterance_id is not None:
                fields['utterance_id'] = utterance_id
            if measurement == 'formants':
                F1, F2, F3 = sanitize_formants(value)
                if F1 > 0:
                    fields['F1'] = F1
                if F2 > 0:
                    fields['F2'] = F2
                if F3 > 0:
                    fields['F3'] = F3
            elif measurement == 'pitch':
                try:
                    value = float(value['F0'])
                except TypeError:
                    try:
                        value = float(value[0])
                    except TypeError:
                        try:
                            value = float(value)
                        except ValueError:
                            continue
                if value <= 0:
                    continue
                fields['F0'] = value
            elif measurement == 'intensity':
                try:
                    value = float(value['Intensity'])
                except TypeError:
                    try:
                        value = float(value[0])
                    except TypeError:
                        try:
                            value = float(value)
                        except ValueError:
                            continue
                fields['Intensity'] = value
            d = {'measurement': measurement,
                 'tags': t_dict,
                 'time': to_nano(time_point),
                 'fields': fields
                 }
            data.append(d)
        self.acoustic_client().write_points(data, batch_size=1000)

    def save_formants(self, sound_file, formant_track, **kwargs):
        """
        Save a formant track for a sound file

        Parameters
        ----------
        sound_file : str or :class:`~polyglotdb.sql.models.SoundFile`
            Discourse name or SoundFile object
        formant_track : dict
            Dictionary with times as keys and tuples of F1, F2, and F3 values as values
        kwargs: kwargs
            Tags to save for acoustic measurements
        """
        self._save_measurement(sound_file, formant_track, 'formants', **kwargs)
        if 'formants' not in self.hierarchy.acoustics:
            self.hierarchy.acoustics.add('formants')
            self.encode_hierarchy()

    def save_pitch(self, sound_file, pitch_track, **kwargs):
        """
        Save a pitch track for a sound file

        Parameters
        ----------
        sound_file : str or :class:`~polyglotdb.sql.models.SoundFile`
            Discourse name or SoundFile object
        pitch_track : dict
            Dictionary with times as keys and F0 values as values
        kwargs: kwargs
            Tags to save for acoustic measurements
        """
        self._save_measurement(sound_file, pitch_track, 'pitch', **kwargs)
        if 'pitch' not in self.hierarchy.acoustics:
            self.hierarchy.acoustics.add('pitch')
            self.encode_hierarchy()

    def save_pitch_tracks(self, tracks, speaker):
        self._save_measurement_tracks('pitch', tracks, speaker)

    def save_formant_tracks(self, tracks, speaker):
        self._save_measurement_tracks('formants', tracks, speaker)

    def save_intensity_tracks(self, tracks, speaker):
        self._save_measurement_tracks('intensity', tracks, speaker)

    def save_intensity(self, sound_file, intensity_track, **kwargs):
        """
        Save a pitch track for a sound file

        Parameters
        ----------
        sound_file : str or :class:`~polyglotdb.sql.models.SoundFile`
            Discourse name or SoundFile object
        intensity_track : dict
            Dictionary with times as keys and intensity values as values
        kwargs: kwargs
            Tags to save for acoustic measurements
        """
        self._save_measurement(sound_file, intensity_track, 'intensity', **kwargs)
        if 'intensity' not in self.hierarchy.acoustics:
            self.hierarchy.acoustics.add('intensity')
            self.encode_hierarchy()

    def has_formants(self, discourse):
        """
        Return whether a discourse has any formant values associated with it
        """
        client = self.acoustic_client()
        query = '''select "F1" from "formants" WHERE "discourse" = '{}' LIMIT 1;'''.format(
            discourse)
        result = client.query(query)
        if len(result) == 0:
            return False
        return True

    def has_pitch(self, discourse):
        """
        Return whether a discourse has any pitch values associated with it
        """
        client = self.acoustic_client()
        query = '''select "F0" from "pitch" WHERE "discourse" = '{}' LIMIT 1;'''.format(discourse)
        result = client.query(query)
        if len(result) == 0:
            return False
        return True

    def has_intensity(self, discourse):
        client = self.acoustic_client()
        query = '''select "Intensity" from "intensity" WHERE "discourse" = '{}' LIMIT 1;'''.format(
            discourse)
        result = client.query(query)
        if len(result) == 0:
            return False
        return True

    def encode_acoustic_statistic(self, acoustic_measure, statistic, by_phone=True, by_speaker=False):
        if not by_speaker and not by_phone:
            raise (Exception('Please specify either by_phone, by_speaker or both.'))
        client = self.acoustic_client()
        acoustic_measure = acoustic_measure.lower()
        measures = []
        template = statistic + '("{}")'
        if acoustic_measure == 'pitch':
            measures.append(template.format('F0'))
        elif acoustic_measure == 'formants':
            measures.append(template.format('F1'))
            measures.append(template.format('F2'))
            measures.append(template.format('F3'))
        elif acoustic_measure == 'intensity':
            measures.append(template.format('Intensity'))
        else:
            raise (ValueError('Acoustic measure must be one of: pitch, formants, or intensity.'))
        if by_speaker and by_phone:
            results = []
            for p in self.phones:
                query = '''select {} from "{}"
                                where "phone" = '{}' group by "speaker";'''.format(
                    ', '.join(measures), acoustic_measure, p)

                result = client.query(query)
                if acoustic_measure == 'formants':
                    for k, v in result.items():
                        data = [x[1] for x in sorted(list(v)[0].items()) if x[0] != 'time']
                        results.append({'speaker': k[1]['speaker'], 'phone': p, 'F1': data[0], 'F2': data[1],
                                        'F3': data[2]})
                else:
                    results.extend([{'speaker': k[1]['speaker'], 'phone': p, acoustic_measure: list(v)[0][statistic]}
                                    for k, v in result.items()])
            if acoustic_measure == 'formants':
                statement = '''WITH {{data}} as data
                            UNWIND data as d
                            MERGE (s:Speaker:{corpus_name})<-[r:spoken_by]-(p:phone_type:{corpus_name})
                            WHERE p.label = d.phone AND s.name = d.speaker
                            SET r.{statistic}_F1 = d.F1
                            AND r.{statistic}_F2 = d.F2
                            AND r.{statistic}_F3 = d.F3'''.format(corpus_name=self.cypher_safe_name,
                                                                  statistic=statistic)
            else:
                statement = '''WITH {{data}} as data
                            UNWIND data as d
                            MATCH (s:Speaker:{corpus_name}), (p:phone_type:{corpus_name})
                            WHERE p.label = d.phone AND s.name = d.speaker
                            MERGE (s)<-[r:spoken_by]-(p)
                            SET r.{statistic}_{measure} = d.{measure}'''.format(corpus_name=self.cypher_safe_name,
                                                                                statistic=statistic,
                                                                                measure=acoustic_measure)
        elif by_phone:
            results = []
            for p in self.phones:
                query = '''select {} from "{}"
                                where "phone" = '{}';'''.format(', '.join(measures),
                                                                acoustic_measure, p)

                result = client.query(query)

                if acoustic_measure == 'formants':
                    results = []
                    for k, v in result.items():
                        data = [x[1] for x in sorted(list(v)[0].items()) if x[0] != 'time']
                        results.append({'phone': p, 'F1': data[0], 'F2': data[1], 'F3': data[2]})
                else:
                    results.extend([{'phone': p, acoustic_measure: list(v)[0][statistic]} for k, v in result.items()])
            if acoustic_measure == 'formants':
                statement = '''WITH {{data}} as data
                                UNWIND data as d
                                MATCH (p:phone_type:{corpus_name})
                                WHERE p.label = d.phone
                                SET p.{statistic}_F1 = d.F1
                                AND p.{statistic}_F2 = d.F2
                                AND p.{statistic}_F3 = d.F3'''.format(corpus_name=self.cypher_safe_name,
                                                                      statistic=statistic)
                self.hierarchy.add_type_properties(self, 'phone', [('{}_F1'.format(statistic), float),
                                                                   ('{}_F2'.format(statistic), float),
                                                                   ('{}_F3'.format(statistic), float)])

            else:
                statement = '''WITH {{data}} as data
                                UNWIND data as d
                                MATCH (p:phone_type:{corpus_name})
                                WHERE p.label = d.phone
                                SET p.{statistic}_{measure} = d.{measure}'''.format(corpus_name=self.cypher_safe_name,
                                                                                    statistic=statistic,
                                                                                    measure=acoustic_measure)
                self.hierarchy.add_type_properties(self, 'phone',
                                                   [('{}_{}'.format(statistic, acoustic_measure), float)])
        elif by_speaker:
            query = '''select {} from "{}" group by "speaker";'''.format(', '.join(measures), acoustic_measure)
            result = client.query(query)
            if acoustic_measure == 'formants':
                results = []
                for k, v in result.items():
                    data = [x[1] for x in sorted(list(v)[0].items()) if x[0] != 'time']
                    results.append({'speaker': k[1]['speaker'], 'F1': data[0], 'F2': data[1], 'F3': data[2]})
                statement = '''WITH {{data}} as data
                                UNWIND data as d
                                MATCH (s:Speaker:{corpus_name})
                                WHERE s.name = d.speaker
                                SET s.{statistic}_F1 = d.F1
                                AND s.{statistic}_F2 = d.F2
                                AND s.{statistic}_F3 = d.F3'''.format(corpus_name=self.cypher_safe_name,
                                                                      statistic=statistic)
                self.hierarchy.add_speaker_properties(self, [('{}_F1'.format(statistic), float),
                                                             ('{}_F2'.format(statistic), float),
                                                             ('{}_F3'.format(statistic), float)])
            else:
                results = [{'speaker': k[1]['speaker'], acoustic_measure: list(v)[0][statistic]} for k, v in
                           result.items()]
                statement = '''WITH {{data}} as data
                                UNWIND data as d
                                MATCH (s:Speaker:{corpus_name})
                                WHERE s.name = d.speaker
                                SET s.{statistic}_{measure} = d.{measure}'''.format(corpus_name=self.cypher_safe_name,
                                                                                    statistic=statistic,
                                                                                    measure=acoustic_measure)
                self.hierarchy.add_speaker_properties(self, [('{}_{}'.format(statistic, acoustic_measure), float)])
        self.execute_cypher(statement, data=results)
        self.encode_hierarchy()

    def get_acoustic_statistic(self, acoustic_measure, statistic, by_phone=True, by_speaker=False):
        if not by_speaker and not by_phone:
            raise (Exception('Please specify either by_phone, by_speaker or both.'))
        if acoustic_measure == 'formants':
            name = '{}_F1'.format(statistic)
        else:
            name = '{}_{}'.format(statistic, acoustic_measure)
        if by_phone and by_speaker:
            statement = '''MATCH (p:phone_type:{0})-[r:spoken_by]->(s:Speaker:{0}) return r.{1} as {1} LIMIT 1'''.format(
                self.cypher_safe_name, name)
            results = self.execute_cypher(statement).records()
            try:
                first = next(results)
            except StopIteration:
                first = None
            if first is None or first[name] is None:
                self.encode_acoustic_statistic(acoustic_measure, statistic, by_phone, by_speaker)
            if acoustic_measure == 'formants':
                statement = '''MATCH (p:phone_type:{0})-[r:spoken_by]->(s:Speaker:{0})
                return p.label as phone, s.name as speaker, r.{1}_F1 as F1, r.{1}_F2 as F2, r.{1}_F3 as F3'''.format(
                    self.cypher_safe_name, statistic)
                results = self.execute_cypher(statement).records()
                results = {(x['speaker'], x['phone']): [x['F1'], x['F2'], x['F3']] for x in results}
            else:
                statement = '''MATCH (p:phone_type:{0})-[r:spoken_by]->(s:Speaker:{0})
                return p.label as phone, s.name as speaker, r.{1} as {1}'''.format(self.cypher_safe_name, name)
                results = self.execute_cypher(statement).records()
                results = {(x['speaker'], x['phone']): [x[name]] for x in results}
        elif by_phone:
            if not self.hierarchy.has_type_property('phone', name):
                self.encode_acoustic_statistic(acoustic_measure, statistic, by_phone, by_speaker)
            if acoustic_measure == 'formants':
                statement = '''MATCH (p:phone_type:{0})
                return p.label as phone, p.{1}_F1 as F1, p.{1}_F2 as F2, p.{1}_F3 as F3'''.format(
                    self.cypher_safe_name, statistic)
                results = self.execute_cypher(statement).records()
                results = {x['phone']: [x['F1'], x['F2'], x['F3']] for x in results}
            else:
                statement = '''MATCH (p:phone_type:{0})
                return p.label as phone, p.{1} as {1}'''.format(self.cypher_safe_name, name)
                results = self.execute_cypher(statement).records()
                results = {x['phone']: [x[name]] for x in results}
        elif by_speaker:
            if not self.hierarchy.has_speaker_property(name):
                self.encode_acoustic_statistic(acoustic_measure, statistic, by_phone, by_speaker)
            if acoustic_measure == 'formants':
                statement = '''MATCH (s:Speaker:{0})
                return s.name as speaker, s.{1}_F1 as F1, s.{1}_F2 as F2, s.{1}_F3 as F3'''.format(
                    self.cypher_safe_name, statistic)
                results = self.execute_cypher(statement).records()
                results = {x['speaker']: [x['F1'], x['F2'], x['F3']] for x in results}
            else:
                statement = '''MATCH (s:Speaker:{0})
                return s.name as speaker, s.{1} as {1}'''.format(self.cypher_safe_name, name)
                results = self.execute_cypher(statement).records()
                results = {x['speaker']: [x[name]] for x in results}
        return results

    def reset_relativized_pitch(self):
        client = self.acoustic_client()
        query = """SELECT "phone", "F0", "utterance_id" INTO "pitch_copy" FROM "pitch" GROUP BY *;"""
        client.query(query)
        client.query('DROP MEASUREMENT "pitch"')
        client.query('SELECT * INTO "pitch" FROM "pitch_copy" GROUP BY *')
        client.query('DROP MEASUREMENT "pitch_copy"')

    def relativize_pitch(self, by_speaker=True, by_phone=False):
        if not by_speaker and not by_phone:
            raise Exception('Relativization must be by phone, speaker, or both.')
        client = self.acoustic_client()
        phone_type = getattr(self, self.phone_name)

        summary_data = {}
        if by_phone:
            for p in self.phones:
                if by_speaker:
                    query = '''select mean("F0"), stddev("F0") from "pitch" where "phone" = '{}' group by "speaker";'''.format(
                        p)
                    result = client.query(query)
                    for k, v in result.items():
                        v = list(v)
                        summary_data[(k[1]['speaker'], p)] = v[0]['mean'], v[0]['stddev']

                else:
                    query = '''select mean("F0"), stddev("F0") from "pitch" where "phone" = '{}';'''.format(p)
                    result = client.query(query)
                    for k, v in result.items():
                        v = list(v)
                        summary_data[p] = v[0]['mean'], v[0]['stddev']
        else:
            query = '''select mean("F0"), stddev("F0") from "pitch" where "phone" != '' group by "speaker";'''
            result = client.query(query)
            for k, v in result.items():
                v = list(v)
                summary_data[k[1]['speaker']] = v[0]['mean'], v[0]['stddev']
        for s in self.speakers:
            all_query = '''select * from "pitch"
                            where "phone" != '' and "speaker" = '{}';'''.format(s)
            all_results = client.query(all_query)
            data = []
            for _, r in all_results.items():
                for t_dict in r:

                    phone = t_dict.pop('phone')
                    utterance_id = t_dict.pop('utterance_id', '')
                    if by_speaker and by_phone:
                        mean_f0, sd_f0 = summary_data[(t_dict['speaker'], phone)]
                    elif by_phone and not by_speaker:
                        mean_f0, sd_f0 = summary_data[phone]
                    elif by_speaker:
                        mean_f0, sd_f0 = summary_data[t_dict['speaker']]
                    if sd_f0 is None:
                        continue
                    pitch = t_dict.pop('F0')
                    if pitch is None:
                        continue
                    new_pitch = t_dict.pop('F0_relativized', None)
                    time_point = t_dict.pop('time')
                    time_point = s_to_ms(to_seconds(time_point))
                    new_pitch = (pitch - mean_f0) / sd_f0
                    d = {'measurement': 'pitch',
                         'tags': t_dict,
                         "time": time_point,
                         "fields": {'F0_relativized': new_pitch}
                         }
                    data.append(d)
            client.write_points(data, batch_size=1000, time_precision='ms')

    def reset_relativized_intensity(self):
        client = self.acoustic_client()
        query = """SELECT "phone", "Intensity", "utterance_id" INTO "intensity_copy" FROM "intensity" GROUP BY *;"""
        client.query(query)
        client.query('DROP MEASUREMENT "intensity"')
        client.query('SELECT * INTO "intensity" FROM "intensity_copy" GROUP BY *')
        client.query('DROP MEASUREMENT "intensity_copy"')

    def relativize_intensity(self, by_speaker=True):
        client = self.acoustic_client()
        phone_type = getattr(self, self.phone_name)

        summary_data = {}
        for p in self.phones:
            if by_speaker:
                query = '''select mean("Intensity"), stddev("Intensity") from "intensity" where "phone" = '{}' group by "speaker";'''.format(
                    p)
                result = client.query(query)
                for k, v in result.items():
                    v = list(v)
                    summary_data[(k[1]['speaker'], p)] = v[0]['mean'], v[0]['stddev']

            else:
                query = '''select mean("Intensity"), stddev("Intensity") from "intensity" where "phone" = '{}' ;'''.format(
                    p)
                result = client.query(query)
                for k, v in result.items():
                    v = list(v)
                    summary_data[p] = v[0]['mean'], v[0]['stddev']

        for s in self.speakers:
            all_query = '''select * from "intensity"
                            where "phone" != '' and "speaker" = '{}';'''.format(s)
            all_results = client.query(all_query)
            data = []
            for _, r in all_results.items():
                for t_dict in r:
                    phone = t_dict.pop('phone')
                    utterance_id = t_dict.pop('utterance_id', '')
                    if by_speaker:
                        mean_intensity, sd_intensity = summary_data[(t_dict['speaker'], phone)]
                    else:
                        mean_intensity, sd_intensity = summary_data[phone]
                    if sd_intensity is None:
                        continue
                    intensity = t_dict.pop('Intensity')
                    if intensity is None:
                        continue
                    time_point = t_dict.pop('time')
                    time_point = s_to_ms(to_seconds(time_point))
                    new_intensity = t_dict.pop('Intensity_relativized', None)
                    new_intensity = (intensity - mean_intensity) / sd_intensity
                    d = {'measurement': 'intensity',
                         'tags': t_dict,
                         "time": time_point,
                         "fields": {'Intensity_relativized': new_intensity}
                         }
                    data.append(d)
            client.write_points(data, batch_size=1000, time_precision='ms')

    def reassess_utterances(self, measure):
        client = self.acoustic_client()
        q = self.query_discourses()
        q = q.columns(self.discourse.name.column_name('name'),
                      self.discourse.speakers.name.column_name('speakers'))
        discourses = q.all()
        for d in discourses:
            discourse_name = d['name']
            data = []
            for s in d['speakers']:
                q = self.query_graph(self.utterance)
                q = q.filter(self.utterance.discourse.name == discourse_name, self.utterance.speaker.name == s)
                q = q.order_by(self.utterance.begin)
                q = q.columns(self.utterance.id.column_name('utterance_id'),
                              self.utterance.begin.column_name('begin'),
                              self.utterance.end.column_name('end'))
                utterances = q.all()
                all_query = '''select * from "{}"
                                where "phone" != '' and 
                                "discourse" = '{}' and 
                                "speaker" = '{}';'''.format(measure, discourse_name, s)
                all_results = client.query(all_query)
                cur_index = 0
                for _, r in all_results.items():
                    for t_dict in r:
                        phone = t_dict.pop('phone')
                        utterance_id = t_dict.pop('utterance_id', '')
                        value = None
                        if measure == 'intensity':
                            value = t_dict.pop('Intensity')
                            rel_value = t_dict.pop('Intensity_relativized', None)
                        elif measure == 'pitch':
                            value = t_dict.pop('F0')
                            rel_value = t_dict.pop('F0_relativized', None)
                        elif measure == 'formants':
                            F2 = t_dict.pop('F2')
                            new_F2 = t_dict.pop('F2_relativized', None)
                            F3 = t_dict.pop('F3')
                            new_F3 = t_dict.pop('F3_relativized', None)
                            value = t_dict.pop('F1')
                            rel_value = t_dict.pop('F1_relativized', None)

                        if value is None:
                            continue
                        time_point = to_seconds(t_dict.pop('time'))
                        for i in range(cur_index, len(utterances)):
                            if utterances[i]['begin'] <= time_point <= utterances[i]['end']:
                                cur_index = i
                                break
                        time_point = s_to_ms(time_point)
                        d = {'measurement': measure,
                             'tags': t_dict,
                             "time": time_point,
                             "fields": {'utterance_id': utterances[cur_index]['utterance_id']}
                             }
                        data.append(d)
            client.write_points(data, batch_size=1000, time_precision='ms')

    def reset_relativized_formants(self):
        client = self.acoustic_client()
        query = """SELECT "phone", "F1", "F2", "F3", "utterance_id" INTO "formants_copy" FROM "formants" GROUP BY *;"""
        client.query(query)
        client.query('DROP MEASUREMENT "formants"')
        client.query('SELECT * INTO "formants" FROM "formants_copy" GROUP BY *')
        client.query('DROP MEASUREMENT "formants_copy"')

    def relativize_formants(self, by_speaker=True):
        client = self.acoustic_client()
        phone_type = getattr(self, self.phone_name)

        summary_data = {}
        for p in self.phones:
            if by_speaker:
                query = '''select mean("F1"), stddev("F1"), mean("F2"), stddev("F2"), mean("F3"), stddev("F3") from "formants" where "phone" = '{}' group by "speaker";'''.format(
                    p)
                result = client.query(query)
                for k, v in result.items():
                    v = list(v)
                    summary_data[(k[1]['speaker'], p)] = v[0]['mean'], v[0]['stddev'], v[0]['mean_1'], v[0]['stddev_1'], \
                                                         v[0]['mean_2'], v[0]['stddev_2']

            else:
                query = '''select mean("F1"), stddev("F1"), mean("F2"), stddev("F2"), mean("F3"), stddev("F3") from "formants" where "phone" = '{}';'''.format(
                    p)
                result = client.query(query)
                for k, v in result.items():
                    v = list(v)
                    summary_data[p] = v[0]['mean'], v[0]['stddev'], v[0]['mean_1'], v[0]['stddev_1'], v[0]['mean_2'], \
                                      v[0]['stddev_2']

        for s in self.speakers:
            all_query = '''select * from "formants"
                            where "phone" != '' and "speaker" = '{}';'''.format(s)
            all_results = client.query(all_query)
            data = []
            for _, r in all_results.items():
                for t_dict in r:
                    phone = t_dict.pop('phone')
                    utterance_id = t_dict.pop('utterance_id', '')
                    if by_speaker:
                        mean_F1, sd_F1, mean_F2, sd_F2, mean_F3, sd_F3 = summary_data[(t_dict['speaker'], phone)]
                    else:
                        mean_F1, sd_F1, mean_F2, sd_F2, mean_F3, sd_F3 = summary_data[phone]
                    F1 = t_dict.pop('F1')
                    new_F1 = t_dict.pop('F1_relativized', None)
                    F2 = t_dict.pop('F2')
                    new_F2 = t_dict.pop('F2_relativized', None)
                    F3 = t_dict.pop('F3')
                    new_F3 = t_dict.pop('F3_relativized', None)
                    time_point = t_dict.pop('time')
                    time_point = s_to_ms(to_seconds(time_point))
                    fields = {}
                    if sd_F1 is not None and F1 is not None:
                        new_F1 = (F1 - mean_F1) / sd_F1
                        fields['F1_relativized'] = new_F1
                    if sd_F2 is not None and F2 is not None:
                        new_F2 = (F2 - mean_F2) / sd_F2
                        fields['F2_relativized'] = new_F2
                    if sd_F3 is not None and F3 is not None:
                        new_F3 = (F3 - mean_F3) / sd_F3
                        fields['F3_relativized'] = new_F3
                    if not fields:
                        continue
                    d = {'measurement': 'formants',
                         'tags': t_dict,
                         "time": time_point,
                         "fields": fields
                         }
                    data.append(d)
            client.write_points(data, batch_size=1000, time_precision='ms')
