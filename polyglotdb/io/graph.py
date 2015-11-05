import csv
import os
from uuid import uuid1
import logging
import time

from .helper import normalize_values_for_neo4j

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
    type_paths = {}
    for x in data.types:
        rel_paths[x] = os.path.join(directory,'{}_r_{}.csv'.format(data.name, x))
        type_paths[x] = os.path.join(directory,'{}_{}.csv'.format(data.name, x))
    rfs = {k: open(v, 'w') for k,v in rel_paths.items()}
    tfs = {k: open(v, 'w') for k,v in type_paths.items()}
    rel_writers = {}
    type_writers = {}
    for k,v in rfs.items():
        token_header = ['from_id', 'to_id', 'type_id', 'id']
        type_header = ['label', 'id']
        if k == 'word':
            token_header += data.token_properties
            type_header += data.type_properties
            supertype = data[data.word_levels[0]].supertype
            if supertype is not None:
                token_header.append(supertype)
        else:
            supertype = data[k].supertype
            if supertype is not None:
                token_header.append(supertype)
        rel_writers[k] = csv.DictWriter(v, token_header, delimiter = ',')
        type_writers[k] = csv.DictWriter(tfs[k], type_header, delimiter = ',')
    for x in rel_writers.values():
        x.writeheader()
    for x in type_writers.values():
        x.writeheader()
    with open(node_path,'w') as nf:
        node_writer = csv.DictWriter(nf, ['id','label','time','corpus','discourse'], delimiter = ',')

        node_writer.writeheader()
        nodes = []
        node_ind = 0
        begin_node = dict(id = node_ind, label = uuid1(),
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
                            node = dict(id = node_ind, label = uuid1(),
                                            time = time, corpus = data.corpus_name,
                                            discourse = data.name)
                            node_writer.writerow(node)
                            nodes.append(node)
                            seg_begin_node = -2
                            type_row = dict(label=seg.label, id = hash(seg))
                            row = dict(from_id=nodes[seg_begin_node]['id'],
                                                type_id = hash(seg),
                                                to_id=node['id'], id = seg.id)
                            supertype = data[b].supertype
                            if seg.super_id is not None:
                                row[supertype] = seg.super_id
                            rel_writers[base_levels[0]].writerow(row)
                            type_writers[base_levels[0]].writerow(type_row)
                        end_node = nodes[-1]
                    elif len(base_levels) == 0:
                        node_ind += 1
                        node = dict(id = node_ind, label = uuid1(),
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
                type_additional = normalize_values_for_neo4j(d.type_properties)
                if d.super_id is not None:
                    token_additional[data[level].supertype] = d.super_id

                if d.label == '':
                    d.label = level
                type_writers[level].writerow(dict(label=d.label, id = hash(d),
                                **type_additional))
                rel_writers[level].writerow(dict(from_id=begin_node['id'],
                                to_id=end_node['id'], type_id = hash(d), id = d.id,
                                **token_additional))
    for x in rfs.values():
        x.close()
    for x in tfs.values():
        x.close()

def import_csvs(corpus_context, data):
        log = logging.getLogger('{}_loading'.format(corpus_context.corpus_name))
        log.info('Beginning to import {} into the graph database...'.format(data.name))
        initial_begin = time.time()
        name, annotation_types = data.name, data.output_types
        token_properties = data.token_properties
        type_properties = data.type_properties
        node_path = 'file:///{}'.format(os.path.join(corpus_context.config.temp_dir, '{}_nodes.csv'.format(name)).replace('\\','/'))

        corpus_context.graph.cypher.execute('CREATE INDEX ON :Anchor(time)')
        corpus_context.graph.cypher.execute('CREATE CONSTRAINT ON (node:Anchor) ASSERT node.id IS UNIQUE')
        node_import_statement = '''LOAD CSV WITH HEADERS FROM "{node_path}" AS csvLine
CREATE (n:Anchor:{corpus_name}:{discourse_name} {{ id: toInt(csvLine.id), label: csvLine.label,
time: toFloat(csvLine.time)}})'''
        kwargs = {'node_path': node_path, 'corpus_name': corpus_context.corpus_name,
                    'discourse_name': data.name}
        log.info('Begin loading anchor nodes...')
        begin = time.time()
        corpus_context.graph.cypher.execute(node_import_statement.format(**kwargs))
        log.info('Finished loading anchor nodes!')
        log.debug('Anchor node loading took {} seconds'.format(time.time()-begin))
        prop_temp = '''{name}: csvLine.{name}'''

        for at in annotation_types:
            rel_path = 'file:///{}'.format(os.path.join(corpus_context.config.temp_dir, '{}_r_{}.csv'.format(name, at)).replace('\\','/'))
            type_path = 'file:///{}'.format(os.path.join(corpus_context.config.temp_dir, '{}_{}.csv'.format(name, at)).replace('\\','/'))

            corpus_context.graph.cypher.execute('CREATE CONSTRAINT ON (node:%s) ASSERT node.id IS UNIQUE' % at)

            properties = []
            corpus_context.graph.cypher.execute('CREATE CONSTRAINT ON (node:%s_type) ASSERT node.id IS UNIQUE' % at)
            if at == 'word':
                for x in type_properties:
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
            corpus_context.graph.cypher.execute('CREATE INDEX ON :r_%s(label)' % at)
            if st is not None:
                corpus_context.graph.cypher.execute('CREATE INDEX ON :%s(%s)' % (at,st))
            rel_import_statement = '''USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
MATCH (n:{annotation_type}_type {{id: csvLine.type_id}}),
    (begin_node:Anchor:{corpus_name}:{discourse_name} {{ id: toInt(csvLine.from_id)}}),
    (end_node:Anchor:{corpus_name}:{discourse_name} {{ id: toInt(csvLine.to_id)}})
CREATE (begin_node)-[:r_{annotation_type}]->(t:{annotation_type}:{corpus_name}:{discourse_name} {{id: csvLine.id, discourse: '{discourse_name}'{token_property_string} }})-[:r_{annotation_type}]->(end_node)
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
        log.info('Cleaning up...')
        corpus_context.graph.cypher.execute('DROP CONSTRAINT ON (node:Anchor) ASSERT node.id IS UNIQUE')
        corpus_context.graph.cypher.execute('''MATCH (n)
                                    WHERE n:Anchor
                                    REMOVE n.id''')
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
        log.info('Finished importing {} into the graph database!'.format(data.name))
        log.debug('Graph importing took: {} seconds'.format(time.time() - initial_begin))
