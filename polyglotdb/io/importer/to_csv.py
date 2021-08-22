import csv
import os
import re


def write_csv_file(path, header, data, mode='w'):
    with open(path, mode, newline='', encoding='utf8') as f:
        writer = csv.DictWriter(f, header, delimiter=',')
        if mode == 'w':
            writer.writeheader()
        for d in data:
            writer.writerow(d)


def data_to_type_csvs(corpus_context, types, type_headers):
    """
    Convert a types object into a CSV file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.ImportContext`
        CorpusContext object to use
    types : dict
        The type information for annotation types
    type_headers : dict
        Header information for the CSV file
    """
    directory = corpus_context.config.temporary_directory('csv')

    for k, v in type_headers.items():
        path = os.path.join(directory, '{}_type.csv'.format(k))
        header = v
        data = [dict(zip(v, t)) for t in types[k]]
        write_csv_file(path, header, data)


def data_to_graph_csvs(corpus_context, data):
    """
    Convert a DiscourseData object into CSV files for efficient loading
    of graph nodes and relationships

    Parameters
    ----------
    data : :class:`~polyglotdb.io.helper.DiscourseData`
        Data to load into a graph
    directory: str
        Full path to a directory to store CSV files
    """
    directory = corpus_context.config.temporary_directory('csv')
    rfs = {}
    rel_writers = {}
    token_headers = data.token_headers
    for s in data.speakers:
        for x in data.annotation_types:
            path = os.path.join(directory, '{}_{}.csv'.format(re.sub(r'\W', '_', s), x))
            rfs[s, x] = open(path, 'a', newline='', encoding='utf8')
            rel_writers[s, x] = csv.DictWriter(rfs[s, x], token_headers[x], delimiter=',')
    subanno_files = {}
    subanno_writers = {}
    for sp in data.speakers:
        for k, v in data.hierarchy.subannotations.items():
            for s in v:
                path = os.path.join(directory, '{}_{}_{}.csv'.format(re.sub(r'\W', '_', sp), k, s))
                subanno_files[sp, k, s] = open(path, 'a', newline='', encoding='utf8')
                header = ['id', 'begin', 'end', 'annotation_id', 'label']
                subanno_writers[sp, k, s] = csv.DictWriter(subanno_files[sp, k, s], header, delimiter=',')

    for level in data.highest_to_lowest():
        for d in data[level]:
            if d.begin is None or d.end is None:
                continue
            token_additional = dict(zip(d.token_keys(), d.token_values()))
            if d.super_id is not None:
                token_additional[data[level].supertype] = d.super_id
            s = d.speaker
            if s is None:
                s = 'unknown'
            rel_writers[s, level].writerow(dict(begin=d.begin, end=d.end,
                                                type_id=d.sha(corpus=corpus_context.corpus_name),
                                                id=d.id, speaker=s, discourse=data.name,
                                                previous_id=d.previous_id,
                                                **token_additional))
            if d.subannotations:
                for sub in d.subannotations:
                    row = {'begin': sub.begin, 'end': sub.end, 'label': sub.label,
                           'annotation_id': d.id, 'id': sub.id}
                    subanno_writers[s, level, sub.type].writerow(row)

    for x in rfs.values():
        x.close()
    for x in subanno_files.values():
        x.close()


def utterance_data_to_csvs(corpus_context, speaker, discourse, data):
    """
    Convert time data into a CSV file

    Parameters
    ----------
    type : obj
        the type of data
    directory : str
        path to the directory
    discourse : str
        the name of the discourse
    timed_data : list
        the timing data
    """
    path = os.path.join(corpus_context.config.temporary_directory('csv'),
                        '{}_{}_utterance.csv'.format(re.sub(r'\W', '_', speaker), discourse))
    header = ['id', 'prev_id', 'begin_word_id', 'end_word_id']
    write_csv_file(path, header, data, 'a')


def utterance_enriched_data_to_csvs(corpus_context, utterance_data):
    """
    Convert time data into a CSV file

    Parameters
    ----------
    type : obj
        the type of data
    directory : str
        path to the directory
    discourse : str
        the name of the discourse
    timed_data : list
        the timing data
    """
    directory = corpus_context.config.temporary_directory('csv')
    with open(os.path.join(directory, 'utterance_enrichment.csv'), 'w') as f:
        header = ['id'] + sorted(next(iter(utterance_data.values())).keys())
        writer = csv.DictWriter(f, header, delimiter=',')
        writer.writeheader()
        for k, v in sorted(utterance_data.items()):
            v['id'] = k
            writer.writerow(v)


def syllables_data_to_csvs(corpus_context, speaker, discourse, syllable_data):
    """
    Convert syllable data into a CSV file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.syllabic.SyllabicContext`
        the corpus object
    data : dict
        Data to load into a csv
  

    """
    path = os.path.join(corpus_context.config.temporary_directory('csv'),
                        '{}_{}_syllable.csv'.format(re.sub(r'\W', '_', speaker), discourse))
    header = ['id', 'prev_id', 'vowel_id', 'onset_id', 'coda_id', 'begin', 'end', 'label', 'type_id']
    write_csv_file(path, header, syllable_data, 'a')


def syllables_enrichment_data_to_csvs(corpus_context, data):
    """
    Convert syllable enrichment data into a CSV file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.syllabic.SyllabicContext`
        the corpus object
    data : Dict
        Data to load into a csv
    """
    directory = corpus_context.config.temporary_directory('csv')
    with open(os.path.join(directory, 'syllable_import.csv'), 'w') as f:
        header = ['label'] + sorted(next(iter(data.values())).keys())
        writer = csv.DictWriter(f, header, delimiter=',')
        writer.writeheader()
        for k, v in sorted(data.items()):
            v['label'] = k
            writer.writerow(v)


