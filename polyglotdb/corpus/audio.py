import os

from .base import BaseContext

from ..acoustics import acoustic_analysis

from ..sql.models import Discourse, SoundFile

from ..acoustics.query import AcousticQuery

class AudioContext(BaseContext):
    def query_acoustics(self, graph_query):
        """
        Checks for soundfiles,
        Makes an AcousticQuery object

        Parameters
        ----------
        graph_query : : class: `polyglotdb.graph.GraphQuery`
            the query to be run

        Returns
        -------
        AcousticQuery : : class `polyglotdb.acoustics.AcousticQuery`

        """
        if not self.has_sound_files:
            raise(NoSoundFileError)
        return AcousticQuery(self, graph_query)

    def analyze_acoustics(self):
        """ runs an acoustic analysis """
        if not self.has_sound_files:
            raise(NoSoundFileError)
        acoustic_analysis(self)

    def discourse_sound_file(self, discourse):
        """
        Gets the first sound file from the discourse

        Parameters
        ----------
        discourse : str
            discourse name

        Returns
        -------
        sound_file : : class: `polyglotdb.sql.models.SoundFile`
            the first soundfile
        """
        q = self.sql_session.query(SoundFile).join(SoundFile.discourse)
        q = q.filter(Discourse.name == discourse)
        sound_file = q.first()
        return sound_file

    def has_all_sound_files(self):
        """
        Checks if it has run before, then checks if all sound files exist for each discourse name

        Returns
        -------
        _has_all_sound_files : bool
            True if sound file exists for each discourse name in corpus
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
        Checks if it has run before, then checks if there are any sound files

        Returns
        -------
        _has_sound_files : bool
            True if there are any sound files at all, false if there aren't
        """
        if self._has_sound_files is None:
            self._has_sound_files = self.sql_session.query(SoundFile).first() is not None
        return self._has_sound_files
