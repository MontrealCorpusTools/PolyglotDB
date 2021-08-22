import os
import re

from polyglotdb.exceptions import BuckeyeParseError
from .base import BaseParser, DiscourseData
from .speaker import FilenameSpeakerParser
from ..helper import find_wav_path

FILLERS = {'uh', 'um', 'okay', 'yes', 'yeah', 'oh', 'heh', 'yknow', 'um-huh',
               'uh-uh', 'uh-huh', 'uh-hum', 'mm-hmm'}


def contained_by(word, phone):
    """
    Check whether a word contains a phone based on time points

    Parameters
    ----------
    word : dict
        Word information
    phone : dict
        Phone information

    Returns
    -------
    bool
        True if phone midpoint is within the bounds of the word
    """
    phone_midpoint = phone[1] + (phone[2] - phone[1]) / 2
    word_midpoint = word['begin'] + (word['end'] - word['begin']) / 2
    if (phone_midpoint > word['begin'] and phone_midpoint < word['end']) or (
            word_midpoint > phone[1] and word_midpoint < phone[2]):
        return True
    return False


class BuckeyeParser(BaseParser):
    """
    Parser for the Buckeye corpus.

    Has annotation types for word labels, word transcription, word part of
    speech, and surface transcription labels.

    Parameters
    ----------
    annotation_tiers: list
        Annotation types of the files to parse
    hierarchy : :class:`~polyglotdb.structure.Hierarchy`
        Details of how linguistic types relate to one another
    stop_check : callable, optional
        Function to check whether to halt parsing
    call_back : callable, optional
        Function to output progress messages
    """
    _extensions = ['.words']

    def __init__(self, annotation_tiers, hierarchy,
                 stop_check=None, call_back=None):
        super(BuckeyeParser, self).__init__(annotation_tiers, hierarchy,
                                            make_transcription=False, make_label=False,
                                            stop_check=stop_check, call_back=call_back)
        self.speaker_parser = FilenameSpeakerParser(3)

    def parse_discourse(self, word_path, types_only=False):
        """
        Parse a Buckeye file for later importing.

        Parameters
        ----------
        word_path : str
            Path to Buckeye .words file
        types_only : bool
            Flag for whether to only save type information, ignoring the token information

        Returns
        -------
        :class:`~polyglotdb.io.discoursedata.DiscourseData`
            Parsed data
        """
        self.make_transcription = False
        phone_ext = ''
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

        for a in self.annotation_tiers:
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
            if word[0] == '{':
                continue
            beg = w['begin']
            end = w['end']

            found = []

            while len(phones):
                if contained_by(w, phones[0]):
                    cur_phone = phones.pop(0)
                    found.append(cur_phone)
                elif phones[0][0][0] == '{' or phones[0][1] < beg:
                    phones.pop(0)
                else:
                    break
            if not found:
                ba = ('?', w['begin'], w['end'])
                found.append(ba)
            else:
                beg = found[0][1]
                if end != found[-1][2]:
                    end = found[-1][2]
                    if i != len(words) - 1:
                        words[i + 1]['begin'] = end
            self.annotation_tiers[0].add([(word, beg, end)])
            if w['transcription'] is None:
                w['transcription'] = '?'
            if w['surface_transcription'] is None:
                w['surface_transcription'] = '?'
            self.annotation_tiers[1].add([(w['transcription'], beg, end)])
            self.annotation_tiers[2].add([(w['surface_transcription'], beg, end)])
            self.annotation_tiers[3].add([(w['category'], beg, end)])
            self.annotation_tiers[4].add(found)

        pg_annotations = self._parse_annotations(types_only)

        data = DiscourseData(name, pg_annotations, self.hierarchy)
        for a in self.annotation_tiers:
            a.reset()

        data.wav_path = find_wav_path(word_path)
        return data


def read_phones(path):
    """
    From a buckeye file, reads the phone lines, appends label, begin, and end to output
    
    Parameters
    ----------
    path : str
        path to file
    
    Returns
    -------
    output : list of tuples
        each tuple is label, begin, end for a phone
    """
    output = []
    with open(path, 'r') as file_handle:
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
            except ValueError:  # Missing phone label
                print('Warning: no label found in line: \'{}\''.format(l))
                continue
            label = label_pattern.split(line[1])[0]
            output.append((label, begin, end))
            begin = end
    return output


def read_words(path):
    """
    From a buckeye file, reads the word info
    
    Parameters
    ----------
    path : str
        path to file
    
    Returns
    -------
    output : list of dicts
        each dict has spelling, begin, end, transcription, surface_transcription, category

    """
    output = []
    misparsed_lines = []
    with open(path, 'r') as file_handle:
        f = re.split(r"#\r{0,1}\n", file_handle.read())[1]
        line_pattern = re.compile("; | \d{3} ")
        begin = 0.0
        flist = f.splitlines()
        for l in flist:
            line = line_pattern.split(l.strip())
            try:
                end = float(line[0])
                word = line[1].replace(' ', '_')
                if word[0] != "<" and word[0] != "{":
                    citation = line[2]
                    phonetic = line[3]
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
            line = {'spelling': word, 'begin': begin, 'end': end,
                    'transcription': citation, 'surface_transcription': phonetic,
                    'category': category}
            output.append(line)
            begin = end
    if misparsed_lines:
        raise (BuckeyeParseError(path, misparsed_lines))
    return output
