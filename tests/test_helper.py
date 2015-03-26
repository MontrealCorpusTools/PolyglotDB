
from annograph.helper import inspect_discourse, global_align

def test_corpus_timed(corpus_data_timed):
    base_levels, has_name, has_labels, hierarchy = inspect_discourse(corpus_data_timed[0])
    assert(base_levels == ['phones'])
    assert(hierarchy['words'] == ['phones'])

def test_corpus_untimed(corpus_data_untimed):
    base_levels, has_name, has_labels, hierarchy = inspect_discourse(corpus_data_untimed[0])
    assert(base_levels == ['phones'])
    assert(hierarchy['words'] == ['phones'])

def test_corpus_srur(corpus_data_ur_sr):
    base_levels, has_name, has_labels, hierarchy = inspect_discourse(corpus_data_ur_sr[0])
    assert(set(base_levels) == set(['ur','sr']))
    print(hierarchy)
    assert(hierarchy['lines'] == ['words'])
    assert(set(hierarchy['words']) == set(['ur','sr']))

def test_align():
    assert(global_align('COELANCANTH', 'PELICAN'),('COELANCANTH', '-PEL-ICAN--'))
