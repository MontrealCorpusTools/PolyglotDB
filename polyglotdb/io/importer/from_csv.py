
import os
import logging
import time

def import_type_csvs(corpus_context, type_headers):
    log = logging.getLogger('{}_loading'.format(corpus_context.corpus_name))
    prop_temp = '''{name}: csvLine.{name}'''
    for at, h in type_headers.items():
        path = os.path.join(corpus_context.config.temporary_directory('csv'),
                            '{}_type.csv'.format(at))
        type_path = 'file:///{}'.format(path.replace('\\','/'))

        corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:%s_type) ASSERT node.id IS UNIQUE' % at)

        corpus_context.execute_cypher('CREATE INDEX ON :%s_type(label)' % (at,))
        properties = []
        for x in h:
            properties.append(prop_temp.format(name=x))
            if x != 'id':
                corpus_context.execute_cypher('CREATE INDEX ON :%s_type(%s)' % (at, x))
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
        #os.remove(path) # FIXME Neo4j 2.3 does not release files

def import_csvs(corpus_context, data):
    log = logging.getLogger('{}_loading'.format(corpus_context.corpus_name))
    log.info('Beginning to import {} into the graph database...'.format(data.name))
    initial_begin = time.time()
    name, annotation_types = data.name, data.annotation_types

    prop_temp = '''{name}: csvLine.{name}'''

    directory = corpus_context.config.temporary_directory('csv')
    for at in data.highest_to_lowest():
        path = os.path.join(directory, '{}_{}.csv'.format(data.name, at))
        rel_path = 'file:///{}'.format(path.replace('\\','/'))

        corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:%s) ASSERT node.id IS UNIQUE' % at)

        properties = []
        corpus_context.execute_cypher('CREATE INDEX ON :%s(begin)' % (at,))
        corpus_context.execute_cypher('CREATE INDEX ON :%s(end)' % (at,))

        for x in data[at].token_property_keys:
            properties.append(prop_temp.format(name=x))
            corpus_context.execute_cypher('CREATE INDEX ON :%s(%s)' % (at, x))
        st = data[at].supertype
        if properties:
            token_prop_string = ', ' + ', '.join(properties)
        else:
            token_prop_string = ''
        if st is not None:
            rel_import_statement = '''USING PERIODIC COMMIT 3000
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    MATCH (n:{annotation_type}_type {{id: csvLine.type_id}}), (super:{stype}:{corpus_name} {{id: csvLine.{stype}}})
    CREATE (t:{annotation_type}:{corpus_name}:speech {{id: csvLine.id, begin: toFloat(csvLine.begin),
                                end: toFloat(csvLine.end){token_property_string} }})
    CREATE (t)-[:is_a]->(n)
    CREATE (t)-[:contained_by]->(super)
    WITH t, csvLine

    MERGE (d:Discourse:{corpus_name} {{name: {{discourse}}}})
    CREATE (t)-[:spoken_in]->(d)
    WITH t, csvLine
    MERGE (s:Speaker:{corpus_name} {{ name: CASE csvLine.speaker WHEN NULL THEN 'unknown' ELSE csvLine.speaker END }})
    CREATE (t)-[:spoken_by]->(s)
    WITH t, csvLine
    MATCH (p:{annotation_type}:{corpus_name}:speech {{id: csvLine.previous_id}})
    CREATE (p)-[:precedes]->(t)
    '''
            kwargs = {'path': rel_path, 'annotation_type': at,
                        'token_property_string': token_prop_string,
                        'corpus_name': corpus_context.corpus_name,
                        'discourse': data.name,
                        'stype':st}
        else:

            rel_import_statement = '''USING PERIODIC COMMIT 3000
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    MATCH (n:{annotation_type}_type {{id: csvLine.type_id}})
    CREATE (t:{annotation_type}:{corpus_name}:speech {{id: csvLine.id, begin: toFloat(csvLine.begin),
                                end: toFloat(csvLine.end){token_property_string} }})
    CREATE (t)-[:is_a]->(n)
    WITH t, csvLine
    MERGE (d:Discourse:{corpus_name} {{name: {{discourse}}}})
    CREATE (t)-[:spoken_in]->(d)
    WITH t, csvLine
    MERGE (s:Speaker:{corpus_name} {{ name: CASE csvLine.speaker WHEN NULL THEN 'unknown' ELSE csvLine.speaker END }})
    CREATE (t)-[:spoken_by]->(s)
    WITH t, csvLine
    MATCH (p:{annotation_type}:{corpus_name}:speech {{id: csvLine.previous_id}})
    CREATE (p)-[:precedes]->(t)
    '''
            kwargs = {'path': rel_path, 'annotation_type': at,
                        'token_property_string': token_prop_string,
                        'corpus_name': corpus_context.corpus_name}
        statement = rel_import_statement.format(**kwargs)
        log.info('Loading {} relationships...'.format(at))
        begin = time.time()
        corpus_context.execute_cypher(statement, discourse = data.name)
        log.info('Finished loading {} relationships!'.format(at))
        log.debug('{} relationships loading took: {} seconds.'.format(at, time.time() - begin))
        #os.remove(path) # FIXME Neo4j 2.3 does not release files

    log.info('Finished importing {} into the graph database!'.format(data.name))
    log.debug('Graph importing took: {} seconds'.format(time.time() - initial_begin))


    for k,v in data.hierarchy.subannotations.items():
        for s in v:
            path = os.path.join(directory,'{}_{}_{}.csv'.format(data.name, k, s))
            corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:%s) ASSERT node.id IS UNIQUE' % s)
            sub_path = 'file:///{}'.format(path.replace('\\','/'))

            rel_import_statement = '''USING PERIODIC COMMIT 3000
LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
MATCH (n:{annotation_type} {{id: csvLine.annotation_id}})
CREATE (t:{subannotation_type}:{corpus_name}:speech {{id: csvLine.id, begin: toFloat(csvLine.begin),
                            end: toFloat(csvLine.end), label: CASE csvLine.label WHEN NULL THEN '' ELSE csvLine.label END  }})
CREATE (t)-[:annotates]->(n)'''
            kwargs = {'path': sub_path, 'annotation_type': k,
                        'subannotation_type': s,
                        'corpus_name': corpus_context.corpus_name,
                        'discourse': data.name}
            statement = rel_import_statement.format(**kwargs)
            corpus_context.execute_cypher(statement)
            #os.remove(path) # FIXME Neo4j 2.3 does not release files


