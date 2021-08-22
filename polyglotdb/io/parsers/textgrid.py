import os
from praatio import tgio


from polyglotdb.exceptions import TextGridError
from polyglotdb.io.types.parsing import Orthography, Transcription

from .base import BaseParser, DiscourseData

from ..helper import find_wav_path


class TextgridParser(BaseParser):
    """
    Parser for Praat TextGrid files.

    Parameters
    ----------
    annotation_tiers: list
        Annotation types of the files to parse
    hierarchy : :class:`~polyglotdb.structure.Hierarchy`
        Details of how linguistic types relate to one another
    make_transcription : bool, defaults to True
        If true, create a word attribute for transcription based on segments
        that are contained by the word
    stop_check : callable, optional
        Function to check whether to halt parsing
    call_back : callable, optional
        Function to output progress messages
    """
    _extensions = ['.textgrid']

    def __init__(self, annotation_tiers, hierarchy, make_transcription=True,
                 make_label=False,
                 stop_check=None, call_back=None):
        super(TextgridParser, self).__init__(annotation_tiers, hierarchy,
                                             make_transcription=True, make_label=True,
                                             stop_check=stop_check, call_back=call_back)

    def load_textgrid(self, path):
        """
        Load a TextGrid file

        Parameters
        ----------
        path : str
            Path to the TextGrid file

        Returns
        -------
        :class:`~praatio.tgio.TextGrid`
            TextGrid object
        """
        try:
            tg = tgio.openTextgrid(path)
        except (AssertionError, ValueError) as e:
            raise (TextGridError('The file {} could not be parsed: {}'.format(path, str(e))))
        return tg

    def parse_discourse(self, path, types_only=False):
        """
        Parse a TextGrid file for later importing.

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

        if len(tg.tierNameList) != len(self.annotation_tiers):
            raise (TextGridError(
                "The TextGrid ({}) does not have the same number of interval tiers as the number of annotation types specified.".format(
                    path)))
        name = os.path.splitext(os.path.split(path)[1])[0]

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
            if isinstance(ti, tgio.IntervalTier):
                self.annotation_tiers[i].add(( (text.strip(), begin, end) for (begin, end, text) in ti.entryList))
            else:
                self.annotation_tiers[i].add(((text.strip(), time) for time, text in ti.entryList))

        is_empty_textgrid = True

        for t in self.annotation_tiers:
            for interval in t:
                if isinstance(interval, Orthography):
                    if interval.label != "":
                        is_empty_textgrid = False
                        break
                if isinstance(interval, Transcription):
                    if interval._list != []:
                        is_empty_textgrid = False
                        break
        if is_empty_textgrid:
            return None

        pg_annotations = self._parse_annotations(types_only)

        data = DiscourseData(name, pg_annotations, self.hierarchy)
        for a in self.annotation_tiers:
            a.reset()
        data.wav_path = find_wav_path(path)
        return data
