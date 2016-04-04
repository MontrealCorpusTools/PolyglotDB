
import os
import logging
import time

def import_type_csvs(corpus_context, type_headers):
    log = logging.getLogger('{}_loading'.format(corpus_context.corpus_name))
    prop_temp = '''{name}: csvLine.{name}'''
    for at, h in type_headers.items():
        type_path = 'file:///{}'.format(
                os.path.join(corpus_context.config.temporary_directory('csv'),
                            '{}_type.csv'.format(at)).replace('\\','/'))

        corpus_context.graph.cypher.execute('CREATE CONSTRAINT ON (node:%s_type) ASSERT node.id IS UNIQUE' % at)

        corpus_context.graph.cypher.execute('CREATE INDEX ON :%s_type(label)' % (at,))
        properties = []
        for x in h:
            properties.append(prop_temp.format(name=x))
            if x != 'id':
                corpus_context.graph.cypher.execute('CREATE INDEX ON :%s_type(%s)' % (at, x))
        if properties:
            type_prop_string = ', '.join(properties)
        else:
            type_prop_string = ''
        type_import_statement = '''USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
MERGE (n:{annotation_type}_type:{corpus_name} {{ {type_property_string} }})
        '''
        kwargs = {'path': type_path, 'annotation_type': at,
                    'type_property_string': type_prop_string,
                    'corpus_name': corpus_context.corpus_name}
        statement = type_import_statement.format(**kwargs)
        log.info('Loading {} types...'.format(at))
        begin = time.time()
        corpus_context.execute_cypher(statement)
        log.info('Finished loading {} types!'.format(at))
        log.debug('{} type loading took: {} seconds.'.format(at, time.time() - begin))

def import_csvs(corpus_context, data):
    log = logging.getLogger('{}_loading'.format(corpus_context.corpus_name))
    log.info('Beginning to import {} into the graph database...'.format(data.name))
    initial_begin = time.time()
    name, annotation_types = data.name, data.annotation_types

    prop_temp = '''{name}: csvLine.{name}'''

    directory = corpus_context.config.temporary_directory('csv')
    for at in data.highest_to_lowest():
        rel_path = 'file:///{}'.format(os.path.join(directory, '{}_{}.csv'.format(data.name, at)).replace('\\','/'))

        corpus_context.graph.cypher.execute('CREATE CONSTRAINT ON (node:%s) ASSERT node.id IS UNIQUE' % at)

        properties = []
        corpus_context.execute_cypher('CREATE INDEX ON :%s(discourse)' % (at,))
        corpus_context.execute_cypher('CREATE INDEX ON :%s(begin)' % (at,))
        corpus_context.execute_cypher('CREATE INDEX ON :%s(end)' % (at,))

        for x in data[at].token_property_keys:
            properties.append(prop_temp.format(name=x))
            corpus_context.execute_cypher('CREATE INDEX ON :%s(%s)' % (at, x))
        st = data[at].supertype
        if st is not None:
            properties.append(prop_temp.format(name = st))
        if properties:
            token_prop_string = ', ' + ', '.join(properties)
        else:
            token_prop_string = ''
        if st is not None:
            corpus_context.execute_cypher('CREATE INDEX ON :%s(%s)' % (at,st))
        rel_import_statement = '''USING PERIODIC COMMIT 3000
LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
MATCH (n:{annotation_type}_type {{id: csvLine.type_id}})
CREATE (t:{annotation_type}:{corpus_name}:{discourse}:speech {{id: csvLine.id, begin: toFloat(csvLine.begin),
                            end: toFloat(csvLine.end), discourse: '{discourse}'{token_property_string} }})
CREATE (t)-[:is_a]->(n)
WITH t, csvLine
MERGE (d:Discourse:{corpus_name} {{name: csvLine.discourse}})
CREATE (t)-[:spoken_in]->(d)
WITH t, csvLine
MERGE (s:Speaker:{corpus_name} {{ name: CASE csvLine.speaker WHEN NULL THEN 'unknown' ELSE csvLine.speaker END }})
CREATE (t)-[:spoken_by]->(s)
WITH t, csvLine
MATCH (p:{annotation_type}:{corpus_name}:{discourse}:speech {{id: csvLine.previous_id}})
CREATE (p)-[:precedes]->(t)
'''
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


    for k,v in data.hierarchy.subannotations.items():
        for s in v:
            corpus_context.graph.cypher.execute('CREATE CONSTRAINT ON (node:%s) ASSERT node.id IS UNIQUE' % s)
            path = 'file:///{}'.format(os.path.join(directory,'{}_{}_{}.csv'.format(data.name, k, s)).replace('\\','/'))

            rel_import_statement = '''USING PERIODIC COMMIT 3000
LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
MATCH (n:{annotation_type} {{id: csvLine.annotation_id}})
CREATE (t:{subannotation_type}:{corpus_name}:{discourse}:speech {{id: csvLine.id, begin: toFloat(csvLine.begin),
                            end: toFloat(csvLine.end), label: CASE csvLine.label WHEN NULL THEN '' ELSE csvLine.label END  }})
CREATE (t)-[:annotates]->(n)'''
            kwargs = {'path': path, 'annotation_type': k,
                        'subannotation_type': s,
                        'corpus_name': corpus_context.corpus_name,
                        'discourse': data.name}
            statement = rel_import_statement.format(**kwargs)
            corpus_context.graph.cypher.execute(statement)



