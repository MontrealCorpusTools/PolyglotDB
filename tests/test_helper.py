
from annograph.helper import align_phones

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
