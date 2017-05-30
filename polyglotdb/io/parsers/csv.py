import os
from csv import DictReader

from polyglotdb.exceptions import DelimiterError, CorpusIntegrityError
from polyglotdb.structure import Hierarchy

from .base import BaseParser, DiscourseData

from ..types.content import (OrthographyAnnotationType, TranscriptionAnnotationType,
                             NumericAnnotationType)


class CsvParser(BaseParser):
    '''
    Parser for CSV files.

    Parameters
    ----------
    annotation_types: list
        Annotation types of the files to parse
    column_delimiter : str
        Delimiter for columns
    stop_check : callable, optional
        Function to check whether to halt parsing
    call_back : callable, optional
        Function to output progress messages
    '''
    _extensions = ['.txt', '.csv']

    def __init__(self, annotation_types, column_delimiter,
                 stop_check=None, call_back=None):
        self.annotation_types = annotation_types
        self.column_delimiter = column_delimiter
        self.hierarchy = Hierarchy({'word': None})
        self.stop_check = stop_check
        self.call_back = call_back
        self.make_transcription = False
        self.make_label = True

    def parse_discourse(self, path):
        '''
        Parse a CSV file for later importing.

        Parameters
        ----------
        path : str
            Path to CSV file

        Returns
        -------
        :class:`~polyglotdb.io.discoursedata.DiscourseData`
            Parsed data from the file
        '''
        name = os.path.splitext(os.path.split(path)[1])[0]
        for a in self.annotation_types:
            if a.name == 'transcription' and not isinstance(a, TranscriptionAnnotationType):
                raise (CorpusIntegrityError(('The column \'{}\' is currently '
                                             'not being parsed as transcriptions '
                                             'despite its name.  Please ensure correct '
                                             'parsing for this column by changing its '
                                             '\'Annotation type\' in the parsing '
                                             'preview to the right.').format(a.name)))
        for a in self.annotation_types:
            a.reset()
        with open(path, encoding='utf-8') as f:
            headers = f.readline()
            headers = headers.split(self.column_delimiter)
            if len(headers) == 1:
                e = DelimiterError(('Could not parse the corpus.\n\Check '
                                    'that the delimiter you typed in matches '
                                    'the one used in the file.'))
                raise (e)

            for line in f.readlines():
                line = line.strip()
                if not line:  # blank or just a newline
                    continue
                d = {}
                for i, (k, v) in enumerate(zip(headers, line.split(self.column_delimiter))):
                    v = v.strip()
                    self.annotation_types[i].add([(v,)])

        pg_annotations = self._parse_annotations()

        data = DiscourseData(name, pg_annotations, self.hierarchy)
        for a in self.annotation_types:
            a.reset()

        return data
