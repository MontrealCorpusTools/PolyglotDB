
import pytest
import os

from polyglotdb.io.text_spelling import (load_discourse_spelling,
                                                load_directory_spelling,
                                                inspect_discourse_spelling,
                                                export_discourse_spelling)
from polyglotdb.io.text_transcription import (load_discourse_transcription,
                                                load_directory_transcription,
                                                inspect_discourse_transcription,
                                                export_discourse_transcription)

from polyglotdb.exceptions import DelimiterError

from polyglotdb.corpus import CorpusContext

@pytest.mark.xfail
def test_export_transcription(graph_db, export_test_dir, unspecified_test_corpus):
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

def test_load_spelling_no_ignore(graph_db, text_test_dir):
    spelling_path = os.path.join(text_test_dir, 'text_spelling.txt')

    with CorpusContext(corpus_name = 'spelling_no_ignore', **graph_db) as c:
        c.reset()
        load_discourse_spelling(c,spelling_path)

    assert(c.lexicon['ab'].frequency == 2)

def test_export_spelling(graph_db, export_test_dir):

    export_path = os.path.join(export_test_dir, 'export_spelling.txt')
    with CorpusContext(corpus_name = 'spelling_no_ignore', **graph_db) as c:
        export_discourse_spelling(c, 'text_spelling', export_path, single_line = False)

    with open(export_path,'r') as f:
        assert(f.read() == 'ab cab\'d ad ab ab.')


def test_load_spelling_ignore(graph_db, text_test_dir):
    spelling_path = os.path.join(text_test_dir, 'text_spelling.txt')
    a = inspect_discourse_spelling(spelling_path)
    a[0].ignored_characters = set(["'",'.'])
    with CorpusContext(corpus_name = 'spelling_ignore', **graph_db) as c:
        c.reset()
        load_discourse_spelling(c, spelling_path, a)

    assert(c.lexicon['ab'].frequency == 3)
    assert(c.lexicon['cabd'].frequency == 1)

def text_test_dir(graph_db, text_test_dir):
    transcription_path = os.path.join(text_test_dir, 'text_transcription.txt')
    with CorpusContext(corpus_name = 'transcription_test_raises', **graph_db) as c:
        c.reset()
        with pytest.raises(DelimiterError):
            load_discourse_transcription(c,
                                transcription_path," ",[],
                                trans_delimiter = ',')

        load_discourse_transcription(c,transcription_path)

    assert(sorted(c.lexicon.inventory) == sorted(['#','a','b','c','d']))

def test_load_transcription_morpheme(graph_db, text_test_dir):
    transcription_morphemes_path = os.path.join(text_test_dir, 'text_transcription_morpheme_boundaries.txt')
    ats = inspect_discourse_transcription(transcription_morphemes_path)
    ats[0].morph_delimiters = set('-=')
    with CorpusContext(corpus_name = 'transcription_morpheme', **graph_db) as c:
        c.reset()
        load_discourse_transcription(c,transcription_morphemes_path, ats)

    assert(c.lexicon['cab'].frequency == 2)
    assert(str(c.lexicon['cab'].transcription) == 'c.a.b')

