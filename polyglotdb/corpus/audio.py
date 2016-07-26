import os

from ..acoustics import acoustic_analysis

from ..sql.models import SoundFile, Pitch, Formants, Discourse

from ..graph.discourse import DiscourseInspecter

def sanitize_formants(value):
    try:
        f1 = value[0][0]
    except TypeError:
        f1 = value[0]
    if f1 is None:
        f1 = 0
    try:
        f2 = value[1][0]
    except TypeError:
        f2 = value[1]
    if f2 is None:
        f2 = 0
    try:
        f3 = value[2][0]
    except TypeError:
        f3 = value[2]
    if f3 is None:
        f3 = 0
    return f1, f2, f3

class AudioContext(object):
    """
    Class that contains methods for dealing with audio files for corpora
    """
    def analyze_acoustics(self):
        """
        Runs all acoustic analyses for the corpus.
        """
        if not self.has_sound_files:
            raise(NoSoundFileError)
        acoustic_analysis(self)

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
        if source is None:
            source = self.config.formant_algorithm
        q = self.sql_session.query(Formants).join(SoundFile).join(Discourse)
        q = q.filter(Discourse.name == discourse)
        q = q.filter(Formants.source == source)
        if begin is not None:
            q = q.filter(Formants.time >= begin)
        if end is not None:
            q = q.filter(Formants.time <= end)
        q = q.filter(Formants.channel == channel)
        q = q.order_by(Formants.time)
        listing = q.all()
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
        if source is None:
            source = self.config.pitch_algorithm
        q = self.sql_session.query(Pitch).join(SoundFile).join(Discourse)
        q = q.filter(Discourse.name == discourse)
        q = q.filter(Pitch.source == source)
        if begin is not None:
            q = q.filter(Pitch.time >= begin)
        if end is not None:
            q = q.filter(Pitch.time <= end)
        q = q.filter(Pitch.channel == channel)
        q = q.order_by(Pitch.time)
        listing = q.all()
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
        for timepoint, value in formant_track.items():
            f1, f2, f3 = sanitize_formants(value)
            f = Formants(sound_file = sound_file, time = timepoint, F1 = f1,
                    F2 = f2, F3 = f3, channel = channel, source = source)
            self.sql_session.add(f)

    def save_pitch(self, sound_file, pitch_track, channel = 0, source = None):
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
        for timepoint, value in pitch_track.items():
            try:
                value = value[0]
            except TypeError:
                pass
            p = Pitch(sound_file = sound_file, time = timepoint, F0 = value, channel = channel, source = source)
            self.sql_session.add(p)

    def has_formants(self, discourse, source = None):
        """
        Return whether a discourse has any formant values associated with it
        """
        q = self.sql_session.query(Formants).join(SoundFile).join(Discourse)
        q = q.filter(Discourse.name == discourse)
        q = q.filter(Formants.source == source)
        listing = q.first()
        if listing is None:
            return False
        return True

    def has_pitch(self, discourse, source = None):
        """
        Return whether a discourse has any pitch values associated with it
        """
        q = self.sql_session.query(Pitch).join(SoundFile).join(Discourse)
        q = q.filter(Discourse.name == discourse)
        q = q.filter(Pitch.source == source)
        listing = q.first()
        if listing is None:
            return False
        return True
