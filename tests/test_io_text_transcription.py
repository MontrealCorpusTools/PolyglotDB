import os

from polyglotdb import CorpusContext
from polyglotdb.io import inspect_transcription


def test_transcription_directory(graph_db, text_transcription_test_dir):
    parser = inspect_transcription(text_transcription_test_dir)
    with CorpusContext("transcription_test_directory", **graph_db) as c:
        c.reset()
        c.load(parser, text_transcription_test_dir)


def test_load_transcription_morpheme(graph_db, text_transcription_test_dir):
    transcription_morphemes_path = os.path.join(
        text_transcription_test_dir, "text_transcription_morpheme_boundaries.txt"
    )
    parser = inspect_transcription(transcription_morphemes_path)
    parser.annotation_tiers[0].morph_delimiters = set("-=")
    with CorpusContext("transcription_morpheme", **graph_db) as c:
        c.reset()
        c.load(parser, transcription_morphemes_path)

        q = c.query_lexicon(c.word).columns(
            c.word.label, c.word.transcription.column_name("transcription")
        )
        q = q.filter(c.word.label == "cab")
        results = q.all()
        assert results[0]["transcription"] == "c.a.b"
