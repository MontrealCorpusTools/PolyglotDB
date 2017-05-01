import string
import re

NUMBER_CHARACTERS = set(string.digits)

parse_numbers = re.compile('\d+|\S')

from .base import BaseAnnotationType, BaseAnnotation


class GroupingAnnotation(BaseAnnotation):
    @property
    def value(self):
        """Returns empty string"""
        return ''


class GroupingAnnotationType(BaseAnnotationType):
    annotation_class = GroupingAnnotation


class OrthographyAnnotation(BaseAnnotation):
    def __init__(self, label):
        self.label = label

    @property
    def value(self):
        """Returns BaseAnnotation label"""
        return self.label


class OrthographyAnnotationType(BaseAnnotationType):
    annotation_class = OrthographyAnnotation

    def __init__(self, name, linguistic_type, label=False):
        self.characters = set()
        self.ignored_characters = set()

        BaseAnnotationType.__init__(self, name, linguistic_type)
        self.label = label

    @property
    def punctuation(self):
        """Returns union of characters and punctuation"""
        return self.characters & set(string.punctuation)


class MorphemeAnnotation(OrthographyAnnotation):
    def __init__(self, morphemes):
        self._list = morphemes

    @property
    def value(self):
        """Returns OrthographyAnnotation morphemes"""
        return self._list


class MorphemeAnnotationType(OrthographyAnnotationType):
    annotation_class = MorphemeAnnotation

    def __init__(self, name, linguistic_type):
        self.morph_delimiters = set()
        OrthographyAnnotationType.__init__(self, name, linguistic_type)

    def _parse_morphemes(self, string):
        md = self.morph_delimiters
        if len(md) and any(x in string for x in md):
            morphemes = re.split("|".join(md), string)
        else:
            morphemes = [string]
        return morphemes

    def add(self, annotations, save=True):
        """
        save annotations  to _list

        Parameters
        ----------
        annotations : list
            the annotations to save

        save : boolean
            defaults to True
        """
        for a in annotations:
            a = list(a)
            label = a.pop(0)
            self.characters.update(label)
            if save or len(self._list) < 10:
                # If save is False, only the first 10 annotations are saved
                morphemes = self._parse_morphemes(label)
                a.insert(0, morphemes)
                annotation = self.annotation_class(*a)
                self._list.append(annotation)


class TranscriptionAnnotation(MorphemeAnnotation):
    def __init__(self, segments, morpheme_breaks=None, stress=None, tone=None):
        self._list = segments
        if morpheme_breaks is None:
            self.morpheme_breaks = []
        else:
            self.morpheme_breaks = morpheme_breaks
        self.stress = None
        self.tone = None
        if stress is not None:
            self.stress = stress
        elif tone is not None:
            self.tone = tone


class TranscriptionAnnotationType(MorphemeAnnotationType):
    annotation_class = TranscriptionAnnotation

    def __init__(self, name, linguistic_type):
        self.digraphs = set()
        self.trans_delimiter = None
        self.number_behavior = None

        MorphemeAnnotationType.__init__(self, name, linguistic_type)

    def pretty_print(self):
        """
        Formats information about corpus from parsing for printing to log

        Returns
        -------
        string : str
            the information
        """
        string = ('{}:\n'.format(self.name) +
                  '    Ignored characters: {}\n'.format(', '.join(self.ignored_characters)) +
                  '    Digraphs: {}\n'.format(', '.join(self.digraphs)) +
                  '    Transcription delimiter: {}\n'.format(self.trans_delimiter) +
                  '    Morpheme delimiters: {}\n'.format(', '.join(self.morph_delimiters)) +
                  '    Number behavior: {}\n'.format(self.number_behavior))
        return string

    @property
    def digraph_pattern(self):
        """
        Builds a regular expression with the list of digraphs

        Returns
        -------
        re object
            the regular expression of digraphs
        """
        if len(self.digraphs) == 0:
            return None
        digraph_list = sorted(self.digraphs, key=lambda x: len(x), reverse=True)
        pattern = '|'.join(re.escape(d) for d in digraph_list)
        pattern += '|\d+|\S'
        return re.compile(pattern)

    def add(self, annotations, save=True):
        """
        save annotations  to _list

        Parameters
        ----------
        annotations : list
            the annotations to save
        save : boolean
            defaults to True
        """
        for a in annotations:
            a = list(a)
            label = a.pop(0)
            self.characters.update(label)
            if save or len(self._list) < 10:
                # If save is False, only the first 10 annotations are saved
                trans, morph = self._parse_transcription(label)
                trans, prosody = self._parse_numbers(trans)
                kwargs = {'morpheme_breaks': morph}
                if self.number_behavior == 'stress':
                    kwargs['stress'] = prosody
                elif self.number_behavior == 'tone':
                    kwargs['tone'] = prosody
                a.insert(0, trans)
                annotation = self.annotation_class(*a, **kwargs)
                self._list.append(annotation)

    def _parse_transcription(self, string):
        """
        Parse a string into a transcription (list of segments) given an
        :class:`AnnotationType`

        Parameters
        ----------
        string : str
            String to be parsed

        Returns
        -------
        list of str
            Parsed string of segments in a list
        """
        md = self.morph_delimiters
        morph_boundaries = []
        if len(md) and any(x in string for x in md):
            morphs = re.split("|".join(md), string)
            transcription = []
            for i, m in enumerate(morphs):
                trans, _ = self._parse_transcription(m)
                transcription += trans
                bound = len(transcription)
                if self.number_behavior is not None:
                    for t in transcription:
                        if t in NUMBER_CHARACTERS:
                            bound -= 1
                morph_boundaries.append(bound)
        else:
            ignored = self.ignored_characters
            if ignored is not None:
                string = ''.join(x for x in string if x not in ignored)
            if self.trans_delimiter is not None:
                string = string.split(self.trans_delimiter)
            elif self.digraph_pattern is not None:
                string = self.digraph_pattern.findall(string)
            else:
                string = parse_numbers.findall(string)
            transcription = [seg for seg in string if seg != '']
        return transcription, morph_boundaries

    def _parse_numbers(self, transcription):
        if self.number_behavior is None:
            return transcription, None
        prosody = {}
        parsed_transcription = []
        for i, seg in enumerate(transcription):
            num = ''.join(x for x in seg if x in NUMBER_CHARACTERS)
            seg = ''.join(x for x in seg if x not in NUMBER_CHARACTERS)
            if num == '':
                num = None

            if seg != '':
                parsed_transcription.append(seg)
            if num is not None:
                prosody[len(parsed_transcription) - 1] = num
        return parsed_transcription, prosody


class NumericAnnotation(BaseAnnotation):
    def __init__(self, value):
        self.value = value


class NumericAnnotationType(BaseAnnotationType):
    annotation_class = NumericAnnotation

    def add(self, annotations, save=True):
        """
        save annotations  to _list

        Parameters
        ----------
        annotations : list
            the annotations to save

        save : boolean
            defaults to True
        """
        for a in annotations:
            a = list(a)
            label = a.pop(0)
            if save or len(self._list) < 10:
                a.insert(0, float(label))
                annotation = self.annotation_class(*a)
                self._list.append(annotation)
