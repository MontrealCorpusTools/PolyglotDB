
from annograph.helper import inspect_discourse, global_align

def test_corpus_timed(corpus_data_timed):
    base_levels, has_name, has_labels, process_order = inspect_discourse(corpus_data_timed[0])
    assert(base_levels == ['phones'])
    assert(process_order == ['words','lines'])

def test_corpus_untimed(corpus_data_untimed):
    base_levels, has_name, has_labels, process_order = inspect_discourse(corpus_data_untimed[0])
    assert(base_levels == ['phones'])
    assert(process_order == ['words','lines'])

def test_corpus_srur(corpus_data_ur_sr):
    base_levels, has_name, has_labels, process_order = inspect_discourse(corpus_data_ur_sr[0])
    assert(set(base_levels) == set(['ur','sr']))
    assert(process_order == ['words','lines'])

def test_align():
    assert(global_align(['k','ae','t','s'], ['k','ae','s']) ==
                        (['k','ae','t','s'], ['k','ae','-','s']))

    assert(global_align(['p','r','aa','b','ah','b','l','iy'], ['p','r','ah','l','iy']) ==
                        (['p','r','aa','b','ah','b','l','iy'], ['p','r','-','-','ah','-','l','iy']))
