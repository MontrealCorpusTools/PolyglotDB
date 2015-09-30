
import pytest
import os

from polyglotdb.io.text_transcription import (load_discourse_transcription,
                                                load_directory_transcription,
                                                inspect_discourse_transcription,
                                                export_discourse_transcription)

from polyglotdb.exceptions import DelimiterError

from polyglotdb.corpus import CorpusContext

@pytest.mark.xfail
def test_export_transcription(graph_db, export_test_dir):
    d = generate_discourse(unspecified_test_corpus)
    export_path = os.path.join(export_test_dir, 'export_transcription.txt')
    export_discourse_transcription(d, export_path, single_line = False)

    with CorpusContext(corpus_name = 'exported_transcription', **graph_db) as c:
        c.reset()
        load_discourse_transcription(c, export_path)
    words = sorted([x for x in unspecified_test_corpus], key = lambda x: x.transcription)
    words2 = sorted([x for x in d2.lexicon], key = lambda x: x.transcription)
    for i,w in enumerate(words):
        w2 = words2[i]
        assert(w.transcription == w2.transcription)
        assert(w.frequency == w2.frequency)


def text_delim_error(graph_db, text_transcription_test_dir):
    transcription_path = os.path.join(text_transcription_test_dir, 'text_transcription.txt')
    with CorpusContext(corpus_name = 'transcription_test_raises', **graph_db) as c:
        with pytest.raises(DelimiterError):
            load_discourse_transcription(c,
                                transcription_path," ",[],
                                trans_delimiter = ',')


def text_transcription_directory(graph_db, text_transcription_test_dir):
    annotation_types = inspect_discourse_transcription(text_transcription_test_dir)
    with CorpusContext(corpus_name = 'transcription_test_directory', **graph_db) as c:
        load_directory_transcription(c, text_transcription_test_dir)

def test_load_transcription_morpheme(graph_db, text_transcription_test_dir):
    transcription_morphemes_path = os.path.join(text_transcription_test_dir,
                                'text_transcription_morpheme_boundaries.txt')
    ats = inspect_discourse_transcription(transcription_morphemes_path)
    ats[0].morph_delimiters = set('-=')
    with CorpusContext(corpus_name = 'transcription_morpheme', **graph_db) as c:
        c.reset()
        load_discourse_transcription(c,transcription_morphemes_path, ats)

    assert(c.lexicon['cab'].frequency == 2)
    assert(str(c.lexicon['cab'].transcription) == 'c.a.b')

