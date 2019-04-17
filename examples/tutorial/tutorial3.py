import os
from polyglotdb import CorpusContext

# Initial query

with CorpusContext('pg_tutorial') as c:
    q = c.query_graph(c.syllable)
    q = q.filter(c.syllable.stress == '1')

    q = q.filter(c.syllable.begin == c.syllable.word.begin)

    q = q.filter(c.syllable.word.end == c.syllable.word.utterance.end)

    q = q.columns(c.syllable.label.column_name('syllable'),
                  c.syllable.duration.column_name('syllable_duration'),
                  c.syllable.word.label.column_name('word'),
                  c.syllable.word.begin.column_name('word_begin'),
                  c.syllable.word.end.column_name('word_end'),
                  c.syllable.word.num_syllables.column_name('word_num_syllables'),
                  c.syllable.word.stress_pattern.column_name('word_stress_pattern'),
                  c.syllable.word.utterance.speech_rate.column_name('utterance_speech_rate'),
                  c.syllable.speaker.name.column_name('speaker'),
                  c.syllable.speaker.gender.column_name('speaker_gender'),
                  c.syllable.discourse.name.column_name('file'),
                  )

    q = q.limit(10)
    results = q.all()
    print(results)


# Export query

export_path = '/mnt/e/pg_tutorial.csv'

with CorpusContext('pg_tutorial') as c:
    q = c.query_graph(c.syllable)
    q = q.filter(c.syllable.stress == 1)

    q = q.filter(c.syllable.begin == c.syllable.word.begin)

    q = q.filter(c.syllable.word.end == c.syllable.word.utterance.end)

    q = q.columns(c.syllable.label.column_name('syllable'),
                  c.syllable.duration.column_name('syllable_duration'),
                  c.syllable.word.label.column_name('word'),
                  c.syllable.word.begin.column_name('word_begin'),
                  c.syllable.word.end.column_name('word_end'),
                  c.syllable.word.num_syllables.column_name('word_num_syllables'),
                  c.syllable.word.stress_pattern.column_name('word_stress_pattern'),
                  c.syllable.word.utterance.speech_rate.column_name('utterance_speech_rate'),
                  c.syllable.speaker.name.column_name('speaker'),
                  c.syllable.speaker.gender.column_name('speaker_gender'),
                  c.syllable.discourse.name.column_name('file'),
                  )
    q.to_csv(export_path)
