import re
import os
import string
import logging
import operator

from polyglotdb.exceptions import DelimiterError

NUMBER_CHARACTERS = set(string.digits)

class Attribute(object):
    """
    Attributes are for collecting summary information about attributes of
    Words or WordTokens, with different types of attributes allowing for
    different behaviour

    Parameters
    ----------
    name : str
        Python-safe name for using `getattr` and `setattr` on Words and
        WordTokens

    att_type : str
        Either 'spelling', 'tier', 'numeric' or 'factor'

    display_name : str
        Human-readable name of the Attribute, defaults to None

    default_value : object
        Default value for initializing the attribute

    Attributes
    ----------
    name : string
        Python-readable name for the Attribute on Word and WordToken objects

    display_name : string
        Human-readable name for the Attribute
    """
    ATT_TYPES = ['spelling', 'tier', 'numeric', 'factor']
    def __init__(self, name, att_type, display_name = None, default_value = None):
        self.name = name
        self.att_type = att_type
        self._display_name = display_name

    @property
    def delimiter(self):
        if self.att_type != 'tier':
            return None
        else:
            return self._delim

    @delimiter.setter
    def delimiter(self, value):
        self._delim = value

    @staticmethod
    def guess_type(values, trans_delimiters = None):
        if trans_delimiters is None:
            trans_delimiters = ['.',' ', ';', ',']
        probable_values = {x: 0 for x in Attribute.ATT_TYPES}
        for i,v in enumerate(values):
            try:
                t = float(v)
                probable_values['numeric'] += 1
                continue
            except ValueError:
                for d in trans_delimiters:
                    if d in v:
                        probable_values['tier'] += 1
                        break
                else:
                    if v in [v2 for j,v2 in enumerate(values) if i != j]:
                        probable_values['factor'] += 1
                    else:
                        probable_values['spelling'] += 1
        return max(probable_values.items(), key=operator.itemgetter(1))[0]

    @staticmethod
    def sanitize_name(name):
        """
        Sanitize a display name into a Python-readable attribute name

        Parameters
        ----------
        name : string
            Display name to sanitize

        Returns
        -------
        string
            Sanitized name
        """
        return re.sub('\W','',name.lower())

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.display_name

    def __eq__(self,other):
        if isinstance(other,Attribute):
            if self.name == other.name:
                return True
        if isinstance(other,str):
            if self.name == other:
                return True
        return False

    @property
    def display_name(self):
        if self._display_name is not None:
            return self._display_name
        return self.name.title()

class BaseAnnotation(object):
    """
    Class for storing information about annotations tied directly to the
    signal (i.e., phones, surface representations)

    Parameters
    ----------
    label : str
        Label of the annotation
    begin : float or None
        Beginning timepoint
    end : float or None
        End timepoint

    Attributes
    ----------
    label : str
        Label of the annotation
    begin : float or None
        Beginning timepoint
    end : float or None
        End timepoint
    stress : str or None
        Stress level of the annotation
    tone : str or None
        Tone of the annotation
    """
    def __init__(self, label, begin = None, end = None):
        self.label = label
        self.begin = begin
        self.end = end
        self.stress = None
        self.tone = None
        self.group = None

    def __iter__(self):
        return iter(self.label)

    def __repr__(self):
        return '<BaseAnnotation "{}" from {} to {}>'.format(self.label,
                                                            self.begin,
                                                            self.end)
    def __eq__(self, other):
        if isinstance(other, BaseAnnotation):
            return self.label == other.label and self.begin == other.begin \
                    and self.end == other.end
        elif isinstance(other, str):
            return self.label == other
        return False

