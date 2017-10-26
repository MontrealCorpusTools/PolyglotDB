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
        found_word = False
        found_phone = False
        invalid = True
        multiple_speakers = False
        for ti in tg.tiers:
            if '-' in ti.name:
                multiple_speakers = True
                break
        if multiple_speakers:
            speakers = {x.name.split('-')[0].strip() for x in tg.tiers}
            found_words = {x: False for x in speakers}
            found_phones = {x: False for x in speakers}
            for ti in tg.tiers:
                if '-' not in ti.name:
                    continue
                speaker, name = ti.name.split('-')
                speaker = speaker.strip()
                name = name.strip()
                if name.startswith('word'):
                    found_words[speaker] = True
                elif name.startswith('word'):
                    found_phones[speaker] = True
            found_word = all(found_words.values())
            found_phone = all(found_words.values())
        else:
            for ti in tg.tiers:
                if ti.name.startswith('word'):
                    found_word = True
                elif ti.name.startswith('phone'):
                    found_phone = True
        return multiple_speakers, found_word and found_phone

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

        multiple_speakers, is_valid = self._is_valid(tg)

        if not is_valid:
            raise (TextGridError('This file cannot be parsed by the MFA parser.'))
        name = os.path.splitext(os.path.split(path)[1])[0]

        # Format 1
        if not multiple_speakers:
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

        # Format 2
        else:
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
                    for ti in tg.tiers:
                        try:
                            speaker, type = ti.name.split(' - ')
                        except ValueError:
                            continue
                        if speaker in speaker_channel_mapping:
                            continue
                        for i, c in enumerate(cutoffs):
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
                if type.startswith('word'):
                    type = 'word'
                elif type.startswith('phone'):
                    type = 'phone'
                if len(ti) == 1 and ti[0].mark.strip() == '':
                    continue
                at = OrthographyTier(type, type)
                at.speaker = speaker
                at.add(((x.mark.strip(), x.minTime, x.maxTime) for x in ti))
                self.annotation_types.append(at)
            pg_annotations = self._parse_annotations(types_only)
            data = DiscourseData(name, pg_annotations, self.hierarchy)
            data.speaker_channel_mapping = speaker_channel_mapping

            self.annotation_types = dummy

        data.wav_path = find_wav_path(path)
        return data