def nonsyls_data_to_csvs(corpus_context, speaker, discourse, data):
    """
    Convert non-syllable data into a CSV file

    Parameters
    ----------
    corpus_context:class:`~polyglotdb.corpus.CorpusContext`
        the corpus object
    data : :class:`~polyglotdb.io.helper.DiscourseData`
        Data to load into a graph
    split_name : str
        identifier of the file to load

    """
    path = os.path.join(corpus_context.config.temporary_directory('csv'),
                        '{}_{}_nonsyl.csv'.format(re.sub(r'\W', '_', speaker), discourse))
    header = ['id', 'prev_id', 'break', 'onset_id', 'coda_id', 'begin', 'end', 'label', 'type_id']
    write_csv_file(path, header, data, 'a')


def subannotations_data_to_csv(corpus_context, type, data):
    """
    Convert subannotation data into a CSV file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.AnnotatedContext`
        the corpus object
    data : :class:`~polyglotdb.io.helper.DiscourseData`
        Data to load into a graph
    type : str
        identifier of the file to load

    """
    path = os.path.join(corpus_context.config.temporary_directory('csv'),
                        '{}_subannotations.csv'.format(type))
    header = sorted(data[0].keys())
    write_csv_file(path, header, data)


def lexicon_data_to_csvs(corpus_context, data, case_sensitive=False):
    """
    Convert lexicon data into a CSV file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.CorpusContext`
        the corpus object
    data : :class:`~polyglotdb.io.helper.DiscourseData`
        Data to load into a graph
    case_sensitive : boolean
        defaults to False
    """
    directory = corpus_context.config.temporary_directory('csv')
    with open(os.path.join(directory, 'lexicon_import.csv'), 'w') as f:
        header = ['label'] + sorted(next(iter(data.values())).keys())
        writer = csv.DictWriter(f, header, delimiter=',')
        writer.writeheader()
        for k, v in sorted(data.items()):
            if not case_sensitive:
                k =  k.lower()
            v['label'] = k
            writer.writerow(v)


def feature_data_to_csvs(corpus_context, data):
    """
    Convert feature data into a CSV file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.CorpusContext`
        the corpus object
    data : :class:`~polyglotdb.io.helper.DiscourseData`
        Data to load into a graph
    """
    directory = corpus_context.config.temporary_directory('csv')
    with open(os.path.join(directory, 'feature_import.csv'), 'w') as f:
        header = ['label'] + sorted(next(iter(data.values())).keys())
        writer = csv.DictWriter(f, header, delimiter=',')
        writer.writeheader()
        for k, v in sorted(data.items()):
            v['label'] = k
            writer.writerow(v)


def speaker_data_to_csvs(corpus_context, data):
    """
    Convert speaker data into a CSV file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.spoken.SpokenContext`
        the corpus object
    data : :class:`~polyglotdb.io.helper.DiscourseData`
        Data to load into a graph
    """
    directory = corpus_context.config.temporary_directory('csv')
    with open(os.path.join(directory, 'speaker_import.csv'), 'w') as f:
        header = ['name'] + sorted(next(iter(data.values())).keys())
        writer = csv.DictWriter(f, header, delimiter=',')
        writer.writeheader()
        for k, v in sorted(data.items()):
            v['name'] = k
            writer.writerow(v)


def discourse_data_to_csvs(corpus_context, data):
    """
    Convert discourse data into a CSV file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.spoken.SpokenContext`
        the corpus object
    data : :class:`~polyglotdb.io.helper.DiscourseData`
        Data to load into a graph
    type : str
        identifier of the file to load
    """
    directory = corpus_context.config.temporary_directory('csv')
    with open(os.path.join(directory, 'discourse_import.csv'), 'w') as f:
        header = ['name'] + sorted(next(iter(data.values())).keys())
        writer = csv.DictWriter(f, header, delimiter=',')
        writer.writeheader()
        for k, v in sorted(data.items()):
            v['name'] = k
            writer.writerow(v)


def create_utterance_csvs(corpus_context):
    header = ['id', 'prev_id', 'begin_word_id', 'end_word_id']
    for s in corpus_context.speakers:
        discourses = corpus_context.get_discourses_of_speaker(s)
        for d in discourses:
            path = os.path.join(corpus_context.config.temporary_directory('csv'),
                                '{}_{}_utterance.csv'.format(re.sub(r'\W', '_', s), d))
            with open(path, 'w', newline='', encoding='utf8') as f:
                writer = csv.DictWriter(f, header, delimiter=',')
                writer.writeheader()


def create_syllabic_csvs(corpus_context):
    header = ['id', 'prev_id', 'vowel_id', 'onset_id', 'coda_id', 'begin', 'end', 'label', 'type_id']
    for s in corpus_context.speakers:
        discourses = corpus_context.get_discourses_of_speaker(s)
        for d in discourses:
            path = os.path.join(corpus_context.config.temporary_directory('csv'),
                                '{}_{}_syllable.csv'.format(re.sub(r'\W', '_', s), d))
            with open(path, 'w', newline='', encoding='utf8') as f:
                writer = csv.DictWriter(f, header, delimiter=',')
                writer.writeheader()


def create_nonsyllabic_csvs(corpus_context):
    header = ['id', 'prev_id', 'break', 'onset_id', 'coda_id', 'begin', 'end', 'label', 'type_id']
    for s in corpus_context.speakers:
        discourses = corpus_context.get_discourses_of_speaker(s)
        for d in discourses:
            path = os.path.join(corpus_context.config.temporary_directory('csv'),
                                '{}_{}_nonsyl.csv'.format(re.sub(r'\W', '_', s), d))
            with open(path, 'w', newline='', encoding='utf8') as f:
                writer = csv.DictWriter(f, header, delimiter=',')
                writer.writeheader()
