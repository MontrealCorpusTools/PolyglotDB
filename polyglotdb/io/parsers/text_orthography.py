import os

from polyglotdb.structure import Hierarchy

from .base import BaseParser, DiscourseData

from ..helper import text_to_lines


class OrthographyTextParser(BaseParser):
    '''
    Parser for orthographic text files.

    Parameters
    ----------
    annotation_tiers: list
        Annotation types of the files to parse
    stop_check : callable, optional
        Function to check whether to halt parsing
    call_back : callable, optional
        Function to output progress messages
    '''

    def __init__(self, annotation_tiers,
                 stop_check=None, call_back=None):
        super(OrthographyTextParser, self).__init__(annotation_tiers,
                                                    Hierarchy({'word': None}), make_transcription=False,
                                                    stop_check=stop_check, call_back=call_back)

    def parse_discourse(self, path, types_only=False):
        '''
        Parse a text file for later importing.

        Parameters
        ----------
        path : str
            Path to text file

        Returns
        -------
        :class:`~polyglotdb.io.discoursedata.DiscourseData`
            Parsed data from the file
        '''

        name = os.path.splitext(os.path.split(path)[1])[0]

        if self.speaker_parser is not None:
            speaker = self.speaker_parser.parse_path(word_path)
            name = speaker + '_' + name
        else:
            speaker = None

        for a in self.annotation_tiers:
            a.reset()
            a.speaker = speaker

        lines = text_to_lines(path)
        if self.call_back is not None:
            self.call_back('Processing file...')
            self.call_back(0, len(lines))
            cur = 0
        num_annotations = 0
        for line in lines:
            if self.stop_check is not None and self.stop_check():
                return
            if self.call_back is not None:
                self.call_back(num_annotations)
            if not line or line == '\n':
                continue

            to_add = []
            for word in line:
                spell = word.strip()
                spell = ''.join(x for x in spell if not x in self.annotation_tiers[0].ignored_characters)
                if spell == '':
                    continue
                to_add.append(spell)
            self.annotation_tiers[0].add((x, num_annotations + i) for i, x in enumerate(to_add))
            num_annotations += len(to_add)

        pg_annotations = self._parse_annotations(types_only)

        data = DiscourseData(name, pg_annotations, self.hierarchy)
        for a in self.annotation_tiers:
            a.reset()
        return data
