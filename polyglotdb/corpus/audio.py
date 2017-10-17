import os
import re
import librosa
from datetime import datetime
from decimal import Decimal

from influxdb import InfluxDBClient

from polyglotdb.query.discourse import DiscourseInspector
from ..acoustics import analyze_pitch, analyze_formant_tracks, analyze_vowel_formant_tracks, analyze_intensity, \
    analyze_script, analyze_discourse_pitch
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


def generate_filter_string(discourse, begin, end, num_points, kwargs):
    extra_filters = ['''"{}" = '{}' '''.format(k, v) for k, v in kwargs.items()]
    filter_string = '''WHERE "discourse" = '{}'
                            AND "time" >= {}
                            AND "time" <= {}'''
    if extra_filters:
        filter_string += '\nAND {}'.format('\nAND '.join(extra_filters))
    if num_points:
        duration = end - begin
        time_step = duration / (num_points - 1)
        begin -= time_step / 2
        end += time_step / 2
        time_step *= 1000
        filter_string += '\ngroup by time({}ms) fill(null)'.format(int(time_step))
    filter_string = filter_string.format(discourse, to_nano(begin), to_nano(end))
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

    def analyze_pitch(self, stop_check=None, call_back=None):
        analyze_pitch(self, stop_check, call_back)

    def analyze_discourse_pitch(self, discourse, **kwargs):
        return analyze_discourse_pitch(self, discourse, **kwargs)

    def analyze_formant_tracks(self, stop_check=None, call_back=None):
        analyze_formant_tracks(self, stop_check, call_back)

    def analyze_vowel_formant_tracks(self, stop_check=None, call_back=None, vowel_inventory=None):
        analyze_vowel_formant_tracks(self, stop_check, call_back, vowel_inventory)

    def analyze_intensity(self, stop_check=None, call_back=None):
        analyze_intensity(self, stop_check, call_back)

    def analyze_script(self, phone_class, script_path, arguments=None, stop_check=None, call_back=None):
        analyze_script(self, phone_class, script_path, arguments=arguments, stop_check=stop_check, call_back=call_back)

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

    def load_waveform(self, discourse, file_type='consonant'):
        sf = self.discourse_sound_file(discourse)
        if file_type == 'consonant':
            file_path = sf['consonant_file_path']
        elif file_type == 'vowel':
            file_path = sf['vowel_file_path']
        elif file_type == 'low_freq':
            file_path = sf['low_freq_file_path']
        else:
            file_path = sf['file_path']
        return load_waveform(file_path)

    def generate_spectrogram(self, discourse, file_type='consonant'):
        signal, sr = self.load_waveform(discourse, file_type)
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

    def get_intensity(self, discourse, begin, end, relative=False, relative_time=False, **kwargs):
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
        if kwargs.get('source', None) is None:
            kwargs['source'] = self.config.intensity_source
        num_points = kwargs.pop('num_points', 0)
        filter_string = generate_filter_string(discourse, begin, end, num_points, kwargs)
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
        listing = []
        for r in result.get_points('intensity'):
            s = to_seconds(r['time'])
            if relative_time:
                s = (s - begin) / (end - begin)
            listing.append((s, r[Intensity_name]))
        return listing

    def get_formants(self, discourse, begin, end, relative=False, relative_time=False, **kwargs):
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
        if kwargs.get('source', None) is None:
            kwargs['source'] = self.config.formant_source
        num_points = kwargs.pop('num_points', 0)
        filter_string = generate_filter_string(discourse, begin, end, num_points, kwargs)
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
        listing = []
        for r in result.get_points('formants'):
            s = to_seconds(r['time'])
            if relative_time:
                s = (s - begin) / (end - begin)
            listing.append(tuple([s] + [r[x] for x in formant_names]))
        return listing

    def get_pitch(self, discourse, begin, end, relative=False, relative_time=False, **kwargs):
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
        if kwargs.get('source', None) is None:
            kwargs['source'] = self.config.pitch_source
        num_points = kwargs.pop('num_points', 0)
        filter_string = generate_filter_string(discourse, begin, end, num_points, kwargs)
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
        listing = []
        for r in result.get_points('pitch'):
            s = to_seconds(r['time'])
            if relative_time:
                s = (s - begin) / (end - begin)
            listing.append((s, r[F0_name]))
        return listing

    def _save_measurement_tracks(self, measurement, tracks, speaker):
        if measurement == 'formants':
            source = self.config.formant_source
        elif measurement == 'pitch':
            source = self.config.pitch_source
        elif measurement == 'intensity':
            source = self.config.intensity_source
        else:
            raise (NotImplementedError('Only pitch, formants, and intensity can be currently saved.'))
        data = []
        for seg, track in tracks.items():
            if not len(track.keys()):
                print(seg)
                continue
            file_path, begin, end, channel = seg.file_path, seg.begin, seg.end, seg.channel
            res = self.execute_cypher(
                'MATCH (d:Discourse:{corpus_name}) where d.vowel_file_path = {{file_path}} RETURN d.name as name'.format(
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
                t_dict = {'speaker': speaker, 'discourse': discourse, 'channel': channel, 'source': source}
                fields = {'phone': label}
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
                    print(fields)
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
            print(sound_file)
            return
        if isinstance(sound_file, str):
            sound_file = self.discourse_sound_file(sound_file)
        if sound_file is None:
            return

        if measurement == 'formants':
            if kwargs.get('source', None) is None:
                kwargs['source'] = self.config.formant_source
        elif measurement == 'pitch':
            if kwargs.get('source', None) is None:
                kwargs['source'] = self.config.pitch_source
        elif measurement == 'intensity':
            if kwargs.get('source', None) is None:
                kwargs['source'] = self.config.intensity_source
        else:
            raise (NotImplementedError('Only pitch, formants, and intensity can be currently saved.'))
        if kwargs.get('channel', None) is None:
            kwargs['channel'] = 0
        data = []
        tag_dict = {}
        if isinstance(sound_file, str):
            kwargs['discourse'] = sound_file
        else:
            kwargs['discourse'] = sound_file['name']
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

    def has_formants(self, discourse, source=None):
        """
        Return whether a discourse has any formant values associated with it
        """
        client = self.acoustic_client()
        if source is None:
            source = self.config.formant_source
        query = '''select "F1" from "formants" WHERE "discourse" = '{}' AND "source" = '{}' LIMIT 1;'''.format(
            discourse, source)
        result = client.query(query)
        if len(result) == 0:
            return False
        return True

    def has_pitch(self, discourse, source=None):
        """
        Return whether a discourse has any pitch values associated with it
        """
        client = self.acoustic_client()
        if source is None:
            source = self.config.pitch_source
        query = '''select "F0" from "pitch" WHERE "discourse" = '{}' AND "source" = '{}' LIMIT 1;'''.format(discourse,
                                                                                                            source)
        result = client.query(query)
        if len(result) == 0:
            return False
        return True

    def has_intensity(self, discourse, source=None):
        client = self.acoustic_client()
        if source is None:
            source = self.config.intensity_source
        query = '''select "Intensity" from "intensity" WHERE "discourse" = '{}' AND "source" = '{}' LIMIT 1;'''.format(
            discourse, source)
        result = client.query(query)
        if len(result) == 0:
            return False
        return True

    def encode_acoustic_statistic(self, acoustic_measure, statistic, by_phone=True, by_speaker=False, source=None):
        print('hello')
        if not by_speaker and not by_phone:
            raise (Exception('Please specify either by_phone, by_speaker or both.'))
        client = self.acoustic_client()
        acoustic_measure = acoustic_measure.lower()
        measures = []
        template = statistic + '("{}")'
        if acoustic_measure == 'pitch':
            measures.append(template.format('F0'))
            if source is None:
                source = self.config.pitch_source
        elif acoustic_measure == 'formants':
            measures.append(template.format('F1'))
            measures.append(template.format('F2'))
            measures.append(template.format('F3'))
            if source is None:
                source = self.config.formant_source
        elif acoustic_measure == 'intensity':
            measures.append(template.format('Intensity'))
            if source is None:
                source = self.config.intensity_source
        else:
            raise (ValueError('Acoustic measure must be one of: pitch, formants, or intensity.'))
        if by_speaker and by_phone:
            results = []
            for p in self.phones:
                query = '''select {} from "{}"
                                where "phone" = '{}' and "source" = '{}' group by "speaker";'''.format(
                    ', '.join(measures), acoustic_measure, p, source)

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
                                where "phone" = '{}' and "source" = '{}';'''.format(', '.join(measures),
                                                                                    acoustic_measure, p, source)

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
            query = '''select {} from "{}"
                            where "source" = '{}' group by "speaker";'''.format(', '.join(measures), acoustic_measure,
                                                                                source)
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
        print(results)
        self.execute_cypher(statement, data=results)
        self.encode_hierarchy()

    def get_acoustic_statistic(self, acoustic_measure, statistic, by_phone=True, by_speaker=False, source=None):
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
                self.encode_acoustic_statistic(acoustic_measure, statistic, by_phone, by_speaker, source)
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
                self.encode_acoustic_statistic(acoustic_measure, statistic, by_phone, by_speaker, source)
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
                self.encode_acoustic_statistic(acoustic_measure, statistic, by_phone, by_speaker, source)
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

    def relativize_pitch(self, by_speaker=True, source=None):
        if source is None:
            source = self.config.pitch_source
        client = self.acoustic_client()
        phone_type = getattr(self, self.phone_name)

        summary_data = {}
        for p in self.phones:
            if by_speaker:
                query = '''select mean("F0"), stddev("F0") from "pitch" where "phone" = '{}' and "source" = '{}' group by "speaker";'''.format(
                    p, source)
                result = client.query(query)
                for k, v in result.items():
                    v = list(v)
                    summary_data[(k[1]['speaker'], p)] = v[0]['mean'], v[0]['stddev']

            else:
                query = '''select mean("F0"), stddev("F0") from "pitch" where "phone" = '{}' and "source" = '{}';'''.format(
                    p, source)
                result = client.query(query)
                for k, v in result.items():
                    v = list(v)
                    summary_data[p] = v[0]['mean'], v[0]['stddev']

        all_query = '''select * from "pitch"
                        where "source" = '{}' and "phone" != '' and "speaker" != '';'''.format(source)
        all_results = client.query(all_query)
        data = []
        for _, r in all_results.items():
            for t_dict in r:
                phone = t_dict.pop('phone')
                if by_speaker:
                    mean_f0, sd_f0 = summary_data[(t_dict['speaker'], phone)]
                else:
                    mean_f0, sd_f0 = summary_data[phone]
                if sd_f0 is None:
                    continue
                pitch = t_dict.pop('F0')
                if pitch is None:
                    continue
                time_point = t_dict.pop('time')
                new_pitch = (pitch - mean_f0) / sd_f0
                d = {'measurement': 'pitch',
                     'tags': t_dict,
                     "time": time_point,
                     "fields": {'F0_relativized': new_pitch}
                     }
                data.append(d)
        client.write_points(data, batch_size=1000)

    def relativize_intensity(self, by_speaker=True, source=None):
        if source is None:
            source = self.config.intensity_source
        client = self.acoustic_client()
        phone_type = getattr(self, self.phone_name)

        summary_data = {}
        for p in self.phones:
            if by_speaker:
                query = '''select mean("Intensity"), stddev("Intensity") from "intensity" where "phone" = '{}' and "source" = '{}' group by "speaker";'''.format(
                    p, source)
                result = client.query(query)
                for k, v in result.items():
                    v = list(v)
                    summary_data[(k[1]['speaker'], p)] = v[0]['mean'], v[0]['stddev']

            else:
                query = '''select mean("Intensity"), stddev("Intensity") from "intensity" where "phone" = '{}' and "source" = '{}';'''.format(
                    p, source)
                result = client.query(query)
                for k, v in result.items():
                    v = list(v)
                    summary_data[p] = v[0]['mean'], v[0]['stddev']

        all_query = '''select * from "intensity"
                        where "source" = '{}' and "phone" != '' and "speaker" != '';'''.format(source)
        all_results = client.query(all_query)
        data = []
        for _, r in all_results.items():
            for t_dict in r:
                phone = t_dict.pop('phone')
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
                new_intensity = (intensity - mean_intensity) / sd_intensity
                d = {'measurement': 'intensity',
                     'tags': t_dict,
                     "time": time_point,
                     "fields": {'Intensity_relativized': new_intensity}
                     }
                data.append(d)
        client.write_points(data, batch_size=1000)

    def relativize_formants(self, by_speaker=True, source=None):
        if source is None:
            source = self.config.formant_source
        client = self.acoustic_client()
        phone_type = getattr(self, self.phone_name)

        summary_data = {}
        for p in self.phones:
            if by_speaker:
                query = '''select mean("F1"), stddev("F1"), mean("F2"), stddev("F2"), mean("F3"), stddev("F3") from "formants" where "phone" = '{}' and "source" = '{}' group by "speaker";'''.format(
                    p, source)
                result = client.query(query)
                for k, v in result.items():
                    v = list(v)
                    summary_data[(k[1]['speaker'], p)] = v[0]['mean'], v[0]['stddev'], v[0]['mean_1'], v[0]['stddev_1'], \
                                                         v[0]['mean_2'], v[0]['stddev_2']

            else:
                query = '''select mean("F1"), stddev("F1"), mean("F2"), stddev("F2"), mean("F3"), stddev("F3") from "formants" where "phone" = '{}' and "source" = '{}';'''.format(
                    p, source)
                result = client.query(query)
                for k, v in result.items():
                    v = list(v)
                    summary_data[p] = v[0]['mean'], v[0]['stddev'], v[0]['mean_1'], v[0]['stddev_1'], v[0]['mean_2'], \
                                      v[0]['stddev_2']

        all_query = '''select * from "formants"
                        where "source" = '{}' and "phone" != '' and "speaker" != '';'''.format(source)
        all_results = client.query(all_query)
        data = []
        for _, r in all_results.items():
            for t_dict in r:
                phone = t_dict.pop('phone')
                if by_speaker:
                    mean_F1, sd_F1, mean_F2, sd_F2, mean_F3, sd_F3 = summary_data[(t_dict['speaker'], phone)]
                else:
                    mean_F1, sd_F1, mean_F2, sd_F2, mean_F3, sd_F3 = summary_data[phone]
                F1 = t_dict.pop('F1')
                F2 = t_dict.pop('F2')
                F3 = t_dict.pop('F3')
                time_point = t_dict.pop('time')
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
        client.write_points(data, batch_size=1000)