class Annotation(BaseAnnotation):
    """
    Class for information about annotations that are indirectly tied
    to a signal (e.g., words, morphemes, syllables, etc.)

    In addition to the label of the annotation, other properties of the
    annotation can be specified through keyword arguments in construction.
    If a keyword argument value is a tuple of integers, then it is interpreted
    as referring to indices of :class:`BaseAnnotation` objects.  All other types will be
    coerced to strings. Lists of segments, such as for underlying/canonical
    transcriptions will use the segment delimiter '.' when creating the
    string.

    Parameters
    ----------
    label : str
        Label of the annotation

    Attributes
    ----------
    label : str
        Label of the annotation
    references : list
        List of BaseAnnotation types that `begins` and `ends` reference
    begins : list
        List of beginning indices
    ends : list
        List of ending indices
    token_properties : dict
        Dictionary of properties that are of the token, not the word type
    type_properties : dict
        Dictionary of properties that are of the word type, not the token
    """
    def __init__(self, label, **kwargs):
        self.label = label
        self.begins = []
        self.ends = []
        self.references = []
        self.token_properties = {}
        self.type_properties = {}
        for k,v in kwargs.items():
            if isinstance(v, tuple):
                self.references.append(k)
                self.begins.append(v[0])
                self.ends.append(v[1])
            elif k == 'type_properties':
                self.type_properties.update(v)
            elif k == 'token_properties':
                self.token_properties.update(v)
            else:
                setattr(self, k, v)

    def __eq__(self, other):
        return self.label == other.label and self.begins == other.begins \
                and self.ends == other.ends

    def __getitem__(self, key):
        for i, r in enumerate(self.references):
            if r == key:
                return self.begins[i], self.ends[i]
        return None

    def __repr__(self):
        return '<Annotation "{}">'.format(self.label)

class AnnotationType(object):
    """
    Class containing information about annotation types.

    Parameters
    ----------
    name : str
        Name of the annotation type
    subtype : str or None
        Name of the annotation type that falls below this annotation type
    supertype : str or None
        Name of the annotation type that is above this annotation type
    attribute : :class:`Attribute`, optional
        Details of parsing the annotations, such as the type (string, float, tier)
    anchor : bool, optional
        Flag for if this annotation type is the anchor, defaults to False
    token : bool, optional
        Flag for if this annotation type is a properties of the token,
        defaults to False
    base : bool, optional
        Flag for if this annotation is directly related to the signal,
        default is False

    Attributes
    ----------
    characters : set
        Set of characters for the annotation type
    ignored_characters : set
        Characters to be ignored during import
    digraphs : set
        Sequences of characters that should be considered single segments
    trans_delimiter : str or None
        Character to use for parsing transcriptions
    morph_delimiters : set
        Characters to use for parsing into morphemes
    number_behavior : str or None
        Specifies how to treat numeric characters in parsing transcriptions,
        either 'stress', 'tone' or None
    """
    def __init__(self, name, subtype, supertype, attribute = None, anchor = False,
                    token = False, base = False, speaker = None):
        self.characters = set()
        self.ignored_characters = set()
        self.digraphs = set()
        self.trans_delimiter = None
        self.morph_delimiters = set()
        self.number_behavior = None
        self._list = []
        self.name = name
        self.subtype = subtype
        self.supertype = supertype
        self.token = token
        self.base = base
        self.anchor = anchor
        self.speaker = speaker
        self.ignored = False
        if self.speaker is not None:
            self.output_name = re.sub('{}\W*'.format(self.speaker),'',self.name)
        else:
            self.output_name = self.name
        if attribute is None:
            if base:
                self.attribute = Attribute(Attribute.sanitize_name(name), 'tier', name)
            else:
                self.attribute = Attribute(Attribute.sanitize_name(name), 'spelling', name)
        else:
            self.attribute = attribute

    def pretty_print(self):
        string = ('{}:\n'.format(self.name) +
                '    Ignored characters: {}\n'.format(', '.join(self.ignored_characters)) +
                '    Digraphs: {}\n'.format(', '.join(self.digraphs)) +
                '    Transcription delimiter: {}\n'.format(self.trans_delimiter) +
                '    Morpheme delimiters: {}\n'.format(', '.join(self.morph_delimiters)) +
                '    Number behavior: {}\n'.format(self.number_behavior))
        return string

    def reset(self):
        self._list = []

    def __repr__(self):
        return '<AnnotationType "{}" with Attribute "{}"'.format(self.name,
                                                        self.attribute.name)

    def __str__(self):
        return self.name

    def __getitem__(self, key):
        return self._list[key]

    def add(self, annotations, save = True):
        for a in annotations:
            self.characters.update(a)
            if save or len(self._list) < 10:
                #If save is False, only the first 10 annotations are saved
                self._list.append(a)

    @property
    def delimited(self):
        if self.delimiter is not None:
            return True
        if self.digraphs:
            return True
        return False

    def __iter__(self):
        for x in self._list:
            yield x

    def __len__(self):
        return len(self._list)

    @property
    def digraph_pattern(self):
        if len(self.digraphs) == 0:
            return None
        return compile_digraphs(self.digraphs)

    @property
    def punctuation(self):
        return self.characters & set(string.punctuation)

    @property
    def delimiter(self):
        return self.trans_delimiter

    @delimiter.setter
    def delimiter(self, value):
        self.trans_delimiter = value

    @property
    def is_word_anchor(self):
        return not self.token and self.anchor

