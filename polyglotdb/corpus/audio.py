import os
from datetime import datetime
from decimal import Decimal

from influxdb import InfluxDBClient

from ..acoustics import acoustic_analysis

from ..sql.models import SoundFile, Discourse

from ..graph.discourse import DiscourseInspecter

from polyglotdb.exceptions import NoSoundFileError


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
    return f1, f2, f3


def generate_filter_string(discourse, begin, end, num_points, kwargs):
    extra_filters = ['''"{}" = '{}' '''.format(k, v) for k, v in kwargs.items()]
    filter_string = '''WHERE "discourse" = '{}'
                            AND "time" >= {}
                            AND "time" <= {}'''
    if extra_filters:
        filter_string += '\nAND {}'.format('\nAND '.join(extra_filters))
    if num_points:
        duration = end - begin
        time_step = duration / (num_points-1)
        begin -= time_step / 2
        end += time_step / 2
        time_step *= 1000
        filter_string += '\ngroup by time({}ms) fill(null)'.format(int(time_step))
    filter_string = filter_string.format(discourse, to_nano(begin), to_nano(end))
    return filter_string


def to_nano(seconds):
    if not isinstance(seconds,Decimal):
        seconds = Decimal(seconds).quantize(Decimal('0.001'))
    return int(seconds * Decimal('1e9'))


def to_seconds(time_string):
    try:
        d = datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%S.%fZ')
    except:
        d = datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%SZ')

    s = 60*60*d.hour + 60*d.minute + d.second + d.microsecond / 1e6
    s = Decimal(s).quantize(Decimal('0.001'))
    return s


