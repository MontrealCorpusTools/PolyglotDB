"""Sonority classes, following Clements (1990).

Clements defines sonority through the major class features [sonorant], [approximant],
and [vocoid] (the converse of [consonantal]). The sonority rank of a nonsyllabic
segment is the number of plus-specifications it has (ex. 6, p. 292):

=========  ========  ======  ======  ======
feature    O         N       L       G/V
=========  ========  ======  ======  ======
vocoid     -         -       -       +
approx.    -         -       +       +
sonorant   -         +       +       +
rank       0         1       2       3
=========  ========  ======  ======  ======

A segment designated [+syllabic] ranks one higher than its nonsyllabic counterpart,
so the syllabic hierarchy is O < N < L < V = 1 < 2 < 3 < 4 (ex. 7). Because glides
and vowels differ only in syllabicity, they share one class here (`VOCOID`), and the
values of `SonorityClass` are the nonsyllabic ranks. Syllabicity is not a property
of the segment: it is assigned elsewhere, and a syllabic segment's rank is its class
value plus one.
"""

from enum import IntEnum


class SonorityClass(IntEnum):
    """Major sonority classes; each value is the class's nonsyllabic rank."""

    OBSTRUENT = 0
    NASAL = 1
    LIQUID = 2
    VOCOID = 3  # glides and vowels