class DiscourseData(object):
    """
    Class for collecting information about a discourse to be loaded

    Parameters
    ----------
    name : str
        Identifier for the discourse
    annotation_types : list
        List of :class:`AnnotationType` objects


    Attributes
    ----------
    name : str
        Identifier for the discourse
    data : dict
        Dictionary containing :class:`AnnotationType` objects indexed by
        their name
    wav_path : str or None
        Path to sound file if it exists

    """
    def __init__(self, name, annotation_types):
        self.name = name
        self.data = {x.name: x for x in annotation_types}
        self.wav_path = None

    def __getitem__(self, key):
        return self.data[key]

    def __contains__(self, item):
        return item in self.data

    @property
    def types(self):
        return self.keys()

    @property
    def output_types(self):
        labels = []
        for x in self.types:
            if self[x].anchor:
                labels.append('word')
            else:
                labels.append(x)
        return labels

    @property
    def word_properties(self):
        labels = []
        for x in self.types:
            if self[x].anchor:
                continue
            if self[x].base:
                continue
            if self[x].token:
                continue
            labels.append(x)
        return labels

    @property
    def token_properties(self):
        labels = []
        for x in self.types:
            if self[x].anchor:
                continue
            if self[x].base:
                continue
            if not self[x].token:
                continue
            labels.append(x)
        return labels

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def items(self):
        return self.data.items()

    def mapping(self):
        return { x.name: x.attribute for x in self.data.values() if not x.ignored}

    @property
    def process_order(self):
        order = self.word_levels
        while len(order) < len(self.data.keys()) - len(self.base_levels):
            for k,v in self.data.items():
                if k in order:
                    continue
                if v.base:
                    continue
                if v.supertype is None:
                    order.append(k)
                    continue
                if v.supertype in order:
                    order.append(k)
        return order

    @property
    def word_levels(self):
        levels = []
        for k in self.data.keys():
            if self.data[k].is_word_anchor:
                levels.append(k)
        return levels

    @property
    def base_levels(self):
        levels = []
        for k in self.data.keys():
            if self.data[k].base:
                levels.append(k)
        return levels

    def add_annotations(self,**kwargs):
        for k,v in kwargs.items():
            self.data[k].add(v)

    def level_length(self, key):
        return len(self.data[key])

def compile_digraphs(digraph_list):
    digraph_list = sorted(digraph_list, key = lambda x: len(x), reverse=True)
    pattern = '|'.join(re.escape(d) for d in digraph_list)
    pattern += '|\d+|\S'
    return re.compile(pattern)

