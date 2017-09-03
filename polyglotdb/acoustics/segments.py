

class Segment(object):
    def __init__(self, **kwargs):
        self.properties = kwargs

    def __repr__(self):
        return '<Segment object with properties: {}>'.format(str(self))

    def __str__(self):
        return str(self.properties)

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.properties[item]
        elif isinstance(item, slice):
            if item.start is None:
                start = 0
            else:
                start = item.start
            if item.stop is None:
                stop = -1
            else:
                stop = item.stop
            if item.step is None:
                step = 1
            else:
                step = item.step
            return [self[i] for i in range(start, stop, step)]
        if item == 0:
            return self.properties['file_path']
        elif item == 1:
            return self.properties['begin']
        elif item == 2:
            return self.properties['end']
        elif item == 3:
            return self.properties['channel']

    def __hash__(self):
        return hash((self[0], self[1], self[2], self[3]))

    def __eq__(self, other):
        if self[0] != other[0]:
            return False
        if self[1] != other[1]:
            return False
        if self[2] != other[2]:
            return False
        if self[3] != other[3]:
            return False
        return True

    def __lt__(self, other):
        if self[0] < other[0]:
            return True
        elif self[0] == other[0]:
            if self[1] < other[1]:
                return True
            elif self[1] == other[1]:
                if self[2] < other[2]:
                    return True
        return False


class SegmentMapping(object):
    def __init__(self):
        self.segments = []

    def add_segment(self, **kwargs):
        self.segments.append(Segment(**kwargs))

    def levels(self, property_key):
        return set(x[property_key] for x in self.segments)

    def grouped_mapping(self, property_key):
        data = {x: [] for x in self.levels(property_key)}
        for s in self.segments:
            data[s[property_key]].append(s)
        return data

    def __iter__(self):
        for s in self.segments:
            yield s


def generate_segments(corpus_context, annotation_type='utterance', subset=None, file_type='vowel',
                      duration_threshold=None):
    """
    Generate segment vectors for an annotation type, to be used as input to analyze_file_segments.

    Parameters
    ----------
    corpus_context : :class:`~polyglot.corpus.context.CorpusContext`
        The CorpusContext object of the corpus
    annotation_type : str, optional
        The type of annotation to use in generating segments, defaults to utterance
    subset : str, optional
        Specify a subset to use for generating segments
    file_type : str, optional
        One of 'low_freq', 'vowel', or 'consonant', specifies the type of audio file to use
    duration_threshold: float, optional
        Segments with length shorter than this value (in milliseconds) will not be included

    Returns
    -------
    SegmentMapping
        Object containing segments to be analyzed
    """
    if annotation_type not in corpus_context.hierarchy.annotation_types:
        raise Exception()
    if subset is not None and not corpus_context.hierarchy.has_type_subset(annotation_type, subset):
        raise Exception()
    speakers = corpus_context.speakers
    segment_mapping = SegmentMapping()
    for s in speakers:
        statement = '''MATCH (s:Speaker:{corpus_name})-[r:speaks_in]->(d:Discourse:{corpus_name})
                    WHERE s.name = {{speaker_name}}
                    RETURN d, r'''.format(corpus_name=corpus_context.cypher_safe_name)
        results = corpus_context.execute_cypher(statement, speaker_name=s)

        for r in results:
            channel = r['r']['channel']
            discourse = r['d']['name']
            if file_type == 'vowel':
                file_path = r['d']['vowel_file_path']
            elif file_type == 'low_freq':
                file_path = r['d']['low_freq_file_path']
            else:
                file_path = r['d']['consonant_file_path']
            at = getattr(corpus_context, annotation_type)
            qr = corpus_context.query_graph(at)
            if subset is not None:
                qr = qr.filter(at.subset == subset)
            qr = qr.filter(at.discourse.name == discourse)
            qr = qr.filter(at.speaker.name == s)
            if qr.count() == 0:
                continue
            annotations = qr.all()
            if annotations is not None:
                for a in annotations:
                    if duration_threshold is not None and a.end - a.begin < duration_threshold:
                        continue
                    segment_mapping.add_segment(file_path=file_path, begin=a.begin, end=a.end, label=a.label,
                                                id=a.id, discourse=discourse, channel=channel, speaker=s,
                                                annotation_type=annotation_type)
    return segment_mapping


def generate_vowel_segments(corpus_context, duration_threshold=None):
    """
    Generate segment vectors for each vowel, to be used as input to analyze_file_segments.

    Parameters
    ----------
    corpus_context : :class:`polyglot.corpus.context.CorpusContext`
        The CorpusContext object of the corpus
    duration_threshold: float, optional
        Segments with length shorter than this value (in milliseconds) will not be included

    Returns
    -------
    SegmentMapping
        Object containing vowel segments to be analyzed
    """
    return generate_segments(corpus_context, annotation_type=corpus_context.phone_name, subset='vowel',
                             file_type='vowel', duration_threshold=duration_threshold)


def generate_utterance_segments(corpus_context, file_type='vowel', duration_threshold=None):
    """
    Generate segment vectors for each utterance, to be used as input to analyze_file_segments.

    Parameters
    ----------
    corpus_context : :class:`polyglot.corpus.context.CorpusContext`
        The CorpusContext object of the corpus
    file_type : str, optional
        One of 'low_freq', 'vowel', or 'consonant', specifies the type of audio file to use
    duration_threshold: float, optional
        Segments with length shorter than this value (in milliseconds) will not be included

    Returns
    -------
    SegmentMapping
        Object containing utterance segments to be analyzed
    """
    return generate_segments(corpus_context, annotation_type='utterance', subset=None, file_type=file_type,
                      duration_threshold=duration_threshold)
