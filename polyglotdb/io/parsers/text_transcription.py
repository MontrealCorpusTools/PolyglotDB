import os
from ..helper import text_to_lines

from .base import BaseParser, DiscourseData

class TranscriptionTextParser(BaseParser):
    def __init__(self, annotation_types,
                    stop_check = None, call_back = None):
        self.annotation_types = annotation_types
        self.hierarchy = {'word': None}
        self.make_transcription = False
        self.make_label = True
        self.stop_check = stop_check
        self.call_back = call_back

    def parse_discourse(self, path):

        name = os.path.splitext(os.path.split(path)[1])[0]


        for a in self.annotation_types:
            a.reset()

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
                cur += 1
                if cur % 20 == 0:
                    self.call_back(cur)
            if not line:
                continue
            a.add(((x, num_annotations + i) for i, x in enumerate(line)))
            num_annotations += len(line)

        pg_annotations = self._parse_annotations()

        data = DiscourseData(name, pg_annotations, self.hierarchy)
        for a in self.annotation_types:
            a.reset()
        return data