def inspect_directory(directory):
    """
    Function to inspect a directory and return the most likely type of
    files within it.

    Searches currently for 'textgrid', 'text', 'buckeye' and 'timit' file
    types.

    Parameters
    ----------
    directory : str
        Full path to the directory

    Returns
    -------
    str
        Most likely type of files
    dict
        Dictionary of the found files separated by the types searched for
    """
    types = ['textgrid', 'text', 'buckeye', 'timit']
    counter = {x: 0 for x in types}
    relevant_files = {x: [] for x in types}
    for root, subdirs, files in os.walk(directory):
        for f in files:
            ext = os.path.splitext(f)[-1].lower()
            if ext == '.textgrid':
                t = 'textgrid'
            elif ext == '.txt':
                t = 'text'
            elif ext == '.words':
                t = 'buckeye'
            elif ext == '.wrd':
                t = 'timit'
            else:
                continue
            counter[t] += 1
            relevant_files[t].append(f)
    max_value = max(counter.values())
    for t in ['textgrid', 'buckeye', 'timit', 'text']:
        if counter[t] == max_value:
            likely_type = t
            break

    return likely_type, relevant_files

parse_numbers = re.compile('\d+|\S')

def parse_transcription(string, annotation_type):
    """
    Parse a string into a transcription (list of segments) given an
    :class:`AnnotationType`

    Parameters
    ----------
    string : str
        String to be parsed
    annotation_type : :class:`AnnotationType`
        :class:`AnnotationType` that contains specification for how to parse the
        string

    Returns
    -------
    list of str
        Parsed string of segments in a list
    """
    md = annotation_type.morph_delimiters
    if len(md) and any(x in string for x in md):
        morphs = re.split("|".join(md),string)
        transcription = []
        for i, m in enumerate(morphs):
            trans = parse_transcription(m, annotation_type)
            for t in trans:
                t.group = i
            transcription += trans
        return transcription
    ignored = annotation_type.ignored_characters
    if ignored is not None:
        string = ''.join(x for x in string if x not in ignored)
    if annotation_type.trans_delimiter is not None:
        string = string.split(annotation_type.trans_delimiter)
    elif annotation_type.digraph_pattern is not None:
        string = annotation_type.digraph_pattern.findall(string)
    else:
        string = parse_numbers.findall(string)
    final_string = []
    for seg in string:
        if seg == '':
            continue
        num = None
        if annotation_type.number_behavior is not None:
            if annotation_type.number_behavior == 'stress':
                num = ''.join(x for x in seg if x in NUMBER_CHARACTERS)
                seg = ''.join(x for x in seg if x not in NUMBER_CHARACTERS)
            elif annotation_type.number_behavior == 'tone':
                num = ''.join(x for x in seg if x in NUMBER_CHARACTERS)
                seg = ''.join(x for x in seg if x not in NUMBER_CHARACTERS)
            if num == '':
                num = None
            if seg == '':
                setattr(final_string[-1],annotation_type.number_behavior, num)
                continue
        a = BaseAnnotation(seg)
        if annotation_type.number_behavior is not None and num is not None:
            setattr(a, annotation_type.number_behavior, num)
        final_string.append(a)
    return final_string

def text_to_lines(path):
    """
    Parse a text file into lines.

    Parameters
    ----------
    path : str
        Fully specified path to text file

    Returns
    -------
    list
        Non-empty lines in the text file
    """
    delimiter = None
    with open(path, encoding='utf-8-sig', mode='r') as f:
        text = f.read()
        if delimiter is not None and delimiter not in text:
            e = DelimiterError('The delimiter specified does not create multiple words. Please specify another delimiter.')
            raise(e)
    lines = [x.strip().split(delimiter) for x in text.splitlines() if x.strip() != '']
    return lines

def find_wav_path(path):
    """
    Find a sound file for a given file, by looking for a .wav file with the
    same base name as the given path

    Parameters
    ----------
    path : str
        Full path to an annotation file

    Returns
    -------
    str or None
        Full path of the wav file if it exists or None if it does not
    """
    name, ext = os.path.splitext(path)
    wav_path = name + '.wav'
    if os.path.exists(wav_path):
        return wav_path
    return None

def log_annotation_types(annotation_types):
    logging.info('Annotation type info')
    logging.info('--------------------')
    logging.info('')
    for a in annotation_types:
        logging.info(a.pretty_print())
