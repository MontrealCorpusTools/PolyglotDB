import os

from .base import BaseContext

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

class AudioContext(BaseContext):
    def analyze_acoustics(self):
        if not self.has_sound_files:
            raise(NoSoundFileError)
        acoustic_analysis(self)

    def inspect_discourse(self, discourse, begin = None, end = None):
        return DiscourseInspecter(self, discourse, begin, end)

    def discourse_sound_file(self, discourse):
        q = self.sql_session.query(SoundFile).join(SoundFile.discourse)
        q = q.filter(Discourse.name == discourse)
        sound_file = q.first()
        return sound_file

    def has_all_sound_files(self):
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
        if self._has_sound_files is None:
            self._has_sound_files = self.sql_session.query(SoundFile).first() is not None
        return self._has_sound_files

    def get_formants(self, discourse, begin, end, source = None):
        if source is None:
            source = self.config.formant_algorithm
        q = self.sql_session.query(Formants).join(SoundFile).join(Discourse)
        q = q.filter(Discourse.name == discourse)
        q = q.filter(Formants.source == self.config.formant_algorithm)
        if begin is not None:
            q = q.filter(Formants.time >= begin)
        if end is not None:
            q = q.filter(Formants.time <= end)
        q = q.order_by(Formants.time)
        listing = q.all()
        return listing

    def get_pitch(self, discourse, begin, end, source = None):
        if source is None:
            source = self.config.pitch_algorithm
        q = self.sql_session.query(Pitch).join(SoundFile).join(Discourse)
        q = q.filter(Discourse.name == discourse)
        q = q.filter(Pitch.source == self.config.pitch_algorithm)
        if begin is not None:
            q = q.filter(Pitch.time >= begin)
        if end is not None:
            q = q.filter(Pitch.time <= end)
        q = q.order_by(Pitch.time)
        listing = q.all()
        return listing

    def save_formants(self, sound_file, formant_track, source = None):
        if isinstance(sound_file, str):
            sound_file = self.discourse_sound_file(sound_file)
        #if sound_file is None:
        #   return
        if source is None:
            source = self.config.formant_algorithm
        for timepoint, value in formant_track.items():
            f1, f2, f3 = sanitize_formants(value)
            f = Formants(sound_file = sound_file, time = timepoint, F1 = f1,
                    F2 = f2, F3 = f3, source = source)
            self.sql_session.add(f)

    def save_pitch(self, sound_file, pitch_track, source = None):
        if isinstance(sound_file, str):
            sound_file = self.discourse_sound_file(sound_file)
        #if sound_file is None:
        #   return
        if source is None:
            source = self.config.pitch_algorithm
        for timepoint, value in pitch_track.items():
            try:
                value = value[0]
            except TypeError:
                pass
            p = Pitch(sound_file = sound_file, time = timepoint, F0 = value, source = source)
            self.sql_session.add(p)
