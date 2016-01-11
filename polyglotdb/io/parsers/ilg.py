
import os
import re
from collections import Counter

from polyglotdb.exceptions import (DelimiterError, ILGError, ILGLinesMismatchError,
                                ILGWordMismatchError)

from ..helper import guess_type, ilg_text_to_lines

from ..discoursedata import DiscourseData

from .base import BaseParser, PGAnnotation, PGAnnotationType, DiscourseData

class IlgParser(BaseParser):
    def __init__(self, annotation_types,
                    stop_check = None, call_back = None):
        self.annotation_types = annotation_types
        self.hierarchy = {'word': None}
        self.make_transcription = False
        self.stop_check = stop_check
        self.call_back = call_back

    def parse_discourse(self, path):
        lines = ilg_text_to_lines(path)

        if len(lines) % len(self.annotation_types) != 0:
            raise(ILGLinesMismatchError(lines))

        if self.call_back is not None:
            self.call_back('Processing file...')
            self.call_back(0,len(lines))
        index = 0
        name = os.path.splitext(os.path.split(path)[1])[0]

        for a in self.annotation_types:
            a.reset()

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

