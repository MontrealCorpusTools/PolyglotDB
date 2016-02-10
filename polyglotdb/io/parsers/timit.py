import os

from .base import BaseParser, DiscourseData

from ..helper import find_wav_path

from .speaker import DirectorySpeakerParser

class TimitParser(BaseParser):
    '''
    Parser for the TIMIT corpus.

    Has annotation types for word labels and surface transcription labels.

    Parameters
    ----------
    annotation_types: list
        Annotation types of the files to parse
    hierarchy : :class:`~polyglotdb.structure.Hierarchy`
        Details of how linguistic types relate to one another
    stop_check : callable, optional
        Function to check whether to halt parsing
    call_back : callable, optional
        Function to output progress messages
    '''
    _extensions = ['.wrd']

    def __init__(self, annotation_types, hierarchy,
                    stop_check = None, call_back = None):
        super(TimitParser, self).__init__(annotation_types, hierarchy,
                    make_transcription = True, make_label = False,
                    stop_check = stop_check, call_back = call_back)
        self.speaker_parser = DirectorySpeakerParser()

    def parse_discourse(self, word_path):
        '''
        Parse a TIMIT file for later importing.

        Parameters
        ----------
        word_path : str
            Path to TIMIT .wrd file

        Returns
        -------
        :class:`~polyglotdb.io.discoursedata.DiscourseData`
            Parsed data from the file
        '''

        name, ext = os.path.splitext(os.path.split(word_path)[1])
        if ext == '.WRD':
            phone_path = os.path.splitext(word_path)[0] + '.PHN'
        else:
            phone_path = os.path.splitext(word_path)[0] + '.phn'

        if self.speaker_parser is not None:
            speaker = self.speaker_parser.parse_path(word_path)
            name = speaker + '_' + name
        else:
            speaker = None

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
