from collections import Counter
from textgrid import TextGrid, IntervalTier
from .aligner import AlignerParser


class MausParser(AlignerParser):
    name = 'Maus'
    word_label = 'ort'
    phone_label = 'mau'