class AudioContext(object):
    """
    Class that contains methods for dealing with audio files for corpora
    """
    def analyze_acoustics(self,
                      pitch = True,
                      formants = False,
                      intensity = False, stop_check = None, call_back = None):
        """
        Runs all acoustic analyses for the corpus.
        """
        if not self.has_sound_files:
            raise(NoSoundFileError)
        acoustic_analysis(self, pitch, formants, intensity, stop_check = stop_check, call_back = call_back)

    def genders(self):

        res = self.execute_cypher('''MATCH (s:Speaker:{corpus_name}) RETURN s.gender as gender'''.format(corpus_name = self.cypher_safe_name))
        genders = set()
        for s in res:
            g = s['gender']
            if g is None:
                g = ''
            genders.add(g)
        return sorted(genders)


    def reset_acoustics(self, call_back = None, stop_check = None):
        self.acoustic_client().drop_database(self.corpus_name)

    def acoustic_client(self):
        client = InfluxDBClient(**self.config.acoustic_conncetion_kwargs)
        databases = client.get_list_database()
        if self.corpus_name not in databases:
            client.create_database(self.corpus_name)
        return client

    def inspect_discourse(self, discourse, begin = None, end = None):
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
        :class:`~polyglotdb.graph.discourse.DiscourseInspecter`
            DiscourseInspecter for the specified discourse
        """
        return DiscourseInspecter(self, discourse, begin, end)

    def discourse_sound_file(self, discourse):
        """
        Gets the sound file object for the discourse

        Parameters
        ----------
        discourse : str
            Name of the discourse

        Returns
        -------
        :class:`~polyglotdb.sql.models.SoundFile`
            the first soundfile
        """
        q = self.sql_session.query(SoundFile).join(SoundFile.discourse)
        q = q.filter(Discourse.name == discourse)
        sound_file = q.first()
        return sound_file

    def discourse_audio_directory(self, discourse):
        """
        Return the directory for the stored audio files for a discourse
        """
        return os.path.join(self.config.audio_dir, discourse)

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
            if not os.path.exists(sf.filepath):
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
            self._has_sound_files = self.sql_session.query(SoundFile).first() is not None
        return self._has_sound_files

    def get_intensity(self, discourse, begin, end, relative = False, relative_time=False, **kwargs):
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
            kwargs['source'] = self.config.intensity_algorithm
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

    def get_formants(self, discourse, begin, end, relative = False, relative_time=False, **kwargs):
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
            kwargs['source'] = self.config.formant_algorithm
        num_points = kwargs.pop('num_points', 0)
        filter_string = generate_filter_string(discourse, begin, end, num_points, kwargs)
        client = self.acoustic_client()
        formant_names = ["F1","F2", "F3"]
        if relative:
            for i in range(3):
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
            kwargs['source'] = self.config.pitch_algorithm
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
        if isinstance(sound_file, str):
            sound_file = self.discourse_sound_file(sound_file)
        if sound_file is None:
           return
        if kwargs.get('source',None) is None:
            kwargs['source'] = self.config.formant_algorithm
        if kwargs.get('channel', None) is None:
            kwargs['channel'] = 0
        data = []
        tag_dict = {}
        if isinstance(sound_file, str):
            kwargs['discourse'] = sound_file
        else:
            kwargs['discourse'] = sound_file.discourse.name
        tag_dict.update(kwargs)
        phone_type = getattr(self, self.phone_name)
        min_time = min(formant_track.keys())
        max_time = max(formant_track.keys())
        q = self.query_graph(phone_type).filter(phone_type.discourse.name == kwargs['discourse'])
        q = q.filter(phone_type.begin >= min_time).filter(phone_type.end <= max_time)
        q = q.columns(phone_type.label.column_name('label'),
                      phone_type.begin.column_name('begin'),
                      phone_type.end.column_name('end'),
                      phone_type.speaker.name.column_name('speaker')).order_by(phone_type.begin)
        phones = [(x['label'], x['begin'],x['end'], x['speaker']) for x in q.all()]
        for time_point, value in formant_track.items():
            F1, F2, F3 = sanitize_formants(value)
            label = None
            speaker = None
            for p in phones:
                if p[1] > time_point:
                    break
                label = p[0]
                speaker = p[-1]
            else:
                label = None
                speaker = None
            if speaker is None:
                continue
            t_dict = {'speaker': speaker}
            t_dict.update(tag_dict)
            fields = {'phone':label}
            if F1 > 0:
                fields['F1'] = F1
            if F2 > 0:
                fields['F2'] = F2
            if F3 > 0:
                fields['F3'] = F3
            d = {'measurement': 'formants',
                 'tags': t_dict,
                 'time': to_nano(time_point),
                 'fields': fields
                }
            data.append(d)
        self.acoustic_client().write_points(data, batch_size=1000)

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
        if isinstance(sound_file, str):
            sound_file = self.discourse_sound_file(sound_file)
        if sound_file is None:
            return
        if kwargs.get('source', None) is None:
            kwargs['source'] = self.config.pitch_algorithm
        if kwargs.get('channel', None) is None:
            kwargs['channel'] = 0
        data = []
        tag_dict = {}
        if isinstance(sound_file, str):
            kwargs['discourse'] = sound_file
        else:
            kwargs['discourse'] = sound_file.discourse.name
        tag_dict.update(kwargs)
        phone_type = getattr(self, self.phone_name)
        min_time = min(pitch_track.keys())
        max_time = max(pitch_track.keys())
        q = self.query_graph(phone_type).filter(phone_type.discourse.name == kwargs['discourse'])
        q = q.filter(phone_type.begin >= min_time).filter(phone_type.end <= max_time)
        q = q.columns(phone_type.label.column_name('label'),
                      phone_type.begin.column_name('begin'),
                      phone_type.end.column_name('end'),
                      phone_type.speaker.name.column_name('speaker')).order_by(phone_type.begin)
        phones = [(x['label'], x['begin'],x['end'], x['speaker']) for x in q.all()]
        for time_point, value in pitch_track.items():
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
            label = None
            speaker = None
            for p in phones:
                if p[1] > time_point:
                    break
                label = p[0]
                speaker = p[-1]
            else:
                label = None
                speaker = None
            if speaker is None:
                continue
            t_dict = {'speaker': speaker}
            t_dict.update(tag_dict)
            fields = {'F0': value, 'phone':label}

            d = {'measurement': 'pitch',
                 'tags': t_dict,
                 'time': to_nano(time_point),
                 'fields': fields
                }
            data.append(d)
        self.acoustic_client().write_points(data, batch_size=1000)


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
        if kwargs.get('source',None) is None:
            source = self.config.intensity_algorithm
            kwargs['source'] = source
        if isinstance(sound_file, str):
            sound_file = self.discourse_sound_file(sound_file)
        if sound_file is None:
            return
        if kwargs.get('source',None) is None:
            kwargs['source'] = self.config.intensity_algorithm
        if kwargs.get('channel', None) is None:
            kwargs['channel'] = 0
        data = []
        tag_dict = {}
        if isinstance(sound_file, str):
            kwargs['discourse'] = sound_file
        else:
            kwargs['discourse'] = sound_file.discourse.name
        tag_dict.update(kwargs)
        phone_type = getattr(self, self.phone_name)
        min_time = min(intensity_track.keys())
        max_time = max(intensity_track.keys())
        q = self.query_graph(phone_type).filter(phone_type.discourse.name == kwargs['discourse'])
        q = q.filter(phone_type.begin >= min_time).filter(phone_type.end <= max_time)
        q = q.columns(phone_type.label.column_name('label'),
                      phone_type.begin.column_name('begin'),
                      phone_type.end.column_name('end'),
                      phone_type.speaker.name.column_name('speaker')).order_by(phone_type.begin)
        phones = [(x['label'], x['begin'],x['end'], x['speaker']) for x in q.all()]
        for time_point, value in intensity_track.items():
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
            label = None
            speaker = None
            for p in phones:
                if p[1] > time_point:
                    break
                label = p[0]
                speaker = p[-1]
            else:
                label = None
                speaker = None
            if speaker is None:
                continue
            t_dict = {'speaker': speaker}
            t_dict.update(tag_dict)
            fields = {'Intensity': value, 'phone':label}
            d = {'measurement': 'intensity',
                'tags': t_dict,
                "time": to_nano(time_point),
                "fields": fields
                }
            data.append(d)
        self.acoustic_client().write_points(data, batch_size=1000)

    def has_formants(self, discourse, source = None):
        """
        Return whether a discourse has any formant values associated with it
        """
        client = self.acoustic_client()
        if source is None:
            source = self.config.pitch_algorithm
        result = client.query('''select "F1" from "formants" WHERE "discourse" = '{}' AND "source" = '{}' LIMIT 1;'''.format(discourse, source))
        if len(result) == 0:
            return False
        return True

    def has_pitch(self, discourse, source = None):
        """
        Return whether a discourse has any pitch values associated with it
        """
        client = self.acoustic_client()
        if source is None:
            source = self.config.pitch_algorithm
        result = client.query('''select "F0" from "pitch" WHERE "discourse" = '{}' AND "source" = '{}' LIMIT 1;'''.format(discourse, source))
        if len(result) == 0:
            return False
        return True

    def has_intensity(self, discourse, source = None):
        client = self.acoustic_client()
        if source is None:
            source = self.config.intensity_algorithm
        result = client.query('''select "Intensity" from "intensity" WHERE "discourse" = '{}' AND "source" = '{}' LIMIT 1;'''.format(discourse, source))
        if len(result) == 0:
            return False
        return True

    def get_acoustic_statistic(self, acoustic_measure, statistic, by_speaker = False, source = None):
        client = self.acoustic_client()
        acoustic_measure = acoustic_measure.lower()
        measures = []
        template = statistic + '("{}")'
        if acoustic_measure == 'pitch':
            measures.append(template.format('F0'))
            if source is None:
                source = self.config.pitch_algorithm
        elif acoustic_measure == 'formants':
            measures.append(template.format('F1'))
            measures.append(template.format('F2'))
            measures.append(template.format('F3'))
            if source is None:
                source = self.config.formant_algorithm
        elif acoustic_measure == 'intensity':
            measures.append(template.format('Intensity'))
            if source is None:
                source = self.config.intensity_algorithm
        else:
            raise(ValueError('Acoustic measure must be one of: pitch, formants, or intensity.'))
        group_by = ['"phone"']
        if by_speaker:
            group_by.append('"speaker"')
        group_by = ', '.join(group_by)
        query = '''select {} from "{}"
                        where "source" = '{}' group by {};'''.format(', '.join(measures), acoustic_measure, source, group_by)
        result = client.query(query)
        if by_speaker:
            if acoustic_measure == 'formants':
                result = {(k[1]['speaker'], k[1]['phone']): [x[1] for x in sorted(list(v)[0].items()) if x[0] != 'time'] for k, v in result.items()}
            else:
                result = {(k[1]['speaker'], k[1]['phone']): list(v)[0][statistic] for k, v in result.items()}
        else:
            if acoustic_measure == 'formants':
                result = {k[1]['phone']: [x[1] for x in sorted(list(v)[0].items()) if x[0] != 'time'] for k, v in result.items()}
            else:
                result = {k[1]['phone']: list(v)[0][statistic] for k, v in result.items()}
        return result

    def relativize_pitch(self, by_speaker = True, source = None):
        if source is None:
            source = self.config.pitch_algorithm
        client = self.acoustic_client()
        phone_type = getattr(self, self.phone_name)

        summary_data = {}
        for p in self.lexicon.phones:
            if by_speaker:
                query = '''select mean("F0"), stddev("F0") from "pitch" where "phone" = '{}' and "source" = '{}' group by "speaker";'''.format(p, source)
                result = client.query(query)
                for k,v in result.items():
                    v = list(v)
                    summary_data[(k[1]['speaker'], p)] = v[0]['mean'], v[0]['stddev']

            else:
                query = '''select mean("F0"), stddev("F0") from "pitch" where "phone" = '{}' and "source" = '{}';'''.format(p, source)
                result = client.query(query)
                for k,v in result.items():
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

    def relativize_intensity(self, by_speaker = True, source = None):
        if source is None:
            source = self.config.intensity_algorithm
        client = self.acoustic_client()
        phone_type = getattr(self, self.phone_name)

        summary_data = {}
        for p in self.lexicon.phones:
            if by_speaker:
                query = '''select mean("Intensity"), stddev("Intensity") from "intensity" where "phone" = '{}' and "source" = '{}' group by "speaker";'''.format(p, source)
                result = client.query(query)
                for k,v in result.items():
                    v = list(v)
                    summary_data[(k[1]['speaker'], p)] = v[0]['mean'], v[0]['stddev']

            else:
                query = '''select mean("Intensity"), stddev("Intensity") from "intensity" where "phone" = '{}' and "source" = '{}';'''.format(p, source)
                result = client.query(query)
                for k,v in result.items():
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

    def relativize_formants(self, by_speaker = True, source = None):
        if source is None:
            source = self.config.formant_algorithm
        client = self.acoustic_client()
        phone_type = getattr(self, self.phone_name)

        summary_data = {}
        for p in self.lexicon.phones:
            if by_speaker:
                query = '''select mean("F1"), stddev("F1"), mean("F2"), stddev("F2"), mean("F3"), stddev("F3") from "formants" where "phone" = '{}' and "source" = '{}' group by "speaker";'''.format(p, source)
                result = client.query(query)
                for k,v in result.items():
                    v = list(v)
                    summary_data[(k[1]['speaker'], p)] = v[0]['mean'], v[0]['stddev'], v[0]['mean_1'], v[0]['stddev_1'], v[0]['mean_2'], v[0]['stddev_2']

            else:
                query = '''select mean("F1"), stddev("F1"), mean("F2"), stddev("F2"), mean("F3"), stddev("F3") from "formants" where "phone" = '{}' and "source" = '{}';'''.format(p, source)
                result = client.query(query)
                for k,v in result.items():
                    v = list(v)
                    summary_data[p] = v[0]['mean'], v[0]['stddev'], v[0]['mean_1'], v[0]['stddev_1'], v[0]['mean_2'], v[0]['stddev_2']

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