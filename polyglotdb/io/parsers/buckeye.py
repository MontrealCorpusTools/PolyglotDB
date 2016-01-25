
import os
import re
import sys

from polyglotdb.exceptions import BuckeyeParseError

from .base import BaseParser, PGAnnotation, PGAnnotationType, DiscourseData

from .speaker import FilenameSpeakerParser

FILLERS = set(['uh','um','okay','yes','yeah','oh','heh','yknow','um-huh',
                'uh-uh','uh-huh','uh-hum','mm-hmm'])

from ..helper import find_wav_path

class BuckeyeParser(BaseParser):
    '''
    Parser for the Buckeye corpus.

    Has annotation types for word labels, word transcription, word part of
    speech, and surface transcription labels.

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
    _extensions = ['.words']

    def __init__(self, annotation_types, hierarchy,
                    stop_check = None, call_back = None):
        super(BuckeyeParser, self).__init__(annotation_types, hierarchy,
                    make_transcription = False, make_label = False,
                    stop_check = stop_check, call_back = call_back)
        self.speaker_parser = FilenameSpeakerParser(3)

    def parse_discourse(self, word_path):
        '''
        Parse a Buckeye file for later importing.

        Parameters
        ----------
        word_path : str
            Path to Buckeye .words file

        Returns
        -------
        DiscourseData
            Parsed data from the file
        '''
        self.make_transcription = False
        name, ext = os.path.splitext(os.path.split(word_path)[1])
        if ext == '.words':
            phone_ext = '.phones'
        elif ext == '.WORDS':
            phone_ext = '.PHONES'
        phone_path = os.path.splitext(word_path)[0] + phone_ext

        if self.speaker_parser is not None:
            speaker = self.speaker_parser.parse_path(word_path)
        else:
            speaker = None

        for a in self.annotation_types:
            a.reset()
            a.speaker = speaker

        try:
            words = read_words(word_path)
        except Exception as e:
            print(e)
            return
        phones = read_phones(phone_path)

        if self.call_back is not None:
            cur = 0
            self.call_back("Parsing %s..." % name)
            self.call_back(0, len(words))

        for i, w in enumerate(words):
            if self.stop_check is not None and self.stop_check():
                return
            if self.call_back is not None:
                cur += 1
                if cur % 20 == 0:
                    self.call_back(cur)
            annotations = {}
            word = w['spelling']
            beg = w['begin']
            end = w['end']

            found = []
            if w['surface_transcription'] is None:
                ba = ('?', w['begin'], w['end'])
                found.append(ba)
            else:
                expected = w['surface_transcription']
                while len(found) < len(expected):
                    cur_phone = phones.pop(0)
                    if phone_match(cur_phone[0], expected[len(found)]) \
                        and cur_phone[2] >= beg and cur_phone[1] <= end:
                            found.append(cur_phone)

                    if not len(phones) and i < len(words)-1:
                        print(found)
                        print(BuckeyeParseError(word_path, [w]))
                        return
            self.annotation_types[0].add([(word, beg, end)])
            if w['transcription'] is None:
                w['transcription'] = '?'
            self.annotation_types[1].add([(w['transcription'], beg, end)])
            self.annotation_types[2].add([(w['category'], beg, end)])
            self.annotation_types[3].add(found)

        pg_annotations = self._parse_annotations()

        data = DiscourseData(name, pg_annotations, self.hierarchy)
        for a in self.annotation_types:
            a.reset()

        data.wav_path = find_wav_path(word_path)
        return data


def read_phones(path):
    output = []
    with open(path,'r') as file_handle:
        header_pattern = re.compile("#\r{0,1}\n")
        line_pattern = re.compile("\s+\d{3}\s+")
        label_pattern = re.compile(" {0,1};| {0,1}\+")
        f = header_pattern.split(file_handle.read())[1]
        flist = f.splitlines()
        begin = 0.0
        for l in flist:
            line = line_pattern.split(l.strip())
            try:
                end = float(line[0])
            except ValueError: # Missing phone label
                print('Warning: no label found in line: \'{}\''.format(l))
                continue
            label = sys.intern(label_pattern.split(line[1])[0])
            output.append((label, begin, end))
            begin = end
    return output

def read_words(path):
    output = []
    misparsed_lines = []
    with open(path,'r') as file_handle:
        f = re.split(r"#\r{0,1}\n",file_handle.read())[1]
        line_pattern = re.compile("; | \d{3} ")
        begin = 0.0
        flist = f.splitlines()
        for l in flist:
            line = line_pattern.split(l.strip())
            try:
                end = float(line[0])
                word = sys.intern(line[1])
                if word[0] != "<" and word[0] != "{":
                    citation = line[2].split(' ')
                    phonetic = line[3].split(' ')
                    if len(line) > 4:
                        category = line[4]
                        if word in FILLERS:
                            category = 'UH'
                    else:
                        category = None
                else:
                    citation = None
                    phonetic = None
                    category = None
            except IndexError:
                misparsed_lines.append(l)
                continue
            line = {'spelling':word,'begin':begin,'end':end,
                    'transcription':citation,'surface_transcription':phonetic,
                    'category':category}
            output.append(line)
            begin = end
    if misparsed_lines:
        raise(BuckeyeParseError(path, misparsed_lines))
    return output

def phone_match(one,two):
    if one != two and one not in two:
        return False
    return True
