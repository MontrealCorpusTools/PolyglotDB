import os

from polyglotdb.exceptions import (ILGLinesMismatchError,
                                   ILGWordMismatchError)
from polyglotdb.structure import Hierarchy

from ..helper import ilg_text_to_lines

from .base import BaseParser, DiscourseData


class IlgParser(BaseParser):
    """
    Parser for interlinear gloss (ILG) files.

    Parameters
    ----------
    annotation_tiers: list
        Annotation types of the files to parse
    stop_check : callable, optional
        Function to check whether to halt parsing
    call_back : callable, optional
        Function to output progress messages
    """

    def __init__(self, annotation_tiers,
                 stop_check=None, call_back=None):
        super(IlgParser, self).__init__(annotation_tiers,
                                        Hierarchy({'word': None}), make_transcription=False,
                                        make_label=True,
                                        stop_check=stop_check, call_back=call_back)

    def parse_discourse(self, path, types_only=False):
        """
        Parse an ILG file for later importing.

        Parameters
        ----------
        path : str
            Path to ILG file
        types_only : bool
            Flag for whether to only save type information, ignoring the token information

        Returns
        -------
        :class:`~polyglotdb.io.discoursedata.DiscourseData`
            Parsed data from the file
        """
        lines = ilg_text_to_lines(path)

        if len(lines) % len(self.annotation_tiers) != 0:
            raise (ILGLinesMismatchError(lines))

        if self.call_back is not None:
            self.call_back('Processing file...')
            self.call_back(0, len(lines))
        index = 0
        name = os.path.splitext(os.path.split(path)[1])[0]

        if self.speaker_parser is not None:
            speaker = self.speaker_parser.parse_path(path)
            name = speaker + '_' + name
        else:
            speaker = None

        for a in self.annotation_tiers:
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
            for line_ind, annotation_type in enumerate(self.annotation_tiers):
                if annotation_type.ignored:
                    continue
                actual_line_ind, line = lines[index + line_ind]
                if len(cur_line.values()) != 0 and len(line) not in [len(x) for x in cur_line.values()]:
                    mismatch = True

                cur_line[line_ind] = line
                self.annotation_tiers[line_ind].add(((x, num_annotations + j) for j, x in enumerate(line)))
            if mismatch:
                start_line = lines[index][0]
                end_line = start_line + len(self.annotation_tiers)
                mismatching_lines.append(((start_line, end_line), cur_line))

            index += len(self.annotation_tiers)
            num_annotations += len(line)

        if len(mismatching_lines) > 0:
            raise (ILGWordMismatchError(mismatching_lines))

        pg_annotations = self._parse_annotations(types_only)

        data = DiscourseData(name, pg_annotations, self.hierarchy)
        for a in self.annotation_tiers:
            a.reset()
        return data
