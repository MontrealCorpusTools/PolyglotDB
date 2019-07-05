import os

from .base import BaseParser, DiscourseData

from ..helper import find_wav_path

from .speaker import DirectorySpeakerParser


class TimitParser(BaseParser):
    """
    Parser for the TIMIT corpus.

    Has annotation types for word labels and surface transcription labels.

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
    _extensions = ['.wrd', '.WRD']

    def __init__(self, annotation_tiers, hierarchy,
                 stop_check=None, call_back=None):
        super(TimitParser, self).__init__(annotation_tiers, hierarchy,
                                          make_transcription=True, make_label=False,
                                          stop_check=stop_check, call_back=call_back)
        self.speaker_parser = DirectorySpeakerParser()

    def parse_discourse(self, word_path, types_only=False):
        """
        Parse a TIMIT file for later importing.

        Parameters
        ----------
        word_path : str
            Path to TIMIT .wrd file
        types_only : bool
            Flag for whether to only save type information, ignoring the token information

        Returns
        -------
        :class:`~polyglotdb.io.discoursedata.DiscourseData`
            Parsed data from the file
        """

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

        for a in self.annotation_tiers:
            a.reset()
            a.speaker = speaker

        if self.call_back is not None:
            self.call_back('Reading files...')
            self.call_back(0, 0)
        words = read_words(word_path)
        phones = read_phones(phone_path)
        if words[-1]['end'] != phones[-1][2]:
            words.append({'spelling': 'sil', 'begin': words[-1]['end'], 'end': phones[-1][2]})

        self.annotation_tiers[0].add((x['spelling'], x['begin'], x['end']) for x in words)
        self.annotation_tiers[1].add(phones)

        pg_annotations = self._parse_annotations(types_only)

        data = DiscourseData(name, pg_annotations, self.hierarchy)
        for a in self.annotation_tiers:
            a.reset()

        data.wav_path = find_wav_path(word_path)

        return data


def read_phones(path):
    """
    From a TIMIT file, reads the phone lines, appends label, begin, and end to output
    
    Parameters
    ----------
    path : str
        path to file
    
    Returns
    -------
    list of tuples
        each tuple is label, begin, end for a phone

    """
    output = []
    sr = 16000
    with open(path, 'r') as file_handle:
        for line in file_handle:
            l = line.strip().split(' ')
            begin = float(l[0]) / sr
            end = float(l[1]) / sr
            label = l[2]
            output.append((label, begin, end))
    return output


def read_words(path):
    """
    From a TIMIT file, reads the word info
    
    Parameters
    ----------
    path : str
        path to file
    
    Returns
    -------
    list of dicts
        each dict has spelling, begin, end

    """
    output = []
    sr = 16000
    prev = None
    with open(path, 'r') as file_handle:
        for line in file_handle:
            l = line.strip().split(' ')
            begin = float(l[0]) / sr
            end = float(l[1]) / sr
            word = l[2]
            if prev is not None and begin != prev:
                output.append({'spelling': '<SIL>', 'begin': prev, 'end': begin})
            elif prev is None and begin != 0:
                output.append({'spelling': '<SIL>', 'begin': 0, 'end': begin})
            output.append({'spelling': word, 'begin': begin, 'end': end})
            prev = end
    return output
