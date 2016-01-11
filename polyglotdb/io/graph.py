import csv
import os
from uuid import uuid1
import logging
import time

from collections import defaultdict

from .helper import normalize_values_for_neo4j

def initialize_csv(type, directory):
    with open(os.path.join(directory, '{}.csv'.format(type)), 'w') as f:
        pass

def initialize_csvs_header(data, directory):
    rel_paths = {}
    for x in data.types:
        rel_paths[x] = os.path.join(directory,'{}.csv'.format(x))
    rfs = {k: open(v, 'w', encoding = 'utf8') for k,v in rel_paths.items()}
    rel_writers = {}
    for k,v in rfs.items():
        token_header = ['begin', 'end', 'type_id', 'id', 'previous_id', 'discourse']
        if k == 'word':
            token_header += data.token_properties
            supertype = data[data.word_levels[0]].supertype
            if supertype is not None:
                token_header.append(supertype)
        else:
            supertype = data[k].supertype
            if supertype is not None:
                token_header.append(supertype)
        rel_writers[k] = csv.DictWriter(v, token_header, delimiter = ',')
    for x in rel_writers.values():
        x.writeheader()
    for x in rfs.values():
        x.close()

def data_to_type_csvs(parsed_data, directory):
    type_paths = {}
    data = list(parsed_data.values())[0]
    for x in data.annotation_types:
        type_paths[x] = os.path.join(directory,'{}_type.csv'.format(x))
    tfs = {k: open(v, 'w', encoding = 'utf8') for k,v in type_paths.items()}
    type_writers = {}
    type_headers = {}
    segment_type = data.segment_type
    for k,v in tfs.items():
        type_headers[k] = ['id']
        type_headers[k] += sorted(data[k].type_property_keys)
        type_writers[k] = csv.DictWriter(tfs[k], type_headers[k], delimiter = ',')
    for x in type_writers.values():
        x.writeheader()
    types = defaultdict(set)

    for data in parsed_data.values():
        for k,v in data.items():
            print(k)
            for d in v:
                type_additional = dict(zip(d.type_keys(), d.type_values()))
                #print(type_headers[k], k, type_additional, d.label)
                row = [d.sha()]
                for th in type_headers[k]:
                    if th not in ['id']:
                        row.append(type_additional[th])
                print(tuple(row))
                types[k].add(tuple(row))
    for k, v in types.items():
        for d in v:
            type_writers[k].writerow(dict(zip(type_headers[k],d)))
    for x in tfs.values():
        x.close()


def data_to_graph_csvs(data, directory):
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
    rel_paths = {}
    for x in data.annotation_types:
        rel_paths[x] = os.path.join(directory,'{}_{}.csv'.format(data.name, x))
    rfs = {k: open(v, 'w', encoding = 'utf8') for k,v in rel_paths.items()}
    rel_writers = {}
    for k,v in rfs.items():
        token_header = ['begin', 'end', 'type_id', 'id', 'previous_id']
        token_header += data[k].token_property_keys
        supertype = data[k].supertype
        if supertype is not None:
            token_header.append(supertype)
        rel_writers[k] = csv.DictWriter(v, token_header, delimiter = ',')
        rel_writers[k] .writeheader()

    segment_type = data.segment_type
    for level in data.highest_to_lowest():
        for d in data[level]:
            if d.begin is None or d.end is None:
                continue
            token_additional = dict(zip(d.token_keys(), d.token_values()))
            if d.super_id is not None:
                token_additional[data[level].supertype] = d.super_id
            rel_writers[level].writerow(dict(begin = d.begin, end = d.end,
                             type_id = d.sha(), id = d.id,
                             previous_id = d.previous_id,
                            **token_additional))
    for x in rfs.values():
        x.close()

def import_type_csvs(corpus_context, discourse_data):
    log = logging.getLogger('{}_loading'.format(corpus_context.corpus_name))
    annotation_types = corpus_context.annotation_types
    prop_temp = '''{name}: csvLine.{name}'''
    for at in annotation_types:
        type_path = 'file:///{}'.format(os.path.join(corpus_context.config.temporary_directory('csv'), '{}_type.csv'.format(at)).replace('\\','/'))

        corpus_context.graph.cypher.execute('CREATE CONSTRAINT ON (node:%s_type) ASSERT node.id IS UNIQUE' % at)

        corpus_context.graph.cypher.execute('CREATE INDEX ON :%s_type(label)' % (at,))
        properties = []
        for x in discourse_data[at].type_property_keys:
            properties.append(prop_temp.format(name=x))
            corpus_context.graph.cypher.execute('CREATE INDEX ON :%s_type(%s)' % (at, x))
        if properties:
            type_prop_string = ', ' + ', '.join(properties)
        else:
            type_prop_string = ''
        type_import_statement = '''USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
MERGE (n:{annotation_type}_type {{ id: csvLine.id{type_property_string} }})
        '''
        kwargs = {'path': type_path, 'annotation_type': at,
                    'type_property_string': type_prop_string,
                    'corpus_name': corpus_context.corpus_name}
        statement = type_import_statement.format(**kwargs)
        log.info('Loading {} types...'.format(at))
        begin = time.time()
        corpus_context.graph.cypher.execute(statement)
        log.info('Finished loading {} types!'.format(at))
        log.debug('{} type loading took: {} seconds.'.format(at, time.time() - begin))

