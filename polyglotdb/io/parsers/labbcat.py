from collections import Counter
from .aligner import AlignerParser

from polyglotdb.io.parsers.speaker import DirectorySpeakerParser
from praatio import tgio


class LabbCatParser(AlignerParser):
    """
    Parser for TextGrids exported from LaBB-CAT

    Parameters
    ----------
    annotation_tiers : list
        List of the annotation tiers to store data from the TextGrid
    hierarchy : Hierarchy
        Basic hierarchy of the TextGrid
    make_transcription : bool
        Flag for whether to add a transcription property to words based on phones they contain
    stop_check : callable
        Function to check for whether parsing should stop
    call_back : callable
        Function to report progress in parsing
    """
    name = 'LabbCat'
    word_label = 'transcript'
    phone_label = 'segment'
    speaker_first = False

    def __init__(self, annotation_tiers, hierarchy, make_transcription=True,
                 stop_check=None, call_back=None):
        super(AlignerParser, self).__init__(annotation_tiers, hierarchy, make_transcription,
                                        False, stop_check, call_back)
        self.speaker_parser = DirectorySpeakerParser()

    def load_textgrid(self, path):
        """
        Load a TextGrid file.  Additionally ignore duplicated tier names as they can sometimes be exported erroneously
        from LaBB-CAT.

        Parameters
        ----------
        path : str
            Path to the TextGrid file

        Returns
        -------
        :class:`~textgrid.TextGrid`
            TextGrid object
        """
        try:
            tg = tgio.openTextgrid(path)
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
