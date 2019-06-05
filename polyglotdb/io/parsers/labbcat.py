from collections import Counter
from textgrid import TextGrid, IntervalTier
from .aligner import AlignerParser

from polyglotdb.io.parsers.speaker import FilenameSpeakerParser


class LabbCatParser(AlignerParser):
    name = 'LabbCat'
    word_label = 'transcript'
    phone_label = 'segment'
    speaker_first = False

    def __init__(self, annotation_tiers, hierarchy, make_transcription=True,
                 stop_check=None, call_back=None):
        super(AlignerParser, self).__init__(annotation_tiers, hierarchy, make_transcription,
                                        False, stop_check, call_back)
        self.speaker_parser = FilenameSpeakerParser(0)

    def load_textgrid(self, path):
        tg = TextGrid(strict=False)
        try:
            tg.read(path)
            new_tiers = []
            dup_tiers_maxes = {k:0 for k,v in Counter([t.name for t in tg.tiers]).items() if v > 1}
            dup_tiers_inds = {k:0 for k in dup_tiers_maxes.keys()}

            for i, t in enumerate(tg.tiers):
                if t.name in dup_tiers_maxes:
                    if len(t) > dup_tiers_maxes[t.name]:
                        dup_tiers_maxes[t.name] = len(t)
                        dup_tiers_inds[t.name] = i
            for i, t in enumerate(tg.tiers):
                if t.name in dup_tiers_maxes:
                    if i != dup_tiers_inds[t.name]:
                        continue
                new_tiers.append(t)
            tg.tiers = new_tiers
            return tg
        except Exception as e:
            print('There was an issue parsing {}:'.format(path))
            raise
