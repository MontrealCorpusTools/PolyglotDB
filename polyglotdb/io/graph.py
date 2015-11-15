import csv
import os
from uuid import uuid1
import logging
import time

from collections import defaultdict

from .helper import normalize_values_for_neo4j

def time_data_to_csvs(type, directory, discourse, timed_data):
    with open(os.path.join(directory, '{}_{}.csv'.format(discourse, type)), 'w') as f:
        for t in timed_data:
            f.write('{},{}\n'.format(*t))

def import_utterance_csv(corpus_context, discourse):
    csv_path = 'file:///{}'.format(os.path.join(corpus_context.config.temporary_directory('csv'), '{}_utterance.csv'.format(discourse)).replace('\\','/'))
    statement = '''USING PERIODIC COMMIT 1000
            LOAD CSV FROM "{path}" AS csvLine
            MATCH (begin:Anchor:{corpus}:{discourse} {{time: toFloat(csvLine[0])}}),
            (end:Anchor:{corpus}:{discourse} {{time: toFloat(csvLine[1])}})
            MERGE (begin)-[:r_utterance]->(utt:utterance:{corpus}:{discourse}:speech)-[:r_utterance]->(end)
            MERGE (utt)-[:is_a]->(u_type:utterance_type)
            WITH utt, begin, end
            MATCH path = (begin)-[:r_word*]->(end)
            WITH utt, begin, end, filter(n in nodes(path) where n.time is null) as words
            UNWIND words as w
            MERGE (w)-[:contained_by]->(utt)'''
    statement = statement.format(path = csv_path, corpus = corpus_context.corpus_name,
                                discourse = discourse)
    corpus_context.graph.cypher.execute(statement)

def import_syllable_csv(corpus_context, discourse, base):
    csv_path = 'file:///{}'.format(os.path.join(corpus_context.config.temporary_directory('csv'), '{}_syllable.csv'.format(discourse)).replace('\\','/'))
    statement = '''USING PERIODIC COMMIT 1000
            LOAD CSV FROM "{path}" AS csvLine
            MATCH (begin:Anchor:{corpus}:{discourse} {{time: toFloat(csvLine[0])}}),
            (end:Anchor:{corpus}:{discourse} {{time: toFloat(csvLine[1])}})
            MERGE (begin)-[:r_syllable]->(syl:syllable:{corpus}:{discourse}:speech)-[:r_syllable]->(end)
            MERGE (syl)-[:is_a]->(s_type:syllable_type)
            WITH syl, begin, end
            MATCH path = (begin)-[:r_{base}*]->(end)
            WITH syl, begin, end, filter(n in nodes(path) where n.time is null) as phones
            UNWIND phones as p
            MATCH (p)-[r:contained_by]->(w)
            DELETE r
            WITH p, w, syl
            MERGE (p)-[:contained_by]->(syl)
            MERGE (syl)-[:contained_by]->(w)'''
    statement = statement.format(path = csv_path, corpus = corpus_context.corpus_name,
                                base = base, discourse = discourse)
    corpus_context.graph.cypher.execute(statement)

