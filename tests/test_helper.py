
from annograph.helper import align_phones

from annograph.io.helper import BaseAnnotation

def test_align():
    cats = [BaseAnnotation('k'), BaseAnnotation('ae'),BaseAnnotation('t'),BaseAnnotation('s')]
    cats2 = [BaseAnnotation('k'),BaseAnnotation('ae'),BaseAnnotation('s')]
    assert(align_phones(cats, cats2) ==
                        (cats, [BaseAnnotation('k'),BaseAnnotation('ae'), '-', BaseAnnotation('s')]))

    probably = [BaseAnnotation('p'),BaseAnnotation('r'),BaseAnnotation('aa'),BaseAnnotation('b'),
                BaseAnnotation('ah'),BaseAnnotation('b'),BaseAnnotation('l'),BaseAnnotation('iy')]
    probably2 = [BaseAnnotation('p'),BaseAnnotation('r'),BaseAnnotation('ah'),BaseAnnotation('l'),BaseAnnotation('iy')]
    assert(align_phones(probably, probably2) ==
                        (probably, [BaseAnnotation('p'),BaseAnnotation('r'),'-','-',
                                    BaseAnnotation('ah'),'-',BaseAnnotation('l'),
                                    BaseAnnotation('iy')]))
