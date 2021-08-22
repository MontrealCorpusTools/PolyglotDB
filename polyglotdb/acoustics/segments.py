from conch.analysis.segments import SegmentMapping


def generate_segments(corpus_context, annotation_type='utterance', subset=None, file_type='vowel',
                      duration_threshold=0.001, padding=0, fetch_subannotations=False):
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
        Segments with length shorter than this value (in seconds) will not be included

    Returns
    -------
    SegmentMapping
        Object containing segments to be analyzed
    """
    if annotation_type not in corpus_context.hierarchy.annotation_types:
        raise Exception()
    if subset is not None and not corpus_context.hierarchy.has_type_subset(annotation_type, subset) and not corpus_context.hierarchy.has_token_subset(annotation_type, subset):
        raise Exception()
    speakers = corpus_context.speakers
    segment_mapping = SegmentMapping()
    for s in speakers:
        statement = '''MATCH (s:Speaker:{corpus_name})-[r:speaks_in]->(d:Discourse:{corpus_name})
                    WHERE s.name = $speaker_name
                    RETURN d, r.channel as channel'''.format(corpus_name=corpus_context.cypher_safe_name)
        results = corpus_context.execute_cypher(statement, speaker_name=s)
        for r in results:
            channel = r['channel']
            discourse = r['d']['name']
            if file_type == 'vowel':
                file_path = r['d']['vowel_file_path']
            elif file_type == 'low_freq':
                file_path = r['d']['low_freq_file_path']
            else:
                file_path = r['d']['consonant_file_path']
            if file_path is None:
                print("Skipping discourse {} because no wav file exists.".format(discourse))
                continue
            discourse_duration = r['d']['duration']
            at = getattr(corpus_context, annotation_type)
            qr = corpus_context.query_graph(at)
            if subset is not None:
                qr = qr.filter(at.subset == subset)
            qr = qr.filter(at.discourse.name == discourse)
            qr = qr.filter(at.end <= discourse_duration)
            qr = qr.filter(at.begin != at.end) # Skip zero duration segments if they exist
            if duration_threshold is not None:
                qr = qr.filter(at.duration >= duration_threshold)
            qr = qr.filter(at.speaker.name == s)
            if annotation_type != 'utterance' and 'utterance'in corpus_context.hierarchy.annotation_types:
                qr.preload(at.utterance)
            else:
                qr.preload(at.discourse)
            if fetch_subannotations:
                for t in corpus_context.hierarchy.annotation_types:
                    if t in corpus_context.hierarchy.subannotations:
                        for s in corpus_context.hierarchy.subannotations[t]:
                            if t == 'utterance':
                                qr = qr.preload(getattr(corpus_context.utterance, s))
                            else:
                                qr = qr.preload(getattr(getattr(corpus_context.utterance, t), s))

            if qr.count() == 0:
                continue
            annotations = qr.all()
            if annotations is not None:
                for a in annotations:
                    if annotation_type == 'utterance':
                        utt_id = a.id
                    elif 'utterance'not in corpus_context.hierarchy.annotation_types:
                        utt_id = None
                    else:
                        utt_id = a.utterance.id
                    if fetch_subannotations:
                        #Get subannotations too
                        subannotations = {}
                        if annotation_type in corpus_context.hierarchy.subannotations and corpus_context.hierarchy.subannotations[annotation_type]:
                            for s in corpus_context.hierarchy.subannotations[annotation_type]:
                                if getattr(a, s):
                                    subannotations[s] = getattr(a, s)[0]
                        segment_mapping.add_file_segment(file_path, a.begin, a.end, label=a.label, id=a.id,
                                                         utterance_id=utt_id, discourse=discourse, channel=channel, speaker=s,
                                                         annotation_type=annotation_type, padding=padding,
                                                         subannotations=subannotations)
                    else:
                        segment_mapping.add_file_segment(file_path, a.begin, a.end, label=a.label, id=a.id,
                                                         utterance_id=utt_id, discourse=discourse, channel=channel, speaker=s,
                                                         annotation_type=annotation_type, padding=padding)
    return segment_mapping


def generate_vowel_segments(corpus_context, duration_threshold=None, padding=0, vowel_label='vowel'):
    """
    Generate segment vectors for each vowel, to be used as input to analyze_file_segments.

    Parameters
    ----------
    corpus_context : :class:`polyglot.corpus.context.CorpusContext`
        The CorpusContext object of the corpus
    duration_threshold: float, optional
        Segments with length shorter than this value (in seconds) will not be included

    Returns
    -------
    SegmentMapping
        Object containing vowel segments to be analyzed
    """
    return generate_segments(corpus_context, annotation_type=corpus_context.phone_name, subset=vowel_label,
                             file_type='vowel', duration_threshold=duration_threshold, padding=padding)


def generate_utterance_segments(corpus_context, file_type='vowel', duration_threshold=None, padding=0):
    """
    Generate segment vectors for each utterance, to be used as input to analyze_file_segments.

    Parameters
    ----------
    corpus_context : :class:`polyglot.corpus.context.CorpusContext`
        The CorpusContext object of the corpus
    file_type : str, optional
        One of 'low_freq', 'vowel', or 'consonant', specifies the type of audio file to use
    duration_threshold: float, optional
        Segments with length shorter than this value (in seconds) will not be included

    Returns
    -------
    SegmentMapping
        Object containing utterance segments to be analyzed
    """
    return generate_segments(corpus_context, annotation_type='utterance', subset=None, file_type=file_type,
                             duration_threshold=duration_threshold, padding=padding)
