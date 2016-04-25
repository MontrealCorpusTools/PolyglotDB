
import os

from textgrid import TextGrid, IntervalTier

from .textgrid import TextgridParser

from polyglotdb.exceptions import TextGridError
from ..helper import find_wav_path

from .base import DiscourseData

class LabbCatParser(TextgridParser):
    def _is_valid(self, tg):
        found_word = False
        found_phone = False
        for ti in tg.tiers:
            if ti.name == 'transcrip':
                found_word = True
            elif ti.name == 'segment':
                found_phone = True
        return found_word and found_phone

    def parse_discourse(self, path):
        '''
        Parse a TextGrid file for later importing.

        Parameters
        ----------
        path : str
            Path to TextGrid file

        Returns
        -------
        :class:`~polyglotdb.io.discoursedata.DiscourseData`
            Parsed data from the file
        '''
        tg = TextGrid()
        tg.read(path)
        if not self._is_valid(tg):
            raise(TextGridError('This file cannot be parsed by the LaBB-CAT parser.'))
        name = os.path.splitext(os.path.split(path)[1])[0]

        if self.speaker_parser is not None:
            speaker = self.speaker_parser.parse_path(path)
        else:
            speaker = None

        for a in self.annotation_types:
            a.reset()
            a.speaker = speaker

        #Parse the tiers
        for i, ti in enumerate(tg.tiers):
            if ti.name == 'transcrip':
                self.annotation_types[0].add(((x.mark.strip(), x.minTime, x.maxTime) for x in ti))
            elif ti.name == 'segment':
                self.annotation_types[1].add(((x.mark.strip(), x.minTime, x.maxTime) for x in ti))
        pg_annotations = self._parse_annotations()

        data = DiscourseData(name, pg_annotations, self.hierarchy)
        for a in self.annotation_types:
            a.reset()

        data.wav_path = find_wav_path(path)
        return data