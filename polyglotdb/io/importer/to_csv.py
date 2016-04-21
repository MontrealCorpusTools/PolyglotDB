import csv
import os
from uuid import uuid1
from collections import defaultdict

def data_to_type_csvs(corpus_context, types, type_headers):
    directory = corpus_context.config.temporary_directory('csv')
    tfs = {}

    for k in type_headers.keys():
        tfs[k] = open(os.path.join(directory,'{}_type.csv'.format(k)), 'w', encoding = 'utf8')
    type_writers = {}
    for k,v in type_headers.items():
        type_writers[k] = csv.DictWriter(tfs[k], type_headers[k], delimiter = ',')
        type_writers[k].writeheader()

    for k,v in types.items():
        for t in v:
            type_writers[k].writerow(dict(zip(type_headers[k],t)))
    for x in tfs.values():
        x.close()

def data_to_graph_csvs(corpus_context, data):
    """
    Convert a DiscourseData object into CSV files for efficient loading
    of graph nodes and relationships

    Parameters
    ----------
    data : DiscourseData
        Data to load into a graph
    directory: str
        Full path to a directory to store CSV files
    """
    directory = corpus_context.config.temporary_directory('csv')
    rfs = {}
    for x in data.annotation_types:
        path = os.path.join(directory,'{}_{}.csv'.format(data.name, x))
        rfs[x] = open(path, 'w', encoding = 'utf8')
    rel_writers = {}

    for k,v in rfs.items():
        token_header = ['begin', 'end', 'type_id', 'id', 'previous_id', 'speaker', 'discourse']
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
            subanno_files[k,s] = open(path, 'w', encoding = 'utf8')
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
                             previous_id = d.previous_id, discourse = data.name,
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

def time_data_to_csvs(type, directory, discourse, timed_data):
    with open(os.path.join(directory, '{}_{}.csv'.format(discourse, type)), 'w') as f:
        for t in timed_data:
            f.write('{},{},{}\n'.format(t[0], t[1], uuid1()))

def syllables_data_to_csvs(corpus_context, data, split_name):
    path = os.path.join(corpus_context.config.temporary_directory('csv'),
                        '{}_syllable.csv'.format(split_name))
    header = ['id', 'prev_id', 'vowel_id', 'onset_id', 'coda_id', 'begin', 'end', 'label', 'type_id']
    with open(path, 'w') as f:
        writer = csv.DictWriter(f, header, delimiter = ',')
        writer.writeheader()
        for d in data:
            writer.writerow(d)

def nonsyls_data_to_csvs(corpus_context, data, split_name):
    path = os.path.join(corpus_context.config.temporary_directory('csv'),
                        '{}_nonsyl.csv'.format(split_name))
    header = ['id', 'prev_id', 'break', 'onset_id', 'coda_id', 'begin', 'end', 'label', 'type_id']
    with open(path, 'w') as f:
        writer = csv.DictWriter(f, header, delimiter = ',')
        writer.writeheader()
        for d in data:
            writer.writerow(d)


def subannotations_data_to_csv(corpus_context, type, data):
    path = os.path.join(corpus_context.config.temporary_directory('csv'),
                        '{}_subannotations.csv'.format(type))
    header = sorted(data[0].keys())
    with open(path, 'w') as f:
        writer = csv.DictWriter(f, header, delimiter = ',')
        writer.writeheader()
        for d in data:
            writer.writerow(d)

def lexicon_data_to_csvs(corpus_context, data, case_sensitive = False):
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
    directory = corpus_context.config.temporary_directory('csv')
    with open(os.path.join(directory, 'feature_import.csv'), 'w') as f:
        header = ['label'] + sorted(next(iter(data.values())).keys())
        writer = csv.DictWriter(f, header, delimiter = ',')
        writer.writeheader()
        for k,v in sorted(data.items()):
            v['label'] = k
            writer.writerow(v)
