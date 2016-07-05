import csv
import os
from collections import defaultdict
from polyglotdb import AlphabetError

def write_csv_file(path, header, data):
    with open(path, 'w', newline = '') as f:
        writer = csv.DictWriter(f, header, delimiter = ',')
        writer.writeheader()
        for d in data:
            writer.writerow(d)

def data_to_type_csvs(corpus_context, types, type_headers):
    """
    Convert a types object into a CSV file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.CorpusContext`
        the corpus
    types : obj
        the types in the corpus
    type_headers : dict
        headers for types
    """
    directory = corpus_context.config.temporary_directory('csv')
    tfs = {}

    for k, v in type_headers.items():
        path = os.path.join(directory,'{}_type.csv'.format(k))
        header = v
        data = [dict(zip(v,t)) for t in types[k]]
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
    for x in data.annotation_types:
        path = os.path.join(directory,'{}_{}.csv'.format(data.name, x))
        rfs[x] = open(path, 'w', newline = '', encoding = 'utf8')
    rel_writers = {}

    for k,v in rfs.items():
        token_header = ['begin', 'end', 'type_id', 'id', 'previous_id', 'speaker']
        token_header += data[k].token_property_keys
        supertype = data[k].supertype
        if supertype is not None:
            token_header.append(supertype)
        rel_writers[k] = csv.DictWriter(v, token_header, delimiter = ',')
        rel_writers[k].writeheader()

    subanno_files = {}
    subanno_writers = {}
    for k,v in data.hierarchy.subannotations.items():
        for s in v:
            path = os.path.join(directory,'{}_{}_{}.csv'.format(data.name, k, s))
            subanno_files[k,s] = open(path, 'w', newline = '', encoding = 'utf8')
            header = ['id', 'begin', 'end', 'annotation_id', 'label']
            subanno_writers[k,s] = csv.DictWriter(subanno_files[k,s], header, delimiter = ',')
            subanno_writers[k,s].writeheader()

    segment_type = data.segment_type
    for level in data.highest_to_lowest():
        for d in data[level]:
            if d.begin is None or d.end is None:
                continue
            token_additional = dict(zip(d.token_keys(), d.token_values()))
            if d.super_id is not None:
                token_additional[data[level].supertype] = d.super_id
            rel_writers[level].writerow(dict(begin = d.begin, end = d.end,
                             type_id = d.sha(corpus = corpus_context.corpus_name),
                             id = d.id, speaker = d.speaker,
                             previous_id = d.previous_id,
                            **token_additional))
            if d.subannotations:
                for sub in d.subannotations:
                    row = {'begin': sub.begin, 'end':sub.end, 'label': sub.label,
                            'annotation_id': d.id, 'id': sub.id}
                    subanno_writers[level, sub.type].writerow(row)

    for x in rfs.values():
        x.close()
    for x in subanno_files.values():
        x.close()

def utterance_data_to_csvs(corpus_context, data, discourse):
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
                        '{}_utterance.csv'.format(discourse))
    header = ['id', 'prev_id', 'begin_word_id', 'end_word_id']
    write_csv_file(path, header, data)

def syllables_data_to_csvs(corpus_context, data, split_name):
    """
    Convert syllable data into a CSV file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.CorpusContext`
        the corpus object
    data : :class:`~polyglotdb.io.helper.DiscourseData`
        Data to load into a graph
    split_name : str
        identifier of the file to load

    """
    path = os.path.join(corpus_context.config.temporary_directory('csv'),
                        '{}_syllable.csv'.format(split_name))
    header = ['id', 'prev_id', 'vowel_id', 'onset_id', 'coda_id', 'begin', 'end', 'label', 'type_id']
    write_csv_file(path, header, data)

def nonsyls_data_to_csvs(corpus_context, data, split_name):
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
                        '{}_nonsyl.csv'.format(split_name))
    header = ['id', 'prev_id', 'break', 'onset_id', 'coda_id', 'begin', 'end', 'label', 'type_id']
    write_csv_file(path, header, data)


def subannotations_data_to_csv(corpus_context, type, data):
    """
    Convert subannotation data into a CSV file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.CorpusContext`
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

def lexicon_data_to_csvs(corpus_context, data, case_sensitive = False):
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
        writer = csv.DictWriter(f, header, delimiter = ',')
        writer.writeheader()
        for k,v in sorted(data.items()):
            if not case_sensitive:
                k = '(?i)' + k
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
        try:
            header = ['label'] + sorted(next(iter(data.values())).keys())
        except(StopIteration):
            raise(AlphabetError)
        writer = csv.DictWriter(f, header, delimiter = ',')
        writer.writeheader()
        for k,v in sorted(data.items()):
            v['label'] = k
            writer.writerow(v)

def speaker_data_to_csvs(corpus_context, data):
    """
    Convert speaker data into a CSV file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.CorpusContext`
        the corpus object
    data : :class:`~polyglotdb.io.helper.DiscourseData`
        Data to load into a graph
    """
    directory = corpus_context.config.temporary_directory('csv')
    with open(os.path.join(directory, 'speaker_import.csv'), 'w') as f:
        header = ['name'] + sorted(next(iter(data.values())).keys())
        writer = csv.DictWriter(f, header, delimiter = ',')
        writer.writeheader()
        for k,v in sorted(data.items()):
            v['name'] = k
            writer.writerow(v)

def discourse_data_to_csvs(corpus_context, data):
    """
    Convert discourse data into a CSV file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.CorpusContext`
        the corpus object
    data : :class:`~polyglotdb.io.helper.DiscourseData`
        Data to load into a graph
    type : str
        identifier of the file to load
    """
    directory = corpus_context.config.temporary_directory('csv')
    with open(os.path.join(directory, 'discourse_import.csv'), 'w') as f:
        header = ['name'] + sorted(next(iter(data.values())).keys())
        writer = csv.DictWriter(f, header, delimiter = ',')
        writer.writeheader()
        for k,v in sorted(data.items()):
            v['name'] = k
            writer.writerow(v)