def import_lexicon_csvs(corpus_context, typed_data, case_sensitive = False):
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
    path = os.path.join(directory,'lexicon_import.csv')
    lex_path = 'file:///{}'.format(path.replace('\\','/'))
    if case_sensitive:
        import_statement = '''USING PERIODIC COMMIT 3000
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    with csvLine
    MATCH (n:{word_type}_type:{corpus_name}) where n.label = csvLine.label
    SET {new_properties}'''
    else:
        import_statement = '''USING PERIODIC COMMIT 3000
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    with csvLine
    MATCH (n:{word_type}_type:{corpus_name}) where n.label =~ toString(csvLine.label)
    SET {new_properties}'''

    statement = import_statement.format(path = lex_path,
                                corpus_name = corpus_context.corpus_name,
                                word_type = corpus_context.word_name,
                                new_properties = properties)
    corpus_context.execute_cypher(statement)
    #os.remove(path) # FIXME Neo4j 2.3 does not release files


def import_feature_csvs(corpus_context, typed_data):
    string_set_template = 'n.{name} = csvLine.{name}'
    float_set_template = 'n.{name} = toFloat(csvLine.{name})'
    int_set_template = 'n.{name} = toInt(csvLine.{name})'
    bool_set_template = '''n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)'''
    properties = []
    for h, v in typed_data.items():
        corpus_context.execute_cypher('CREATE INDEX ON :%s(%s)' % (corpus_context.phone_name,h))
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
    path = os.path.join(directory,'feature_import.csv')
    feat_path = 'file:///{}'.format(path.replace('\\','/'))
    import_statement = '''
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    MATCH (n:{phone_type}_type:{corpus_name}) where n.label = csvLine.label
    SET {new_properties}'''

    statement = import_statement.format(path = feat_path,
                                corpus_name = corpus_context.corpus_name,
                                phone_type = corpus_context.phone_name,
                                new_properties = properties)
    corpus_context.execute_cypher(statement)
    #os.remove(path) # FIXME Neo4j 2.3 does not release files

