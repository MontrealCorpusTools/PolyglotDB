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
    for x in data.output_types:
        type_paths[x] = os.path.join(directory,'{}_type.csv'.format(x))
    tfs = {k: open(v, 'w', encoding = 'utf8') for k,v in type_paths.items()}
    type_writers = {}
    type_headers = {}
    for k,v in tfs.items():
        type_headers[k] = ['label', 'id']
        if data[k].anchor:
            type_headers[k] += data.type_properties
            if len(data.base_levels) > 0 and 'transcription' not in type_headers[k]:
                type_headers[k].append('transcription')
        type_writers[k] = csv.DictWriter(tfs[k], type_headers[k], delimiter = ',')
    for x in type_writers.values():
        x.writeheader()
    types = defaultdict(set)
    base_levels = data.base_levels

    for data in parsed_data.values():
        for i, level in enumerate(data.process_order):
            annotations = []
            for d in data[level]:
                if i == 0: #Anchor level, should have all base levels in it
                    if len(base_levels) == 1:
                        b = base_levels[0]
                        begin, end = d[b]
                        base_sequence = data[b][begin:end]
                        for j, seg in enumerate(base_sequence):
                            types[b].add((seg.label, seg.sha()))
                        if 'transcription' not in d.type_properties:
                            t = '.'.join(x.label for x in base_sequence)
                            d.type_properties['transcription'] = t
                type_additional = normalize_values_for_neo4j(d.type_properties)
                if d.label == '':
                    d.label = level
                row = [d.label, d.sha()]
                for th in type_headers[level]:
                    if th not in ['label', 'id']:
                        row.append(type_additional[th])

                types[level].add(tuple(row))
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
    for x in data.output_types:
        rel_paths[x] = os.path.join(directory,'{}_{}.csv'.format(data.name, x))
    rfs = {k: open(v, 'w', encoding = 'utf8') for k,v in rel_paths.items()}
    rel_writers = {}
    for k,v in rfs.items():
        token_header = ['begin', 'end', 'type_id', 'id', 'previous_id']
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
        rel_writers[k] .writeheader()

    base_levels = data.base_levels
    base_ind = 0

    print(data.base_levels)
    print(data.output_types)
    for i, level in enumerate(data.process_order):
        annotations = []
        for k,d in enumerate(data[level]):
            if len(base_levels) > 0:
                b = base_levels[0]
                begin, end = d[b]
                base_sequence = data[b][begin:end]

                if i == 0: #Anchor level, should have all base levels in it

                    for j, seg in enumerate(base_sequence):
                        if j == 0:
                            if k == 0:
                                previous_id = None
                            else:
                                _, end = data[level][k-1][b]
                                previous_id = data[b][end - 1].id
                        else:
                            previous_id = base_sequence[j-1].id
                        begin = seg.begin
                        if begin is None:
                            begin = base_ind
                        end = seg.end
                        if end is None:
                            end = base_ind + 1
                        row = dict(begin=begin, end = end,
                                            type_id = seg.sha(),
                                            previous_id = previous_id,
                                            id = seg.id)
                        supertype = data[b].supertype
                        if seg.super_id is not None:
                            row[supertype] = seg.super_id
                        rel_writers[base_levels[0]].writerow(row)
                        base_ind += 1
            token_additional = normalize_values_for_neo4j(d.token_properties)
            if d.super_id is not None:
                token_additional[data[level].supertype] = d.super_id

            if d.label == '':
                d.label = level
            if k == 0:
                previous_id = None
            else:
                previous_id = data[level][k-1].id
            if len(base_levels) > 0:
                try:
                    begin = base_sequence[0].begin
                    end = base_sequence[-1].end
                except IndexError:
                    continue # Don't include words with empty transcriptions
            else:
                begin = base_ind
                end = base_ind + 1
                base_ind += 1
            rel_writers[level].writerow(dict(begin = begin, end = end,
                             type_id = d.sha(), id = d.id,
                             previous_id = previous_id,
                            **token_additional))
    for x in rfs.values():
        x.close()

def import_type_csvs(corpus_context, word_type_properties):
    log = logging.getLogger('{}_loading'.format(corpus_context.corpus_name))
    annotation_types = corpus_context.relationship_types
    prop_temp = '''{name}: csvLine.{name}'''
    for at in annotation_types:
        if at == 'pause':
            continue
        type_path = 'file:///{}'.format(os.path.join(corpus_context.config.temporary_directory('csv'), '{}_type.csv'.format(at)).replace('\\','/'))
        corpus_context.graph.cypher.execute('CREATE CONSTRAINT ON (node:%s_type) ASSERT node.id IS UNIQUE' % at)
        corpus_context.graph.cypher.execute('CREATE INDEX ON :%s_type(label)' % (at,))
        properties = []
        if at == 'word':
            for x in word_type_properties:
                properties.append(prop_temp.format(name=x))
                corpus_context.graph.cypher.execute('CREATE INDEX ON :%s_type(%s)' % (at, x))
        if properties:
            type_prop_string = ', ' + ', '.join(properties)
        else:
            type_prop_string = ''
        type_import_statement = '''USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
MERGE (n:{annotation_type}_type {{ label: csvLine.label, id: csvLine.id{type_property_string} }})
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
    name, annotation_types = data.name, data.output_types
    token_properties = data.token_properties
    type_properties = data.type_properties

    prop_temp = '''{name}: csvLine.{name}'''

    for at in annotation_types:
        rel_path = 'file:///{}'.format(os.path.join(corpus_context.config.temporary_directory('csv'), '{}_{}.csv'.format(data.name, at)).replace('\\','/'))

        corpus_context.graph.cypher.execute('CREATE CONSTRAINT ON (node:%s) ASSERT node.id IS UNIQUE' % at)

        properties = []
        corpus_context.graph.cypher.execute('CREATE INDEX ON :%s(discourse)' % (at,))
        corpus_context.graph.cypher.execute('CREATE INDEX ON :%s(begin)' % (at,))
        corpus_context.graph.cypher.execute('CREATE INDEX ON :%s(end)' % (at,))
        if at == 'word':
            for x in token_properties:
                properties.append(prop_temp.format(name=x))
                corpus_context.graph.cypher.execute('CREATE INDEX ON :%s(%s)' % (at, x))
            st = data[data.word_levels[0]].supertype
        else:
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
