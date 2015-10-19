
from polyglotdb.sql.models import SoundFile, Pitch

from acousticsim.representations.pitch import Pitch as ASPitch

def acoustic_analysis(corpus_context):
    sound_files = corpus_context.sql_session.query(SoundFile).all()
    for sf in sound_files:
        pitch = ASPitch(sf.filepath, 0.01, (75,500))
        pitch.process()
        for time, value in pitch.items():
            p = Pitch(sound_file = sf, time = time, F0 = value[0], source = 'acousticsim')
            corpus_context.sql_session.add(p)
