#from __future__ import absolute_import
import os

from textgrid import TextGrid, IntervalTier

from .textgrid import TextgridParser
from ..types.parsing import OrthographyTier

from polyglotdb.exceptions import TextGridError
from ..helper import find_wav_path, get_n_channels
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
        result = "invalid"
         # (1) Checks for words ; phones format
        if tg.tiers[0].name == "word" and tg.tiers[1].name == "phone" and len(tg.tiers) == 2:
            result = "one_speaker"
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
                            if item1[1] == "word" and item2[1] == "phone":
                                result = "multiple_speakers"
                            else:
                                break
                        else:
                            break
                    else:
                        break
            #else:
            #    break

        return result


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

        # Turns "words" into "word" and "phones" into "phone", to be consistent with other code
        for ti in tg.tiers:
            if "words" in ti.name:
                ti.name = ti.name.replace("words", "word")
            elif "phones" in ti.name:
                ti.name = ti.name.replace("phones", "phone")

        if self._is_valid(tg) == "invalid":
            raise (TextGridError('This file cannot be parsed by the MFA parser.'))
        name = os.path.splitext(os.path.split(path)[1])[0]

        # Format 1
        if self._is_valid(tg) == "one_speaker":
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

        # Format 2
        elif self._is_valid(tg) == "multiple_speakers":
            dummy = self.annotation_types
            self.annotation_types = []
            wav_path = find_wav_path(path)
            speaker_channel_mapping = {}
            if wav_path is not None:
                n_channels = get_n_channels(wav_path)
                if n_channels > 1:
                    # Figure speaker-channel mapping
                    n_tiers = 0
                    for ti in tg.tiers:
                        try:
                            speaker, type = ti.name.split(' - ')
                        except ValueError:
                            continue
                        n_tiers += 1
                    ind = 0
                    cutoffs = [x / n_channels for x in range(1, n_channels)]
                    #print(cutoffs)
                    for ti in tg.tiers:
                        try:
                            speaker, type = ti.name.split(' - ')
                        except ValueError:
                            continue
                        if speaker in speaker_channel_mapping:
                            continue
                        #print(ind / n_channels)
                        for i, c in enumerate(cutoffs):
                            #print(c)
                            if ind / n_channels < c:
                                speaker_channel_mapping[speaker] = i
                                break
                        else:
                            speaker_channel_mapping[speaker] = i + 1
                        ind += 1

            # Parse the tiers
            for ti in tg.tiers:
                try:
                    speaker, type = ti.name.split(' - ')
                except ValueError:
                    continue
                if len(ti) == 1 and ti[0].mark.strip() == '':
                    continue
                at = OrthographyTier(type, type)
                at.speaker = speaker
                at.add(((x.mark.strip(), x.minTime, x.maxTime) for x in ti))
                self.annotation_types.append(at)
            pg_annotations = self._parse_annotations(types_only)

            data = DiscourseData(name, pg_annotations, self.hierarchy)
            data.speaker_channel_mapping = speaker_channel_mapping
            data.wav_path = wav_path

            self.annotation_types = dummy

            return data