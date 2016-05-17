
import os

from textgrid import TextGrid, IntervalTier

from .textgrid import TextgridParser

from ..types.parsing import OrthographyTier

from polyglotdb.exceptions import TextGridError
from ..helper import find_wav_path

from .base import DiscourseData

class FaveParser(TextgridParser):
    def _is_valid(self, tg):
        found_words = {}
        found_phones = {}
        for ti in tg.tiers:
            try:
                speaker, type = ti.name.split(' - ')
            except ValueError:
                continue
            if speaker not in found_words:
                found_words[speaker] = False
            if speaker not in found_phones:
                found_phones[speaker] = False
            if type == 'word':
                found_words[speaker] = True
            elif type == 'phone':
                found_phones[speaker] = True
        if len(list(found_words.keys())) == 0:
            return False
        found_word = all(found_words.values())
        found_phone = all(found_phones.values())
        return found_word and found_phone

    def parse_discourse(self, path, types_only = False):
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
            raise(TextGridError('The file "{}" cannot be parsed by the FAVE parser.'.format(path)))
        name = os.path.splitext(os.path.split(path)[1])[0]

        dummy = self.annotation_types
        self.annotation_types = []

        #Parse the tiers
        for i, ti in enumerate(tg.tiers):
            try:
                speaker, type = ti.name.split(' - ')
            except ValueError:
                continue
            at = OrthographyTier(type, type)
            at.speaker = speaker
            at.add(((x.mark.strip(), x.minTime, x.maxTime) for x in ti))
            self.annotation_types.append(at)
        pg_annotations = self._parse_annotations(types_only)

        data = DiscourseData(name, pg_annotations, self.hierarchy)
        data.wav_path = find_wav_path(path)

        self.annotation_types = dummy

        return data