def import_speaker_csvs(corpus_context, typed_data):
    string_set_template = 'n.{name} = csvLine.{name}'
    float_set_template = 'n.{name} = toFloat(csvLine.{name})'
    int_set_template = 'n.{name} = toInt(csvLine.{name})'
    bool_set_template = '''n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)'''
    properties = []
    for h, v in typed_data.items():
        corpus_context.execute_cypher('CREATE INDEX ON :Speaker(%s)' % h)
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
    path = os.path.join(directory,'speaker_import.csv')
    feat_path = 'file:///{}'.format(path.replace('\\','/'))
    import_statement = '''
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    MATCH (n:Speaker:{corpus_name}) where n.name = csvLine.name
    SET {new_properties}'''

    statement = import_statement.format(path = feat_path,
                                corpus_name = corpus_context.corpus_name,
                                new_properties = properties)
    corpus_context.execute_cypher(statement)
    #os.remove(path) # FIXME Neo4j 2.3 does not release files

def import_discourse_csvs(corpus_context, typed_data):
    string_set_template = 'n.{name} = csvLine.{name}'
    float_set_template = 'n.{name} = toFloat(csvLine.{name})'
    int_set_template = 'n.{name} = toInt(csvLine.{name})'
    bool_set_template = '''n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)'''
    properties = []
    for h, v in typed_data.items():
        corpus_context.execute_cypher('CREATE INDEX ON :Discourse(%s)' % h)
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
    path = os.path.join(directory,'discourse_import.csv')
    feat_path = 'file:///{}'.format(path.replace('\\','/'))
    import_statement = '''
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    MATCH (n:Discourse:{corpus_name}) where n.name = csvLine.name
    SET {new_properties}'''

    statement = import_statement.format(path = feat_path,
                                corpus_name = corpus_context.corpus_name,
                                new_properties = properties)
    corpus_context.execute_cypher(statement)
    #os.remove(path) # FIXME Neo4j 2.3 does not release files

def import_utterance_csv(corpus_context, discourse):
    path = os.path.join(corpus_context.config.temporary_directory('csv'), '{}_utterance.csv'.format(discourse))
    csv_path = 'file:///{}'.format(path.replace('\\','/'))

    corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:utterance) ASSERT node.id IS UNIQUE')
    corpus_context.execute_cypher('CREATE INDEX ON :utterance(begin)')
    corpus_context.execute_cypher('CREATE INDEX ON :utterance(end)')
    statement = '''LOAD CSV FROM "{path}" AS csvLine
            MATCH (d:Discourse:{corpus})<-[:spoken_in]-(begin:{word_type}:{corpus}:speech {{id: csvLine[0]}})-[:spoken_by]->(s:Speaker:{corpus})
            WHERE d.name = {{discourse}}
            OPTIONAL MATCH (d)<-[:spoken_in]-(end:{word_type}:{corpus}:speech {{id: csvLine[1]}})
            CREATE (utt:utterance:{corpus}:speech {{id: csvLine[2], begin: begin.begin, end: end.end}})-[:is_a]->(u_type:utterance_type:{corpus}),
                (d)<-[:spoken_in]-(utt),
                (s)<-[:spoken_by]-(utt)
            WITH utt, begin, end
            MATCH path = shortestPath((begin)-[:precedes*0..]->(end))
            WITH utt, begin, end, nodes(path) as words
            UNWIND words as w
            CREATE (w)-[:contained_by]->(utt)'''
    statement = statement.format(path = csv_path,
                corpus = corpus_context.corpus_name,
                    word_type = corpus_context.word_name)
    corpus_context.execute_cypher(statement, discourse = discourse)
    #os.remove(path) # FIXME Neo4j 2.3 does not release files

