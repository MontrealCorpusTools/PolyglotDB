
import os
import re
from collections import Counter

from polyglotdb.exceptions import (DelimiterError, ILGError, ILGLinesMismatchError,
                                ILGWordMismatchError)
from polyglotdb.structure import Hierarchy

from ..helper import guess_type, ilg_text_to_lines

from ..discoursedata import DiscourseData

from .base import BaseParser, PGAnnotation, PGAnnotationType, DiscourseData

class IlgParser(BaseParser):
    '''
    Parser for interlinear gloss (ILG) files.

    Parameters
    ----------
    annotation_types: list
        Annotation types of the files to parse
    stop_check : callable, optional
        Function to check whether to halt parsing
    call_back : callable, optional
        Function to output progress messages
    '''
    def __init__(self, annotation_types,
                    stop_check = None, call_back = None):
        super(IlgParser, self).__init__(annotation_types,
                    Hierarchy({'word': None}), make_transcription = False,
                    make_label = True,
                    stop_check = stop_check, call_back = call_back)

    def parse_discourse(self, path):
        '''
        Parse an ILG file for later importing.

        Parameters
        ----------
        path : str
            Path to ILG file

        Returns
        -------
        :class:`~polyglotdb.io.discoursedata.DiscourseData`
            Parsed data from the file
        '''
        lines = ilg_text_to_lines(path)

        if len(lines) % len(self.annotation_types) != 0:
            raise(ILGLinesMismatchError(lines))

        if self.call_back is not None:
            self.call_back('Processing file...')
            self.call_back(0,len(lines))
        index = 0
        name = os.path.splitext(os.path.split(path)[1])[0]

        if self.speaker_parser is not None:
            speaker = self.speaker_parser.parse_path(word_path)
            name = speaker + '_' + name
        else:
            speaker = None

        for a in self.annotation_types:
            a.reset()
            a.speaker = speaker

        mismatching_lines = []
        num_annotations = 0
        while index < len(lines):
            if self.stop_check is not None and self.stop_check():
                return
            if self.call_back is not None:
                self.call_back('Processing file...')
                self.call_back(index)
            cur_line = {}
            mismatch = False
            for line_ind, annotation_type in enumerate(self.annotation_types):
                if annotation_type.ignored:
                    continue
                actual_line_ind, line = lines[index+line_ind]
                if len(cur_line.values()) != 0 and len(line) not in [len(x) for x in cur_line.values()]:
                    mismatch = True

                cur_line[line_ind] = line
                self.annotation_types[line_ind].add(((x, num_annotations + j)  for j, x in enumerate(line)))
            if mismatch:
                start_line = lines[index][0]
                end_line = start_line + len(self.annotation_types)
                mismatching_lines.append(((start_line, end_line), cur_line))

            index += len(self.annotation_types)
            num_annotations += len(line)

        if len(mismatching_lines) > 0:
            raise(ILGWordMismatchError(mismatching_lines))

        pg_annotations = self._parse_annotations()

        data = DiscourseData(name, pg_annotations, self.hierarchy)
        for a in self.annotation_types:
            a.reset()
        return data