def data_to_type_csvs(parsed_data, directory):
    type_paths = {}
    data = list(parsed_data.values())[0]
    for x in data.types:
        type_paths[x] = os.path.join(directory,'{}.csv'.format(x))
    tfs = {k: open(v, 'w', encoding = 'utf8') for k,v in type_paths.items()}
    type_writers = {}
    type_headers = {}
    for k,v in tfs.items():
        type_headers[k] = ['label', 'id']
        if data[k].anchor:
            type_headers[k] += data.type_properties
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
    node_path = os.path.join(directory,'{}_nodes.csv'.format(data.name))
    rel_paths = {}
    for x in data.types:
        rel_paths[x] = os.path.join(directory,'{}_r_{}.csv'.format(data.name, x))
    rfs = {k: open(v, 'w', encoding = 'utf8') for k,v in rel_paths.items()}
    rel_writers = {}
    for k,v in rfs.items():
        token_header = ['from_id', 'to_id', 'type_id', 'id']
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
    with open(node_path,'w', encoding = 'utf8') as nf:
        node_writer = csv.DictWriter(nf, ['id','time','corpus','discourse'], delimiter = ',')

        node_writer.writeheader()
        nodes = []
        node_ind = 0
        begin_node = dict(id = uuid1(),
            time = 0, corpus = data.corpus_name, discourse = data.name)
        node_writer.writerow(begin_node)
        base_ind_to_node = {}
        base_levels = data.base_levels
        nodes.append(begin_node)
        for b in base_levels:
            base_ind_to_node[b] = {0: begin_node}
        for i, level in enumerate(data.process_order):
            annotations = []
            for d in data[level]:

                if i == 0: #Anchor level, should have all base levels in it
                    begin_node = nodes[-1]

                    to_align = []
                    endpoints = []
                    if len(base_levels) == 1:

                        b = base_levels[0]
                        begin, end = d[b]
                        base_sequence = data[b][begin:end]
                        for j, seg in enumerate(base_sequence):
                            time = seg.end
                            node_ind += 1
                            node = dict(id = uuid1(),
                                            time = time, corpus = data.corpus_name,
                                            discourse = data.name)
                            node_writer.writerow(node)
                            nodes.append(node)
                            seg_begin_node = -2
                            row = dict(from_id=nodes[seg_begin_node]['id'],
                                                type_id = seg.sha(),
                                                to_id=node['id'], id = seg.id)
                            supertype = data[b].supertype
                            if seg.super_id is not None:
                                row[supertype] = seg.super_id
                            rel_writers[base_levels[0]].writerow(row)
                        end_node = nodes[-1]
                    elif len(base_levels) == 0:
                        node_ind += 1
                        node = dict(id = uuid1(),
                                        time = None, corpus = data.corpus_name,
                                        discourse = data.name)
                        node_writer.writerow(node)
                        nodes.append(node)
                        end_node = nodes[-1]
                else:
                    for b in base_levels:
                        if b in d.references:

                            begin, end = d[b]
                            begin_node = nodes[begin]
                            end_node = nodes[end]
                token_additional = normalize_values_for_neo4j(d.token_properties)
                if d.super_id is not None:
                    token_additional[data[level].supertype] = d.super_id

                if d.label == '':
                    d.label = level
                rel_writers[level].writerow(dict(from_id=begin_node['id'],
                                to_id=end_node['id'], type_id = d.sha(), id = d.id,
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
        type_path = 'file:///{}'.format(os.path.join(corpus_context.config.temporary_directory('csv'), '{}.csv'.format(at)).replace('\\','/'))
        corpus_context.graph.cypher.execute('CREATE CONSTRAINT ON (node:%s_type) ASSERT node.key IS UNIQUE' % at)
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
MERGE (n:{annotation_type}_type {{ label: csvLine.label, key: csvLine.id{type_property_string} }})
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
    node_path = 'file:///{}'.format(os.path.join(corpus_context.config.temporary_directory('csv'), '{}_nodes.csv'.format(name)).replace('\\','/'))

    corpus_context.graph.cypher.execute('CREATE INDEX ON :Anchor(time)')
    corpus_context.graph.cypher.execute('CREATE CONSTRAINT ON (node:Anchor) ASSERT node.id IS UNIQUE')
    node_import_statement = '''LOAD CSV WITH HEADERS FROM "{node_path}" AS csvLine
CREATE (n:Anchor:{corpus_name}:{discourse_name} {{ id: csvLine.id,
time: toFloat(csvLine.time), discourse: '{discourse_name}'}})'''
    kwargs = {'node_path': node_path, 'corpus_name': corpus_context.corpus_name,
                'discourse_name': data.name}
    log.info('Begin loading anchor nodes...')
    begin = time.time()
    corpus_context.graph.cypher.execute(node_import_statement.format(**kwargs))
    log.info('Finished loading anchor nodes!')
    log.debug('Anchor node loading took {} seconds'.format(time.time()-begin))
    prop_temp = '''{name}: csvLine.{name}'''

    for at in annotation_types:
        rel_path = 'file:///{}'.format(os.path.join(corpus_context.config.temporary_directory('csv'), '{}_r_{}.csv'.format(name, at)).replace('\\','/'))

        corpus_context.graph.cypher.execute('CREATE CONSTRAINT ON (node:%s) ASSERT node.id IS UNIQUE' % at)


        properties = []
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
        corpus_context.graph.cypher.execute('CREATE INDEX ON :%s(label)' % at)
        if st is not None:
            corpus_context.graph.cypher.execute('CREATE INDEX ON :%s(%s)' % (at,st))
        rel_import_statement = '''USING PERIODIC COMMIT 3000
LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
MATCH (n:{annotation_type}_type {{key: csvLine.type_id}}),
(begin_node:Anchor:{corpus_name}:{discourse_name} {{ id: csvLine.from_id}}),
(end_node:Anchor:{corpus_name}:{discourse_name} {{ id: csvLine.to_id}})
CREATE (begin_node)-[:r_{annotation_type}]->(t:{annotation_type}:{corpus_name}:{discourse_name}:speech {{id: csvLine.id{token_property_string} }})-[:r_{annotation_type}]->(end_node)
CREATE (t)-[:is_a]->(n)'''
        kwargs = {'path': rel_path, 'annotation_type': at,
                    'token_property_string': token_prop_string,
                    'corpus_name': corpus_context.corpus_name,
                    'discourse_name': data.name}
        statement = rel_import_statement.format(**kwargs)
        log.info('Loading {} relationships...'.format(at))
        begin = time.time()
        corpus_context.graph.cypher.execute(statement)
        log.info('Finished loading {} relationships!'.format(at))
        log.debug('{} relationships loading took: {} seconds.'.format(at, time.time() - begin))
    log.info('Creating containing relationships...')
    begin = time.time()
    for at in annotation_types:
        st = data[at].supertype
        if st is None:
            continue

        statement = '''MATCH (a:{atype}:{corpus}:{discourse_name})
                                WITH a
                                MATCH (s:{stype}:{corpus}:{discourse_name} {{id: a.{stype}}})
                                WITH a, s
                                CREATE (a)-[:contained_by]->(s)'''.format(atype = at,
                                    stype = st, corpus = corpus_context.corpus_name,
                                    discourse_name = data.name)
        corpus_context.graph.cypher.execute(statement)
    log.info('Finished creating containing relationships!')
    log.info('Creating containing relationships took: {}.seconds'.format(time.time() - begin))
    log.info('Finished importing {} into the graph database!'.format(data.name))
    log.debug('Graph importing took: {} seconds'.format(time.time() - initial_begin))