def import_lexicon_csvs(corpus_context, typed_data):
    string_set_template = 'n.{name} = csvLine.{name}'
    float_set_template = 'n.{name} = toFloat(csvLine.{name})'
    int_set_template = 'n.{name} = toInt(csvLine.{name})'
    bool_set_template = '''n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)'''
    properties = []
    for h, v in typed_data.items():
        corpus_context.execute_cypher('CREATE INDEX ON :%s(%s)' % (corpus_context.word_name,h))
        if v == int:
            template = int_set_template
        elif v == bool:
            template = bool_set_template
        elif v == float:
            template = float_set_template
        else:
            template = string_set_template
        properties.append(template.format(name = h))
    properties = ',\n'.join(properties)
    directory = corpus_context.config.temporary_directory('csv')
    path = 'file:///{}'.format(os.path.join(directory,'lexicon_import.csv').replace('\\','/'))
    import_statement = '''USING PERIODIC COMMIT 3000
LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
MATCH (n:{word_type}_type:{corpus_name}) where n.label = csvLine.label
SET {new_properties}'''
    statement = import_statement.format(path = path,
                                corpus_name = corpus_context.corpus_name,
                                word_type = corpus_context.word_name,
                                new_properties = properties)
    corpus_context.execute_cypher(statement)

def import_utterance_csv(corpus_context, discourse, transaction = None):
    csv_path = 'file:///{}'.format(os.path.join(corpus_context.config.temporary_directory('csv'), '{}_utterance.csv'.format(discourse)).replace('\\','/'))

    word = getattr(corpus_context, 'word') #FIXME make word more general
    word_type = word.type
    statement = '''LOAD CSV FROM "{path}" AS csvLine
            MATCH (begin:{word_type}:{corpus}:{discourse} {{begin: toFloat(csvLine[0])}})-[:spoken_by]->(s:Speaker:{corpus}),
            (end:{word_type}:{corpus}:{discourse} {{end: toFloat(csvLine[1])}}),
            (d:Discourse:{corpus} {{name: '{discourse}'}})
            CREATE (utt:utterance:{corpus}:{discourse}:speech {{id: csvLine[2], begin: toFloat(csvLine[0]), end: toFloat(csvLine[1])}})-[:is_a]->(u_type:utterance_type),
                (d)<-[:spoken_in]-(utt),
                (s)<-[:spoken_by]-(utt)
            WITH utt, begin, end
            MATCH path = shortestPath((begin)-[:precedes*0..]->(end))
            WITH utt, begin, end, nodes(path) as words
            UNWIND words as w
            MERGE (w)-[:contained_by]->(utt)'''
    statement = statement.format(path = csv_path,
                corpus = corpus_context.corpus_name,
                    discourse = discourse,
                    word_type = word_type)
    if transaction is None:
        corpus_context.execute_cypher(statement)
    else:
        transaction.append(statement)



def import_subannotation_csv(corpus_context, type, annotated_type, props, transaction = None):
    path = os.path.join(corpus_context.config.temporary_directory('csv'),
                        '{}_subannotations.csv'.format(type))
    csv_path = 'file:///{}'.format(path.replace('\\','/'))
    prop_temp = '''{name}: csvLine.{name}'''
    properties = []
    try:
        corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:%s) ASSERT node.id IS UNIQUE' % type)
    except py2neo.cypher.error.schema.ConstraintAlreadyExists:
        pass

    for p in props:
        if p in ['id', 'annotated_id', 'begin', 'end']:
            continue
        corpus_context.execute_cypher('CREATE INDEX ON :%s(%s)' % (type, p))
        properties.append(prop_temp.format(name = p))
    if properties:
        properties = ', ' + ', '.join(properties)
    else:
        properties = ''
    statement = '''USING PERIODIC COMMIT 500
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            MATCH (annotated:{a_type}:{corpus} {{id: csvLine.annotated_id}})
            CREATE (annotated) <-[:annotates]-(annotation:{type}:{corpus}
                {{id: csvLine.id, begin: toFloat(csvLine.begin),
                end: toFloat(csvLine.end){properties}}})
            '''
    statement = statement.format(path = csv_path,
                corpus = corpus_context.corpus_name,
                    a_type = annotated_type,
                    type = type,
                    properties = properties)
    if transaction is None:
        corpus_context.execute_cypher(statement)
    else:
        transaction.append(statement)
