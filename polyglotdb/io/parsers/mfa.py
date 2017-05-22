#from __future__ import absolute_import
import os

from textgrid import TextGrid, IntervalTier

from polyglotdb.io.parsers.textgrids import TextgridParser

from polyglotdb.exceptions import TextGridError
from polyglotdb.io.helper import find_wav_path

from polyglotdb.io.parsers.base import DiscourseData

from polyglotdb.io.parsers.speaker import DirectorySpeakerParser


class MfaParser(TextgridParser):
    def __init__(self, annotation_types, hierarchy, make_transcription=True,
                 make_label=False,
                 stop_check=None, call_back=None):
        super(MfaParser, self).__init__(annotation_types, hierarchy, make_transcription,
                                        make_label, stop_check, call_back)
        self.speaker_parser = DirectorySpeakerParser()

    def _is_valid(self, tg):
        format_1 = False
        format_2 = False
        # (1) Checks for words ; phones format
        if tg.tiers[0].name == "words" and tg.tiers[1].name == "phones" and len(tg.tiers) == 2:
            format_1 = True
        # (2) Checks for Speaker1 - words; Speaker1 - phones; Speaker2 - words; Speaker2 - phones format
        else:
            if len(tg.tiers) % 2 == 0:  # Get into pairs and check each pair
                pairs = []
                pair = []
                for index, ti in enumerate(tg.tiers):
                    if index % 2 == 0:
                        pair = []
                        pair.append(ti.name)
                    else:
                        pair.append(ti.name)
                        pairs.append(pair)
                for pair in pairs:
                    if " - " in pair[0] and " - " in pair[1]:
                        item1 = pair[0].split(" - ")
                        item2 = pair[1].split(" - ")
                        if item1[0] == item2[0]:
                            if item1[1] == "words" and item2[1] == "phones":
                                format_2 = True
                            else:
                                format_2 = False
                                break
                        else:
                            format_2 = False
                            break
                    else:
                        format_2 = False
                        break
            else:
                format_2 = False

        if (format_1 == True or format_2 == True) and not (format_1 == True and format_2 == True):
            return True
        else:
            return False
                
                




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
            if ti.name == 'words':
                self.annotation_types[0].add(((x.mark.strip(), x.minTime, x.maxTime) for x in ti))
            elif ti.name == 'phones':
                self.annotation_types[1].add(((x.mark.strip(), x.minTime, x.maxTime) for x in ti))
        pg_annotations = self._parse_annotations(types_only)

        data = DiscourseData(name, pg_annotations, self.hierarchy)
        for a in self.annotation_types:
            a.reset()

        data.wav_path = find_wav_path(path)
        return data
