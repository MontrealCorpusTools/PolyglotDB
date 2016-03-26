import os
import pytest

from polyglotdb import CorpusContext
from polyglotdb.utils import add_default_annotations, update_sound_files

@pytest.mark.xfail
def test_add_default_voicing_annotations(acoustic_config):
    with CorpusContext(acoustic_config) as c:
        stops = ('p', 't', 'k', 'b', 'd', 'g')

        q = c.query_graph(c.phone).filter(c.phone.label.in_(stops))
        q = q.columns(c.phone.id)
        num = q.count()
        assert(num == 28)

        defaults = [('closure', 0, 0.5, {'checked': False}),
                    ('release', 0.5, 1, {'checked': False})]
        add_default_annotations(c, 'phone', defaults, subset = stops)

        q = c.query_graph(c.phone).filter(c.phone.label.in_(stops))

        for a in q.all():
            assert(len(a.closure) == 1)
            assert(len(a.release) == 1)
            assert(all(not x.checked for x in a.closure))
            assert(all(not x.checked for x in a.release))

        assert(q.count() == 28)

        q = c.query_graph(c.phone).filter(c.phone.label.in_(stops))
        q = q.preload(c.phone.closure, c.phone.release)
        assert(q.count() == 28)
        for a in q.all():
            print([(x.begin, x.end, x._type) for x in a.closure])
            print([(x.begin, x.end, x._type) for x in a.release])
            assert(len(a.closure) == 1)
            assert(len(a.release) == 1)


def test_update_sound_files(acoustic_config, textgrid_test_dir):
    with CorpusContext(acoustic_config) as c:
        update_sound_files(c, textgrid_test_dir)
        expected_path = os.path.join(textgrid_test_dir, 'acoustic_corpus.wav')
        assert(c.discourse_sound_file('acoustic_corpus').filepath == expected_path)