def import_syllable_csv(corpus_context, split_name):
    path = os.path.join(corpus_context.config.temporary_directory('csv'),
                        '{}_syllable.csv'.format(split_name))
    csv_path = 'file:///{}'.format(path.replace('\\','/'))

    corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:syllable) ASSERT node.id IS UNIQUE')
    corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:syllable_type) ASSERT node.id IS UNIQUE')

    corpus_context.execute_cypher('CREATE INDEX ON :syllable(begin)')
    corpus_context.execute_cypher('CREATE INDEX ON :syllable(prev_id)')
    corpus_context.execute_cypher('CREATE INDEX ON :syllable(end)')
    corpus_context.execute_cypher('CREATE INDEX ON :syllable(label)')
    corpus_context.execute_cypher('CREATE INDEX ON :syllable_type(label)')

    statement = '''USING PERIODIC COMMIT 500
    LOAD CSV WITH HEADERS FROM "{path}" as csvLine
    MERGE (s_type:syllable_type:{corpus} {{id: csvLine.type_id}})
    ON CREATE SET s_type.label = csvLine.label
    WITH s_type, csvLine
    MATCH (n:{phone_name}:{corpus}:speech {{id: csvLine.vowel_id}})-[r:contained_by]->(w:{word_name}:{corpus}:speech),
            (n)-[:spoken_by]->(sp:Speaker),
            (n)-[:spoken_in]->(d:Discourse)
    WITH n, w, csvLine, sp, d, r,s_type
    SET n :nucleus, n.syllable_position = 'nucleus'
    WITH n, w, csvLine, sp, d, r,s_type
    DELETE r
    WITH n, w, csvLine, sp, d,s_type
    CREATE (s:syllable:{corpus}:speech {{id: csvLine.id, prev_id:csvLine.prev_id,
                        label: csvLine.label,
                        begin: toFloat(csvLine.begin), end: toFloat(csvLine.end)}}),
            (s)-[:is_a]->(s_type),
            (s)-[:contained_by]->(w),
            (n)-[:contained_by]->(s),
            (s)-[:spoken_by]->(sp),
            (s)-[:spoken_in]->(d)
    with n, w, csvLine, s
    OPTIONAL MATCH (prev:syllable {{id:csvLine.prev_id}})
    FOREACH (o IN CASE WHEN prev IS NOT NULL THEN [prev] ELSE [] END |
      CREATE (o)-[:precedes]->(s)
    )
    with n, w, csvLine, s
    OPTIONAL MATCH
            (onset:{phone_name}:{corpus} {{id: csvLine.onset_id}}),
            onspath = (onset)-[:precedes*1..10]->(n)

    with n, w,s, csvLine, onspath
    UNWIND (case when onspath is not null then nodes(onspath)[0..-1] else [null] end) as o

    OPTIONAL MATCH (o)-[r:contained_by]->(w)
    with n, w,s, csvLine, filter(x in collect(o) WHERE x is not NULL) as ons,
    filter(x in collect(r) WHERE x is not NULL) as rels
    FOREACH (o in ons | SET o :onset, o.syllable_position = 'onset')
    FOREACH (o in ons | CREATE (o)-[:contained_by]->(s))
    FOREACH (r in rels | DELETE r)
    with distinct n, w, s, csvLine
    Optional match
            (coda:{phone_name}:{corpus} {{id: csvLine.coda_id}}),
        codapath = (n)-[:precedes*1..10]->(coda)
    with n, w, s, codapath
    UNWIND (case when codapath is not null then nodes(codapath)[1..] else [null] end) as c

    OPTIONAL MATCH (c)-[r:contained_by]->(w)
    with n, w,s, filter(x in collect(c) WHERE x is not NULL) as cod,
    filter(x in collect(r) WHERE x is not NULL) as rels
    FOREACH (c in cod | SET c :coda, c.syllable_position = 'coda')
    FOREACH (c in cod | CREATE (c)-[:contained_by]->(s))
    FOREACH (r in rels | DELETE r)'''

    statement = statement.format(path = csv_path,
                corpus = corpus_context.corpus_name,
                word_name = corpus_context.word_name,
                    phone_name = corpus_context.phone_name,
                    discourse = split_name)
    corpus_context.execute_cypher(statement)

