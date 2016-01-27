
import os

from textgrid import TextGrid, IntervalTier

from polyglotdb.exceptions import TextGridError
from polyglotdb.structure import Hierarchy

from .base import BaseParser, PGAnnotation, PGAnnotationType, DiscourseData

from ..helper import find_wav_path

class TextgridParser(BaseParser):
    '''
    Parser for Praat TextGrid files.

    Parameters
    ----------
    annotation_types: list
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
    '''
    _extensions = ['.textgrid']
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

        if len(tg.tiers) != len(self.annotation_types):
            raise(TextGridError("The TextGrid ({}) does not have the same number of interval tiers as the number of annotation types specified.".format(path)))
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

            if isinstance(ti, IntervalTier):
                self.annotation_types[i].add(((x.mark.strip(), x.minTime, x.maxTime) for x in ti))
            else:
                self.annotation_types[i].add(((x.mark.strip(), x.time) for x in ti))
        pg_annotations = self._parse_annotations()

        data = DiscourseData(name, pg_annotations, self.hierarchy)
        for a in self.annotation_types:
            a.reset()

        data.wav_path = find_wav_path(path)
        return data

