
import os


from .textgrid import TextgridParser
from ..types.parsing import OrthographyTier

from polyglotdb.exceptions import TextGridError
from ..helper import get_n_channels
from polyglotdb.io.helper import find_wav_path

from polyglotdb.io.parsers.base import DiscourseData

from polyglotdb.io.parsers.speaker import DirectorySpeakerParser


class AlignerParser(TextgridParser):
    """
    Base class for parsing TextGrid output from forced aligners.

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

    Attributes
    ----------
    word_label : str
        Label identifying word tiers
    phone_label : str
        Label identifying phone tiers
    name : str
        Name of the aligner the TextGrids are from
    speaker_first : bool
        Whether speaker names precede tier types in the TextGrid when multiple speakers are present
    """
    word_label = 'word'
    phone_label = 'phone'
    name = 'aligner'
    speaker_first = True

    def __init__(self, annotation_tiers, hierarchy, make_transcription=True,
                 stop_check=None, call_back=None):
        super(AlignerParser, self).__init__(annotation_tiers, hierarchy, make_transcription,
                                            False, stop_check, call_back)
        self.speaker_parser = DirectorySpeakerParser()

    def _is_valid(self, tg):
        found_word = False
        found_phone = False
        invalid = True
        multiple_speakers = False
        for i, tier_name in enumerate(tg.tierNameList):
            if ' - ' in tier_name:
                multiple_speakers = True
                break
        if multiple_speakers:
            if self.speaker_first:
                speakers = {tier_name.split(' - ')[0].strip().replace('/', '_').replace('\\', '_') for tier_name in tg.tierNameList if
                            ' - ' in tier_name}
            else:
                speakers = {tier_name.split(' - ')[1].strip().replace('/', '_').replace('\\', '_') for tier_name in tg.tierNameList if
                            ' - ' in tier_name}
            found_words = {x: False for x in speakers}
            found_phones = {x: False for x in speakers}
            for i, tier_name in enumerate(tg.tierNameList):
                if ' - ' not in tier_name:
                    continue
                if self.speaker_first:
                    speaker, name = tier_name.split(' - ')
                else:
                    name, speaker = tier_name.split(' - ')
                speaker = speaker.strip().replace('/', '_').replace('\\', '_')
                name = name.strip()
                if name.lower().startswith(self.word_label):
                    found_words[speaker] = True
                elif name.lower().startswith(self.phone_label):
                    found_phones[speaker] = True
            found_word = all(found_words.values())
            found_phone = all(found_words.values())
        else:
            for i, tier_name in enumerate(tg.tierNameList):
                if tier_name.lower().startswith(self.word_label):
                    found_word = True
                elif tier_name.lower().startswith(self.phone_label):
                    found_phone = True
        return multiple_speakers, found_word and found_phone

    def parse_discourse(self, path, types_only=False):
        """
        Parse a forced aligned TextGrid file for later importing.

        Parameters
        ----------
        path : str
            Path to TextGrid file
        types_only : bool
            Flag for whether to only save type information, ignoring the token information

        Returns
        -------
        :class:`~polyglotdb.io.discoursedata.DiscourseData`
            Parsed data from the file
        """

        tg = self.load_textgrid(path)
        multiple_speakers, is_valid = self._is_valid(tg)

        if not is_valid:
            raise (TextGridError('This file ({}) cannot be parsed by the {} parser.'.format(path, self.name)))
        name = os.path.splitext(os.path.split(path)[1])[0]

        # Format 1
        if not multiple_speakers:
            if self.speaker_parser is not None:
                speaker = self.speaker_parser.parse_path(path)
            else:
                speaker = None

            for a in self.annotation_tiers:
                a.reset()
                a.speaker = speaker

            # Parse the tiers
            for i, tier_name in enumerate(tg.tierNameList):
                ti = tg.tierDict[tier_name]
                if tier_name.lower().startswith(self.word_label):
                    self.annotation_tiers[0].add(( (text.strip(), begin, end) for (begin, end, text) in ti.entryList))
                elif tier_name.lower().startswith(self.phone_label):
                    self.annotation_tiers[1].add(( (text.strip(), begin, end) for (begin, end, text) in ti.entryList))
            pg_annotations = self._parse_annotations(types_only)

            data = DiscourseData(name, pg_annotations, self.hierarchy)
            for a in self.annotation_tiers:
                a.reset()

        # Format 2
        else:
            dummy = self.annotation_tiers
            self.annotation_tiers = []
            wav_path = find_wav_path(path)
            speaker_channel_mapping = {}
            if wav_path is not None:
                n_channels = get_n_channels(wav_path)
                if n_channels > 1:
                    # Figure speaker-channel mapping
                    n_tiers = 0
                    for i, tier_name in enumerate(tg.tierNameList):
                        try:
                            speaker, type = tier_name.split(' - ')
                        except ValueError:
                            continue
                        n_tiers += 1
                    ind = 0
                    cutoffs = [x / n_channels for x in range(1, n_channels)]
                    for i, tier_name in enumerate(tg.tierNameList):
                        try:
                            if self.speaker_first:
                                speaker, type = tier_name.split(' - ')
                            else:
                                type, speaker = tier_name.split(' - ')
                            speaker = speaker.strip().replace('/', '_').replace('\\', '_')
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
            for i, tier_name in enumerate(tg.tierNameList):
                ti = tg.tierDict[tier_name]
                try:
                    if self.speaker_first:
                        speaker, type = tier_name.split(' - ')
                    else:
                        type, speaker = tier_name.split(' - ')
                    speaker = speaker.strip().replace('/', '_').replace('\\', '_')
                except ValueError:
                    continue
                if type.lower().startswith(self.word_label):
                    type = 'word'
                elif type.lower().startswith(self.phone_label):
                    type = 'phone'
                if len(ti.entryList) == 1 and ti[0][2].strip() == '':
                    continue
                at = OrthographyTier(type, type)
                at.speaker = speaker
                at.add(( (text.strip(), begin, end) for (begin, end, text) in ti.entryList))
                self.annotation_tiers.append(at)
            pg_annotations = self._parse_annotations(types_only)
            data = DiscourseData(name, pg_annotations, self.hierarchy)
            data.speaker_channel_mapping = speaker_channel_mapping

            self.annotation_tiers = dummy

        data.wav_path = find_wav_path(path)
        return data
