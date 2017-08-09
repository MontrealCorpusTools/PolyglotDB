import os

from textgrid import TextGrid, IntervalTier

from .textgrid import TextgridParser

from polyglotdb.exceptions import TextGridError
from ..helper import find_wav_path

from .base import DiscourseData

from .speaker import DirectorySpeakerParser


class MfaParser(TextgridParser):
    def __init__(self, annotation_types, hierarchy, make_transcription=True,
                 make_label=False,
                 stop_check=None, call_back=None):
        super(MfaParser, self).__init__(annotation_types, hierarchy, make_transcription,
                                        make_label, stop_check, call_back)
        self.speaker_parser = DirectorySpeakerParser()

    def _is_valid(self, tg):
        found_word = False
        found_phone = False
        for ti in tg.tiers:
            if ti.name.startswith('word'):
                found_word = True
            elif ti.name.startswith('phone'):
                found_phone = True
        return found_word and found_phone

    def parse_discourse(self, path, types_only=False):
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
            raise (TextGridError('This file cannot be parsed by the MFA parser.'))
        name = os.path.splitext(os.path.split(path)[1])[0]

        if self.speaker_parser is not None:
            speaker = self.speaker_parser.parse_path(path)
        else:
            speaker = None

        for a in self.annotation_types:
            a.reset()
            a.speaker = speaker

        # Parse the tiers
        for i, ti in enumerate(tg.tiers):
            if ti.name.startswith('word'):
                self.annotation_types[0].add(((x.mark.strip(), x.minTime, x.maxTime) for x in ti))
            elif ti.name.startswith('phone'):
                self.annotation_types[1].add(((x.mark.strip(), x.minTime, x.maxTime) for x in ti))
        pg_annotations = self._parse_annotations(types_only)

        data = DiscourseData(name, pg_annotations, self.hierarchy)
        for a in self.annotation_types:
            a.reset()

        data.wav_path = find_wav_path(path)
        return data