def import_nonsyl_csv(corpus_context, split_name):
    path = os.path.join(corpus_context.config.temporary_directory('csv'),
                        '{}_nonsyl.csv'.format(split_name))
    csv_path = 'file:///{}'.format(path.replace('\\','/'))

    corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:syllable) ASSERT node.id IS UNIQUE')
    corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:syllable_type) ASSERT node.id IS UNIQUE')

    corpus_context.execute_cypher('CREATE INDEX ON :syllable(begin)')
    corpus_context.execute_cypher('CREATE INDEX ON :syllable(prev_id)')
    corpus_context.execute_cypher('CREATE INDEX ON :syllable(end)')
    corpus_context.execute_cypher('CREATE INDEX ON :syllable(label)')
    corpus_context.execute_cypher('CREATE INDEX ON :syllable_type(label)')

    statement = '''USING PERIODIC COMMIT 500
    LOAD CSV WITH HEADERS FROM "{path}" as csvLine
    MERGE (s_type:syllable_type:{corpus} {{id: csvLine.type_id}})
    ON CREATE SET s_type.label = csvLine.label
    WITH s_type, csvLine
MATCH (o:{phone_name}:{corpus}:speech {{id: csvLine.onset_id}})-[r:contained_by]->(w:{word_name}:{corpus}:speech),
            (o)-[:spoken_by]->(sp:Speaker),
            (o)-[:spoken_in]->(d:Discourse)
WITH o, w, csvLine, sp, d, r, s_type
DELETE r
WITH o, w, csvLine, sp, d, s_type
CREATE (s:syllable:{corpus}:speech {{id: csvLine.id,
                                begin: toFloat(csvLine.begin), end: toFloat(csvLine.end),
                                label: csvLine.label}}),
        (s)-[:is_a]->(s_type),
        (s)-[:contained_by]->(w),
        (s)-[:spoken_by]->(sp),
        (s)-[:spoken_in]->(d)
with o, w, csvLine, s
    OPTIONAL MATCH (prev:syllable {{id:csvLine.prev_id}})
    FOREACH (pv IN CASE WHEN prev IS NOT NULL THEN [prev] ELSE [] END |
      CREATE (pv)-[:precedes]->(s)
    )
with o, w, csvLine, s
    OPTIONAL MATCH (foll:syllable {{prev_id:csvLine.id}})
    FOREACH (fv IN CASE WHEN foll IS NOT NULL THEN [foll] ELSE [] END |
      CREATE (s)-[:precedes]->(fv)
    )
with o, w, csvLine, s
OPTIONAL MATCH
(c:{phone_name}:{corpus}:speech {{id: csvLine.coda_id}})-[:contained_by]->(w),
p = (o)-[:precedes*..10]->(c)
with o, w, s, p, csvLine
    UNWIND (case when p is not null then nodes(p) else [o] end) as c

    OPTIONAL MATCH (c)-[r:contained_by]->(w)
    with w,s, toInt(csvLine.break) as break, filter(x in collect(c) WHERE x is not NULL) as cod,
    filter(x in collect(r) WHERE x is not NULL) as rels
    FOREACH (c in cod[break..] | SET c :coda, c.syllable_position = 'coda')
    FOREACH (c in cod[..break] | SET c :onset, c.syllable_position = 'onset')
    FOREACH (c in cod | CREATE (c)-[:contained_by]->(s))
    FOREACH (r in rels | DELETE r)'''

    statement = statement.format(path = csv_path,
                corpus = corpus_context.corpus_name,
                word_name = corpus_context.word_name,
                    phone_name = corpus_context.phone_name,
                    discourse = split_name
                )
    corpus_context.execute_cypher(statement)

def import_subannotation_csv(corpus_context, type, annotated_type, props):
    path = os.path.join(corpus_context.config.temporary_directory('csv'),
                        '{}_subannotations.csv'.format(type))
    csv_path = 'file:///{}'.format(path.replace('\\','/'))
    prop_temp = '''{name}: csvLine.{name}'''
    properties = []

    corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:%s) ASSERT node.id IS UNIQUE' % type)


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
    corpus_context.execute_cypher(statement)
    #os.remove(path) # FIXME Neo4j 2.3 does not release files
