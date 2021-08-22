import re
import os
from polyglotdb.io.parsers.base import BaseParser

from .speaker import DirectorySpeakerParser

from .base import DiscourseData


class PartiturParser(BaseParser):
    """
    Parser for Partitur formatted text files.

    Parameters
    ----------
    annotation_tiers : list
        List of the annotation tiers to store data from the TextGrid
    hierarchy : Hierarchy
        Basic hierarchy of the TextGrid
    stop_check : callable
        Function to check for whether parsing should stop
    call_back : callable
        Function to report progress in parsing
    """
    _extensions = ['.par,2']

    def __init__(self, annotation_tiers, hierarchy,
                 stop_check=None, call_back=None):
        super(PartiturParser, self).__init__(annotation_tiers, hierarchy,
                                             make_transcription=False, make_label=False,
                                             stop_check=stop_check, call_back=call_back)
        self.speaker_parser = DirectorySpeakerParser()

    def parse_discourse(self, path, types_only=False):
        '''
        Parse a BAS Partitur file for later importing.

        Parameters
        ----------
        path : str
            Path to Partitur file
        types_only : bool
            Flag for whether to only save type information, ignoring the token information

        Returns
        -------
        :class:`~polyglotdb.io.discoursedata.DiscourseData`
            Parsed data from the file
        '''
        speaker = parse_speaker(path)
        for a in self.annotation_tiers:
            a.reset()
            a.speaker = speaker

        name = os.path.splitext(os.path.split(path)[1])[0]

        phones = read_phones(path)
        scrambled = match_words(read_words(path), phones)
        words = sorted(scrambled.values(), key=lambda x: x[1])

        for i, tup in enumerate(words):
            # tup = (key, words[key][0], words[key][1])

            word = tup[0]
            self.annotation_tiers[0].add([tup[0:3]])
            self.annotation_tiers[1].add([(str(tup[3]), tup[1], tup[2])])


            # self.annotation_tiers[0][-1].type_properties['transcription'] = tup[3]

        for tup in phones.values():
            self.annotation_tiers[2].add(((x for x in tup)))
        pg_annotations = self._parse_annotations(types_only)
        data = DiscourseData(name, pg_annotations, self.hierarchy)

        for a in self.annotation_tiers:
            a.reset()
        return data


def parse_speaker(path):
    """
    Get speaker id from a BAS partitur file

    Parameters
    ----------
    path : str
        a path to the file

    Returns
    -------
    str or None
        the speaker id
    """
    speaker = ''
    with open(path, 'r', encoding='utf8') as f:
        lines = f.readlines()
    for line in lines:
        splitline = re.split("\s", line)
        if splitline[0] == 'SPN:':
            return splitline[1].strip()

    return None


def read_words(path):
    """
    Get all word info from a BAS partitur file

    Parameters
    ----------
    path : str
        a path to the file

    Returns
    -------
    dict
        dictionary of words and their indexes
    """
    words = {}
    with open(path, 'r', encoding='utf8') as f:
        lines = f.readlines()
    for line in lines:
        splitline = re.split("\s", line)
        if splitline[0] == 'ORT:':
            try:
                words[splitline[1]][0] = splitline[2]
            except KeyError:
                words[splitline[1]] = [None, None]
                words[splitline[1]][0] = splitline[2]
                # words.update({splitline[1].strip():splitline[2].strip()})
        if splitline[0] == 'KAN:':
            try:
                words[splitline[1]][-1] = splitline[2]
            except KeyError:
                words[splitline[1]] = [None, None]
                words[splitline[1]][-1] = splitline[2]
    return words


def read_phones(path):
    """
    Get all phone info from a BAS partitur file

    Parameters
    ----------
    path : str
        a path to the file

    Returns
    -------
    dict
        dictionary of phones, their word indexes, and their begin and end
    """
    phones = {}
    with open(path, 'r', encoding='utf8') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        splitline = re.split("\s", line)
        if splitline[0] == 'MAU:':
            begin = float(splitline[1].strip()) / 10000
            end = begin + float(splitline[2].strip()) / 10000
            index = splitline[3]
            try:
                phones[index].append((splitline[4].strip(), begin, end))
            except KeyError:
                phones[index] = [(splitline[4].strip(), begin, end)]

    return phones


def match_words(words, phones):
    """
    Matches a dict of phones to a dict of words using their indexes
    produces a dict of words with begin time (begin of first phone)
    and end time (end of last phone)

    Parameters
    ----------
    words : dict
        a dict of words and their indexes
    phones : dict
        a dict of phones, their indexes, and their begins and ends
    """
    newwords = {}
    for i, key in enumerate(words):
        v = words[key]
        word = words[key][0]
        transcription = words[key][1]
        # "Kuchen": '3'
        in_word = phones[key]
        begmin = in_word[0][2]
        endmax = in_word[0][1]
        for tup in in_word:
            if tup[1] < begmin:
                begmin = tup[1]
            if tup[2] > endmax:
                endmax = tup[2]

        # words[key] = (key, begmin, endmax)
        newwords[word] = (word, begmin, endmax, transcription)

    return newwords
