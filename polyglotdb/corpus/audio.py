import os
from datetime import datetime
from decimal import Decimal

from influxdb import InfluxDBClient

from ..acoustics import acoustic_analysis

from ..sql.models import SoundFile, Discourse

from ..graph.discourse import DiscourseInspecter

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

def to_nano(seconds):
    if not isinstance(seconds,Decimal):
        seconds = Decimal(seconds).quantize(Decimal('0.001'))
    return int(seconds * Decimal('1e9'))

def to_seconds(timestring):
    try:
        d = datetime.strptime(timestring, '%Y-%m-%dT%H:%M:%S.%fZ')
    except:
        d = datetime.strptime(timestring, '%Y-%m-%dT%H:%M:%SZ')

    s = 60*60*d.hour + 60*d.minute + d.second + d.microsecond / 1e6
    s = Decimal(s).quantize(Decimal('0.001'))
    return s

class AudioContext(object):
    """
    Class that contains methods for dealing with audio files for corpora
    """
    def analyze_acoustics(self, stop_check = None, call_back = None):
        """
        Runs all acoustic analyses for the corpus.
        """
        if not self.has_sound_files:
            raise(NoSoundFileError)
        acoustic_analysis(self, stop_check = stop_check, call_back = call_back)

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

    def get_formants(self, discourse, begin, end, channel = 0, source = None):
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
        channel : int, defaults to 0
            Specify a channel of the audio file
        source : str, defaults to None
            Specify a source of the formants, if None, use the formant_algorithm
            attribute of the CorpusContext

        Returns
        -------
        list
            List of results with fields for ``time``, ``F1``, ``F2``, and ``F3``
        """
        begin = Decimal(begin).quantize(Decimal('0.001'))
        end = Decimal(end).quantize(Decimal('0.001'))
        if source is None:
            source = self.config.formant_algorithm
        client = self.acoustic_client()
        result = client.query('''select "time", "F1", "F2", "F3" from "formants"
                        WHERE "discourse" = '{}' AND "source" = '{}'
                        AND "time" >= {}
                        AND "time" <= {};'''.format(discourse, source,
                                                to_nano(begin),to_nano(end)))
        listing = []
        for r in result.get_points('formants'):
            s = to_seconds(r['time'])
            listing.append((s, r['F1'], r['F2'], r['F3']))
        return listing


    def get_pitch(self, discourse, begin, end, channel = 0, source = None):
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
        channel : int, defaults to 0
            Specify a channel of the audio file
        source : str, defaults to None
            Specify a source of the formants, if None, use the pitch_algorithm
            attribute of the CorpusContext

        Returns
        -------
        list
            List of results with fields for ``time`` and ``F0``
        """
        begin = Decimal(begin).quantize(Decimal('0.001'))
        end = Decimal(end).quantize(Decimal('0.001'))
        if source is None:
            source = self.config.pitch_algorithm
        client = self.acoustic_client()
        query = '''select "time", "F0" from "pitch"
                        WHERE "discourse" = '{}' AND "source" = '{}'
                        AND "time" >= {}
                        AND "time" <= {};'''.format(discourse, source,
                                                to_nano(begin),to_nano(end))
        result = client.query(query)
        listing = []
        for r in result.get_points('pitch'):
            s = to_seconds(r['time'])
            listing.append((s, r['F0']))
        return listing

    def save_formants(self, sound_file, formant_track, channel = 0, source = None):
        """
        Save a formant track for a sound file

        Parameters
        ----------
        sound_file : str or :class:`~polyglotdb.sql.models.SoundFile`
            Discourse name or SoundFile object
        formant_track : dict
            Dictionary with times as keys and tuples of F1, F2, and F3 values as values
        channel : int, defaults to 0
            Specify a channel of the audio file
        source : str, defaults to None
            Specify a source of the formants, if None, use the formant_algorithm
            attribute of the CorpusContext
        """
        if isinstance(sound_file, str):
            sound_file = self.discourse_sound_file(sound_file)
        if sound_file is None:
           return
        if source is None:
            source = self.config.formant_algorithm
        data = []
        for timepoint, value in formant_track.items():
            f1, f2, f3 = sanitize_formants(value)
            d = {'measurement': 'formants',
                'tags': {'discourse': sound_file.discourse.name,
                        'channel': channel,
                        'source': source},
                "time": to_nano(timepoint),
                "fields": {'F1': f1,'F2':f2,'F3':f3}
                }
            data.append(d)
        self.acoustic_client().write_points(data)

    def save_pitch(self, sound_file, pitch_track, channel = None, speaker = None, source = None):
        """
        Save a pitch track for a sound file

        Parameters
        ----------
        sound_file : str or :class:`~polyglotdb.sql.models.SoundFile`
            Discourse name or SoundFile object
        pitch_track : dict
            Dictionary with times as keys and F0 values as values
        channel : int, defaults to 0
            Specify a channel of the audio file
        source : str, defaults to None
            Specify a source of the formants, if None, use the pitch_algorithm
            attribute of the CorpusContext
        """
        if isinstance(sound_file, str):
            sound_file = self.discourse_sound_file(sound_file)
        if sound_file is None:
           return
        if source is None:
            source = self.config.pitch_algorithm
        data = []
        tag_dict = {}
        if isinstance(sound_file, str):
            tag_dict['discourse'] = sound_file
        else:
            tag_dict['discourse'] = sound_file.discourse.name
        if speaker is not None:
            tag_dict['speaker'] = speaker
        if source is not None:
            tag_dict['source'] = source
        if channel is not None:
            tag_dict['channel'] = channel
        for timepoint, value in pitch_track.items():
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

            d = {'measurement': 'pitch',
                'tags': tag_dict,
                "time": to_nano(timepoint),
                "fields": {'F0': value}
                }
            data.append(d)
        self.acoustic_client().write_points(data)

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
