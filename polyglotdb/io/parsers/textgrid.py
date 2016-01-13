
import os

from textgrid import TextGrid, IntervalTier

from polyglotdb.exceptions import TextGridError
from polyglotdb.structure import Hierarchy

from .base import BaseParser, PGAnnotation, PGAnnotationType, DiscourseData

from ..helper import find_wav_path

class TextgridParser(BaseParser):
    _extensions = ['.textgrid']
    def parse_discourse(self, path):
        tg = TextGrid()
        tg.read(path)

        if len(tg.tiers) != len(self.annotation_types):
            raise(TextGridError("The TextGrid ({}) does not have the same number of interval tiers as the number of annotation types specified.".format(path)))
        name = os.path.splitext(os.path.split(path)[1])[0]
        for a in self.annotation_types:
            a.reset()

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

