import os

from .base import BaseParser, DiscourseData

from ..helper import find_wav_path

class TimitParser(BaseParser):
    _extensions = ['.wrd']

    def parse_discourse(self, word_path):

        name, ext = os.path.splitext(os.path.split(word_path)[1])
        if ext == '.WRD':
            phone_path = os.path.splitext(word_path)[0] + '.PHN'
        else:
            phone_path = os.path.splitext(word_path)[0] + '.phn'
        speaker = os.path.basename(os.path.dirname(word_path))
        name = speaker + '_' + name
        for a in self.annotation_types:
            a.reset()
            a.speaker = speaker

        if self.call_back is not None:
            self.call_back('Reading files...')
            self.call_back(0,0)
        words = read_words(word_path)
        phones = read_phones(phone_path)
        if words[-1]['end'] != phones[-1][2]:
            words.append({'spelling': 'sil', 'begin': words[-1]['end'], 'end': phones[-1][2]})

        self.annotation_types[0].add((x['spelling'], x['begin'], x['end']) for x in words)
        self.annotation_types[1].add(phones)

        pg_annotations = self._parse_annotations()

        data = DiscourseData(name, pg_annotations, self.hierarchy)
        for a in self.annotation_types:
            a.reset()

        data.wav_path = find_wav_path(word_path)
        return data

def read_phones(path):
    output = []
    sr = 16000
    with open(path,'r') as file_handle:
        for line in file_handle:
            l = line.strip().split(' ')
            begin = float(l[0]) / sr
            end = float(l[1])/ sr
            label = l[2]
            output.append((label, begin, end))
    return output

def read_words(path):
    output = []
    sr = 16000
    prev = None
    with open(path,'r') as file_handle:
        for line in file_handle:
            l = line.strip().split(' ')
            begin = float(l[0]) / sr
            end = float(l[1]) / sr
            word = l[2]
            if prev is not None and begin != prev:
                output.append({'spelling': 'sil', 'begin':prev, 'end':begin})
            elif prev is None and begin != 0:
                output.append({'spelling': 'sil', 'begin':0, 'end':begin})
            output.append({'spelling':word, 'begin':begin, 'end':end})
            prev = end
    return output
