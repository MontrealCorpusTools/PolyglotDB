
from annograph.helper import inspect_discourse, align_phones

def test_corpus_timed(corpus_data_timed):
    base_levels, has_name, has_labels, process_order = inspect_discourse(corpus_data_timed[0])
    assert(base_levels == ['phone'])
    assert(process_order == ['word','line'])

def test_corpus_untimed(corpus_data_untimed):
    base_levels, has_name, has_labels, process_order = inspect_discourse(corpus_data_untimed[0])
    assert(base_levels == ['phone'])
    assert(process_order == ['morpheme','word','line'])

def test_corpus_srur(corpus_data_ur_sr):
    base_levels, has_name, has_labels, process_order = inspect_discourse(corpus_data_ur_sr[0])
    assert(set(base_levels) == set(['ur','sr']))
    assert(process_order == ['word','line'])

def test_align():
    cats = [{'label':'k'}, {'label':'ae'},{'label':'t'},{'label':'s'}]
    cats2 = [{'label':'k'},{'label':'ae'},{'label':'s'}]
    assert(align_phones(cats, cats2) ==
                        (cats, [{'label':'k'},{'label':'ae'}, '-', {'label':'s'}]))

    probably = [{'label':'p'},{'label':'r'},{'label':'aa'},{'label':'b'},
                {'label':'ah'},{'label':'b'},{'label':'l'},{'label':'iy'}]
    probably2 = [{'label':'p'},{'label':'r'},{'label':'ah'},{'label':'l'},{'label':'iy'}]
    assert(align_phones(probably, probably2) ==
                        (probably, [{'label':'p'},{'label':'r'},'-','-',
                                    {'label':'ah'},'-',{'label':'l'},
                                    {'label':'iy'}]))
