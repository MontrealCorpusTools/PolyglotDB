import pytest
import os

from polyglotdb.io import inspect_transcription

from polyglotdb.exceptions import DelimiterError

from polyglotdb import CorpusContext


@pytest.mark.xfail
def test_export_transcription(graph_db, export_test_dir):
    d = generate_discourse(unspecified_test_corpus)
    export_path = os.path.join(export_test_dir, 'export_transcription.txt')
    export_discourse_transcription(d, export_path, single_line=False)

    with CorpusContext('exported_transcription', **graph_db) as c:
        c.reset()
        parser = inspect_transcription(export_path)
        c.load(parser, export_path)
    words = sorted([x for x in unspecified_test_corpus], key=lambda x: x.transcription)
    words2 = sorted([x for x in d2.lexicon], key=lambda x: x.transcription)
    for i, w in enumerate(words):
        w2 = words2[i]
        assert (w.transcription == w2.transcription)
        # assert(w.frequency == w2.frequency)


@pytest.mark.xfail
def test_delim_error(graph_db, text_transcription_test_dir):
    transcription_path = os.path.join(text_transcription_test_dir, 'text_transcription.txt')
    parser = inspect_transcription(transcription_path)
    parser.annotation_tiers[0].trans_delimiter = ','
    with CorpusContext('transcription_test_raises', **graph_db) as c:
        with pytest.raises(DelimiterError):
            c.load(parser, transcription_path)


def test_transcription_directory(graph_db, text_transcription_test_dir):
    parser = inspect_transcription(text_transcription_test_dir)
    with CorpusContext('transcription_test_directory', **graph_db) as c:
        c.reset()
        c.load(parser, text_transcription_test_dir)


def test_load_transcription_morpheme(graph_db, text_transcription_test_dir):
    transcription_morphemes_path = os.path.join(text_transcription_test_dir,
                                                'text_transcription_morpheme_boundaries.txt')
    parser = inspect_transcription(transcription_morphemes_path)
    parser.annotation_tiers[0].morph_delimiters = set('-=')
    with CorpusContext('transcription_morpheme', **graph_db) as c:
        c.reset()
        c.load(parser, transcription_morphemes_path)

        # assert(c.lexicon['cab'].frequency == 2)
        q = c.query_lexicon(c.word).columns(c.word.label, c.word.transcription.column_name('transcription'))
        q = q.filter(c.word.label == 'cab')
        results = q.all()
        assert (results[0]['transcription'] == 'c.a.b')
