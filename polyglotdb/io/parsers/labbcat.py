from .aligner import AlignerParser


class LabbCatParser(AlignerParser):
    name = 'LabbCat'
    word_label = 'transcript'
    phone_label = 'segment'
    speaker_first = False