def import_csvs(corpus_context, data):
    log = logging.getLogger('{}_loading'.format(corpus_context.corpus_name))
    log.info('Beginning to import {} into the graph database...'.format(data.name))
    initial_begin = time.time()
    name, annotation_types = data.name, data.annotation_types

    corpus_context.graph.cypher.execute('''MERGE (n:Discourse:{} {{name: {{discourse_name}}}})'''.format(corpus_context.corpus_name), discourse_name = data.name)
    prop_temp = '''{name}: csvLine.{name}'''

    for at in data.highest_to_lowest():
        rel_path = 'file:///{}'.format(os.path.join(corpus_context.config.temporary_directory('csv'), '{}_{}.csv'.format(data.name, at)).replace('\\','/'))

        corpus_context.graph.cypher.execute('CREATE CONSTRAINT ON (node:%s) ASSERT node.id IS UNIQUE' % at)

        properties = []
        corpus_context.graph.cypher.execute('CREATE INDEX ON :%s(discourse)' % (at,))
        corpus_context.graph.cypher.execute('CREATE INDEX ON :%s(begin)' % (at,))
        corpus_context.graph.cypher.execute('CREATE INDEX ON :%s(end)' % (at,))

        for x in data[at].token_property_keys:
            properties.append(prop_temp.format(name=x))
            corpus_context.graph.cypher.execute('CREATE INDEX ON :%s(%s)' % (at, x))
        st = data[at].supertype
        if st is not None:
            properties.append(prop_temp.format(name = st))
        if properties:
            token_prop_string = ', ' + ', '.join(properties)
        else:
            token_prop_string = ''
        if st is not None:
            corpus_context.graph.cypher.execute('CREATE INDEX ON :%s(%s)' % (at,st))
        rel_import_statement = '''USING PERIODIC COMMIT 3000
LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
MATCH (n:{annotation_type}_type {{id: csvLine.type_id}})
CREATE (t:{annotation_type}:{corpus_name}:{discourse}:speech {{id: csvLine.id, begin: toFloat(csvLine.begin), end: toFloat(csvLine.end), discourse: '{discourse}'{token_property_string} }})
CREATE (t)-[:is_a]->(n)
WITH t, csvLine
MATCH (p:{annotation_type}:{corpus_name}:{discourse}:speech {{id: csvLine.previous_id}})
CREATE (p)-[:precedes]->(t)'''
        kwargs = {'path': rel_path, 'annotation_type': at,
                    'token_property_string': token_prop_string,
                    'corpus_name': corpus_context.corpus_name,
                    'discourse': data.name}
        statement = rel_import_statement.format(**kwargs)
        print(statement)
        log.info('Loading {} relationships...'.format(at))
        begin = time.time()
        corpus_context.graph.cypher.execute(statement)
        log.info('Finished loading {} relationships!'.format(at))
        log.debug('{} relationships loading took: {} seconds.'.format(at, time.time() - begin))

    #log.info('Optimizing discourses...')
    #begin = time.time()
    #for d in corpus_context.discourses:
    #    statement = '''MATCH (utt:speech:unoptimized)
    #    WHERE utt.discourse = {{discourse}}
    #    SET utt :{discourse}
    #    REMOVE utt:unoptimized'''.format(discourse = d)
    #    corpus_context.graph.cypher.execute(statement, discourse = d)
    #log.info('Finished optimizing!')
    #log.debug('Optimizing took: {} seconds.'.format(time.time() - begin))
    log.info('Creating containing relationships...')
    begin = time.time()
    for at in annotation_types:
        st = data[at].supertype
        if st is None:
            continue

        statement = '''MATCH (a:{atype}:{corpus}:{discourse})
                                WITH a
                                MATCH (s:{stype}:{corpus}:{discourse} {{id: a.{stype}}})
                                WITH a, s
                                CREATE (a)-[:contained_by]->(s)'''.format(atype = at,
                                    stype = st, corpus = corpus_context.corpus_name,
                                    discourse = data.name)
        corpus_context.graph.cypher.execute(statement)
    log.info('Finished creating containing relationships!')
    log.info('Creating containing relationships took: {}.seconds'.format(time.time() - begin))
    log.info('Finished importing {} into the graph database!'.format(data.name))
    log.debug('Graph importing took: {} seconds'.format(time.time() - initial_begin))
