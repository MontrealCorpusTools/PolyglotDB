import os
import logging
import time
import neo4j
import re

def make_path_safe(path):
    '''Takes a path and returns it with the associated Javascript URL-safe characters'''
    replacements = [('%', '%25'), ('\\', '/'), (' ', '%20'), ("'", "\\'"), ('?', '%3F'), (';', '%3B'),
                    ('<', '%3C'), ('=', '%3D'), ('>', '%3E'), (':', '%3A'), ('*', '%2A'), ('&', '%26'),
                    ('(', '%28'), (')', '%29'), ('@', '%40'), ('!', '%21'), ('#', '%23')]
    for o, r in replacements:
        path = path.replace(o, r)
    return path


def import_type_csvs(corpus_context, type_headers):
    """
    Imports types into corpus from csv files

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.ImportContext`
        the corpus to import into
    type_headers : list
        a list of type files
    """
    log = logging.getLogger('{}_loading'.format(corpus_context.corpus_name))
    prop_temp = '''{name}: csvLine.{name}'''
    for at, h in type_headers.items():
        path = os.path.join(corpus_context.config.temporary_directory('csv'),
                            '{}_type.csv'.format(at))
        # If on the Docker version, the files live in /site/proj
        if os.path.exists('/site/proj') and not path.startswith('/site/proj'):
            type_path = 'file:///site/proj/{}'.format(make_path_safe(path))
        else:
            type_path = 'file:///{}'.format(make_path_safe(path))

        try:
            corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:%s_type) ASSERT node.id IS UNIQUE' % at)
        except neo4j.exceptions.ClientError as e:
            if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                raise

        properties = []
        for x in h:
            properties.append(prop_temp.format(name=x))
        if 'label' in h:
            properties.append('label_insensitive: toLower(csvLine.label)')
            try:
                corpus_context.execute_cypher('CREATE INDEX ON :%s_type(label_insensitive)' % at)
            except neo4j.exceptions.ClientError as e:
                if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                    raise
        for x in h:
            if x != 'id':
                try:
                    corpus_context.execute_cypher('CREATE INDEX ON :%s_type(%s)' % (at, x))
                except neo4j.exceptions.ClientError as e:
                    if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                        raise
        if properties:
            type_prop_string = ', '.join(properties)
        else:
            type_prop_string = ''
        type_import_statement = '''USING PERIODIC COMMIT 2000
LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
MERGE (n:{annotation_type}_type:{corpus_name} {{ {type_property_string} }})
        '''
        kwargs = {'path': type_path, 'annotation_type': at,
                  'type_property_string': type_prop_string,
                  'corpus_name': corpus_context.cypher_safe_name}
        statement = type_import_statement.format(**kwargs)
        log.info('Loading {} types...'.format(at))
        begin = time.time()
        try:
            corpus_context.execute_cypher(statement)
        except:
            raise
        finally:
            #    with open(path, 'w'):
            #        pass
            os.remove(path)

        log.info('Finished loading {} types!'.format(at))
        log.debug('{} type loading took: {} seconds.'.format(at, time.time() - begin))


def import_csvs(corpus_context, speakers, token_headers, hierarchy, call_back=None, stop_check=None):
    """
    Loads data from a csv file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.importable.ImportContext`
        the corpus to load into
    data_list : :class:`~polyglotdb.io.helper.DiscourseData` or list
        DiscourseData object or list of DiscourseData objects to import
    call_back : callable or None
        Function to report progress
    stop_check : callable or None
        Function to check whether to terminate early
    """
    log = logging.getLogger('{}_loading'.format(corpus_context.corpus_name))
    log.info('Beginning to import data into the graph database...')
    initial_begin = time.time()

    prop_temp = '''{name}: csvLine.{name}'''

    directory = corpus_context.config.temporary_directory('csv')
    annotation_types = hierarchy.highest_to_lowest
    if call_back is not None:
        call_back('Importing data...')
        call_back(0, len(speakers) * len(annotation_types))
        cur = 0
    statements = []

    def _unique_function(tx, at):
        tx.run('CREATE CONSTRAINT ON (node:%s) ASSERT node.id IS UNIQUE' % at)

    def _prop_index(tx, at, prop):
        tx.run('CREATE INDEX ON :%s(%s)' % (at, prop))

    def _label_index(tx, at):
        tx.run('CREATE INDEX ON :%s(label_insensitive)' % at)

    def _begin_index(tx, at):
        tx.run('CREATE INDEX ON :%s(begin)' % (at,))

    def _end_index(tx, at):
        tx.run('CREATE INDEX ON :%s(end)' % (at,))

    with corpus_context.graph_driver.session() as session:
        for i, s in enumerate(speakers):
            speaker_statements = []
            for at in annotation_types:
                if stop_check is not None and stop_check():
                    return
                if call_back is not None:
                    call_back(cur)
                    cur += 1
                path = os.path.join(directory, '{}_{}.csv'.format(re.sub(r'\W', '_', s), at))
                if not os.path.exists(path):  # Already imported
                    continue
                # If on the Docker version, the files live in /site/proj
                if os.path.exists('/site/proj') and not path.startswith('/site/proj'):
                    rel_path = 'file:///site/proj/{}'.format(make_path_safe(path))
                else:
                    rel_path = 'file:///{}'.format(make_path_safe(path))
                try:
                    session.write_transaction(_unique_function, at)
                except neo4j.exceptions.ClientError as e:
                    if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                        raise

                properties = []

                for x in token_headers[at]:
                    if x in ['type_id', 'id', 'previous_id', 'speaker', 'discourse', 'begin', 'end']:
                        continue
                    properties.append(prop_temp.format(name=x))
                    try:
                        session.write_transaction(_prop_index, at, x)
                    except neo4j.exceptions.ClientError as e:
                        if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                            raise
                if 'label' in token_headers[at]:
                    properties.append('label_insensitive: toLower(csvLine.label)')
                    try:
                        session.write_transaction(_label_index, at)
                    except neo4j.exceptions.ClientError as e:
                        if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                            raise
                st = hierarchy[at]
                if properties:
                    token_prop_string = ', ' + ', '.join(properties)
                else:
                    token_prop_string = ''
                node_import_statement = '''USING PERIODIC COMMIT 2000
                LOAD CSV WITH HEADERS FROM '{path}' AS csvLine
                CREATE (t:{annotation_type}:{corpus_name}:speech {{id: csvLine.id, begin: toFloat(csvLine.begin),
                                            end: toFloat(csvLine.end){token_property_string} }})
                '''
                node_kwargs = {'path': rel_path, 'annotation_type': at,
                               'token_property_string': token_prop_string,
                               'corpus_name': corpus_context.cypher_safe_name}
                if st is not None:
                    rel_import_statement = '''USING PERIODIC COMMIT 2000
                    LOAD CSV WITH HEADERS FROM '{path}' AS csvLine
                    MATCH (n:{annotation_type}_type:{corpus_name} {{id: csvLine.type_id}}), (super:{stype}:{corpus_name} {{id: csvLine.{stype}}}),
                    (d:Discourse:{corpus_name} {{name: csvLine.discourse}}),
                    (s:Speaker:{corpus_name} {{name: csvLine.speaker}}),
                    (t:{annotation_type}:{corpus_name}:speech {{id: csvLine.id}})
                    CREATE (t)-[:is_a]->(n),
                        (t)-[:contained_by]->(super),
                        (t)-[:spoken_in]->(d),
                        (t)-[:spoken_by]->(s)
                    WITH t, csvLine
                    MATCH (p:{annotation_type}:{corpus_name}:speech {{id: csvLine.previous_id}})
                        CREATE (p)-[:precedes]->(t)
                    '''
                    rel_kwargs = {'path': rel_path, 'annotation_type': at,
                                  'corpus_name': corpus_context.cypher_safe_name,
                                  'stype': st}
                else:

                    rel_import_statement = '''USING PERIODIC COMMIT 2000
                LOAD CSV WITH HEADERS FROM '{path}' AS csvLine
                MATCH (n:{annotation_type}_type:{corpus_name} {{id: csvLine.type_id}}),
                (d:Discourse:{corpus_name} {{name: csvLine.discourse}}),
                (s:Speaker:{corpus_name} {{ name: csvLine.speaker}}),
                        (t:{annotation_type}:{corpus_name}:speech {{id: csvLine.id}})
                CREATE (t)-[:is_a]->(n),
                        (t)-[:spoken_in]->(d),
                        (t)-[:spoken_by]->(s)
                    WITH t, csvLine
                    MATCH (p:{annotation_type}:{corpus_name}:speech {{id: csvLine.previous_id}})
                        CREATE (p)-[:precedes]->(t)
                '''
                    rel_kwargs = {'path': rel_path, 'annotation_type': at,
                                  'corpus_name': corpus_context.cypher_safe_name}
                node_statement = node_import_statement.format(**node_kwargs)
                rel_statement = rel_import_statement.format(**rel_kwargs)
                speaker_statements.append((node_statement, rel_statement, path, at, s))
                begin = time.time()
                try:
                    session.write_transaction(_begin_index, at)
                except neo4j.exceptions.ClientError as e:
                    if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                        raise
                try:
                    session.write_transaction(_end_index, at)
                except neo4j.exceptions.ClientError as e:
                    if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                        raise
            statements.append(speaker_statements)

    for i, speaker_statements in enumerate(statements):
        if call_back is not None:
            call_back('Importing data for speaker {} of {} ({})...'.format(i, len(statements), speaker_statements[0][4]))
        for s in speaker_statements:
            log.info('Loading {} relationships...'.format(s[3]))
            try:
                corpus_context.execute_cypher(s[0])
                corpus_context.execute_cypher(s[1])
            except:
                raise
            finally:
                # with open(path, 'w'):
                #    pass
                os.remove(s[2])
            log.info('Finished loading {} relationships for speaker {}!'.format(s[3], s[4]))
            log.debug('{} relationships loading took: {} seconds.'.format(s[3], time.time() - begin))

    log.info('Finished importing into the graph database!')
    log.debug('Graph importing took: {} seconds'.format(time.time() - initial_begin))

    for sp in speakers:
        for k, v in hierarchy.subannotations.items():
            for s in v:
                path = os.path.join(directory, '{}_{}_{}.csv'.format(re.sub(r'\W', '_', sp), k, s))
                try:
                    corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:%s) ASSERT node.id IS UNIQUE' % s)
                except neo4j.exceptions.ClientError as e:
                    if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                        raise
                # If on the Docker version, the files live in /site/proj
                if os.path.exists('/site/proj') and not path.startswith('/site/proj'):
                    sub_path = 'file:///site/proj/{}'.format(make_path_safe(path))
                else:
                    sub_path = 'file:///{}'.format(make_path_safe(path))

                rel_import_statement = '''USING PERIODIC COMMIT 1000
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    MATCH (n:{annotation_type} {{id: csvLine.annotation_id}})
    CREATE (t:{subannotation_type}:{corpus_name}:speech {{id: csvLine.id, type: $subannotation_type, begin: toFloat(csvLine.begin),
                                end: toFloat(csvLine.end), label: CASE csvLine.label WHEN NULL THEN '' ELSE csvLine.label END  }})
    CREATE (t)-[:annotates]->(n)'''
                kwargs = {'path': sub_path, 'annotation_type': k,
                          'subannotation_type': s,
                          'corpus_name': corpus_context.cypher_safe_name}
                statement = rel_import_statement.format(**kwargs)
                try:
                    corpus_context.execute_cypher(statement, subannotation_type=s)
                except:
                    raise
                finally:
                    # with open(path, 'w'):
                    #    pass
                    os.remove(path)


def import_lexicon_csvs(corpus_context, typed_data, case_sensitive=False):
    """
    Import a lexicon from csv file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.CorpusContext`
        the corpus to load into
    typed_data : dict
        the data
    case_sensitive : boolean
        defaults to false

    """
    string_set_template = 'n.{name} = csvLine.{name}'
    float_set_template = 'n.{name} = toFloat(csvLine.{name})'
    int_set_template = 'n.{name} = toInteger(csvLine.{name})'
    bool_set_template = '''n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)'''
    properties = []
    for h, v in typed_data.items():
        if v == int:
            template = int_set_template
        elif v == bool:
            template = bool_set_template
        elif v == float:
            template = float_set_template
        else:
            template = string_set_template
        properties.append(template.format(name=h))
    properties = ',\n'.join(properties)
    directory = corpus_context.config.temporary_directory('csv')
    path = os.path.join(directory, 'lexicon_import.csv')
    # If on the Docker version, the files live in /site/proj
    if os.path.exists('/site/proj') and not path.startswith('/site/proj'):
        lex_path = 'file:///site/proj/{}'.format(make_path_safe(path))
    else:
        lex_path = 'file:///{}'.format(make_path_safe(path))
    if case_sensitive:
        import_statement = '''USING PERIODIC COMMIT 3000
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    with csvLine
    MATCH (n:{word_type}_type:{corpus_name}) where n.label = csvLine.label
    SET {new_properties}'''
    else:
        import_statement = '''USING PERIODIC COMMIT 3000
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    MATCH (n:{word_type}_type:{corpus_name}) where n.label_insensitive = csvLine.label
    SET {new_properties}'''

    statement = import_statement.format(path=lex_path,
                                        corpus_name=corpus_context.cypher_safe_name,
                                        word_type=corpus_context.word_name,
                                        new_properties=properties)
    corpus_context.execute_cypher(statement)
    for h, v in typed_data.items():
        try:
            corpus_context.execute_cypher('CREATE INDEX ON :%s(%s)' % (corpus_context.word_name, h))
        except neo4j.exceptions.ClientError as e:
            if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                raise
    os.remove(path)


def import_feature_csvs(corpus_context, typed_data):
    """
    Import features from csv file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.CorpusContext`
        the corpus to load into
    typed_data : dict
        the data
    """
    string_set_template = 'n.{name} = csvLine.{name}'
    float_set_template = 'n.{name} = toFloat(csvLine.{name})'
    int_set_template = 'n.{name} = toInteger(csvLine.{name})'
    bool_set_template = '''n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)'''
    properties = []
    for h, v in typed_data.items():
        if v == int:
            template = int_set_template
        elif v == bool:
            template = bool_set_template
        elif v == float:
            template = float_set_template
        else:
            template = string_set_template
        properties.append(template.format(name=h))
    properties = ',\n'.join(properties)
    directory = corpus_context.config.temporary_directory('csv')
    path = os.path.join(directory, 'feature_import.csv')

    # If on the Docker version, the files live in /site/proj
    if os.path.exists('/site/proj') and not path.startswith('/site/proj'):
        feat_path = 'file:///site/proj/{}'.format(make_path_safe(path))
    else:
        feat_path = 'file:///{}'.format(make_path_safe(path))

    import_statement = '''
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    MATCH (n:{phone_type}_type:{corpus_name}) where n.label = csvLine.label
    SET {new_properties}'''

    statement = import_statement.format(path=feat_path,
                                        corpus_name=corpus_context.cypher_safe_name,
                                        phone_type=corpus_context.phone_name,
                                        new_properties=properties)
    corpus_context.execute_cypher(statement)
    for h, v in typed_data.items():
        try:
            corpus_context.execute_cypher('CREATE INDEX ON :%s(%s)' % (corpus_context.phone_name, h))
        except neo4j.exceptions.ClientError as e:
            if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                raise
    os.remove(path)


def import_syllable_enrichment_csvs(corpus_context, typed_data):
    """
    Import syllable features from csv file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.syllabic.SyllabicContext`
        the corpus to load into
    typed_data : dict
        the data
    """
    string_set_template = 'n.{name} = csvLine.{name}'
    float_set_template = 'n.{name} = toFloat(csvLine.{name})'
    int_set_template = 'n.{name} = toInteger(csvLine.{name})'
    bool_set_template = '''n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)'''
    properties = []
    for h, v in typed_data.items():
        if v == int:
            template = int_set_template
        elif v == bool:
            template = bool_set_template
        elif v == float:
            template = float_set_template
        else:
            template = string_set_template
        properties.append(template.format(name=h))
    properties = ',\n'.join(properties)
    directory = corpus_context.config.temporary_directory('csv')
    path = os.path.join(directory, 'syllable_import.csv')

    # If on the Docker version, the files live in /site/proj
    if os.path.exists('/site/proj') and not path.startswith('/site/proj'):
        syl_path = 'file:///site/proj/{}'.format(make_path_safe(path))
    else:
        syl_path = 'file:///{}'.format(make_path_safe(path))

    import_statement = '''
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    MATCH (n:syllable_type:{corpus_name}) where n.label = csvLine.label
    SET {new_properties}'''

    statement = import_statement.format(path=syl_path,
                                        corpus_name=corpus_context.cypher_safe_name,
                                        phone_type="syllable",
                                        new_properties=properties)
    corpus_context.execute_cypher(statement)
    for h, v in typed_data.items():
        try:
            corpus_context.execute_cypher('CREATE INDEX ON :%s(%s)' % ("syllable", h))
        except neo4j.exceptions.ClientError as e:
            if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                raise


def import_utterance_enrichment_csvs(corpus_context, typed_data):
    """
    Import syllable features from csv file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.CorpusContext`
        the corpus to load into
    typed_data : dict
        the data
    """
    string_set_template = 'n.{name} = csvLine.{name}'
    float_set_template = 'n.{name} = toFloat(csvLine.{name})'
    int_set_template = 'n.{name} = toInteger(csvLine.{name})'
    bool_set_template = '''n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)'''
    properties = []
    for h, v in typed_data.items():
        if v == int:
            template = int_set_template
        elif v == bool:
            template = bool_set_template
        elif v == float:
            template = float_set_template
        else:
            template = string_set_template
        properties.append(template.format(name=h))
    properties = ',\n'.join(properties)
    directory = corpus_context.config.temporary_directory('csv')
    path = os.path.join(directory, 'utterance_enrichment.csv')

    # If on the Docker version, the files live in /site/proj
    if os.path.exists('/site/proj') and not path.startswith('/site/proj'):
        utt_path = 'file:///site/proj/{}'.format(make_path_safe(path))
    else:
        utt_path = 'file:///{}'.format(make_path_safe(path))

    import_statement = '''
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    MATCH (n:utterance:{corpus_name}) where n.id = csvLine.id
    SET {new_properties}'''

    statement = import_statement.format(path=utt_path,
                                        corpus_name=corpus_context.cypher_safe_name,
                                        phone_type="syllable",
                                        new_properties=properties)
    corpus_context.execute_cypher(statement)
    for h, v in typed_data.items():
        try:
            corpus_context.execute_cypher('CREATE INDEX ON :%s(%s)' % ("utterance", h))
        except neo4j.exceptions.ClientError as e:
            if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                raise


def import_speaker_csvs(corpus_context, typed_data):
    """
    Import a speaker from csv file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.spoken.SpokenContext`
        the corpus to load into
    typed_data : dict
        the data
    """
    string_set_template = 'n.{name} = csvLine.{name}'
    float_set_template = 'n.{name} = toFloat(csvLine.{name})'
    int_set_template = 'n.{name} = toInteger(csvLine.{name})'
    bool_set_template = '''n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)'''
    properties = []
    for h, v in typed_data.items():
        if v == int:
            template = int_set_template
        elif v == bool:
            template = bool_set_template
        elif v == float:
            template = float_set_template
        else:
            template = string_set_template
        properties.append(template.format(name=h))
    properties = ',\n'.join(properties)
    directory = corpus_context.config.temporary_directory('csv')
    path = os.path.join(directory, 'speaker_import.csv')

    # If on the Docker version, the files live in /site/proj
    if os.path.exists('/site/proj') and not path.startswith('/site/proj'):
        feat_path = 'file:///site/proj/{}'.format(make_path_safe(path))
    else:
        feat_path = 'file:///{}'.format(make_path_safe(path))

    import_statement = '''
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    MATCH (n:Speaker:{corpus_name}) where n.name = toString(csvLine.name)
    SET {new_properties}'''

    statement = import_statement.format(path=feat_path,
                                        corpus_name=corpus_context.cypher_safe_name,
                                        new_properties=properties)
    corpus_context.execute_cypher(statement)
    for h, v in typed_data.items():
        try:
            corpus_context.execute_cypher('CREATE INDEX ON :Speaker(%s)' % h)
        except neo4j.exceptions.ClientError as e:
            if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                raise
    os.remove(path)


def import_discourse_csvs(corpus_context, typed_data):
    """
    Import a discourse from csv file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.spoken.SpokenContext`
        the corpus to load into
    typed_data : dict
        the data
    """
    string_set_template = 'n.{name} = csvLine.{name}'
    float_set_template = 'n.{name} = toFloat(csvLine.{name})'
    int_set_template = 'n.{name} = toInteger(csvLine.{name})'
    bool_set_template = '''n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)'''
    properties = []
    for h, v in typed_data.items():
        if v == int:
            template = int_set_template
        elif v == bool:
            template = bool_set_template
        elif v == float:
            template = float_set_template
        else:
            template = string_set_template
        properties.append(template.format(name=h))
    properties = ',\n'.join(properties)
    directory = corpus_context.config.temporary_directory('csv')
    path = os.path.join(directory, 'discourse_import.csv')

    # If on the Docker version, the files live in /site/proj
    if os.path.exists('/site/proj') and not path.startswith('/site/proj'):
        feat_path = 'file:///site/proj/{}'.format(make_path_safe(path))
    else:
        feat_path = 'file:///{}'.format(make_path_safe(path))

    import_statement = '''
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    MATCH (n:Discourse:{corpus_name}) where n.name = toString(csvLine.name)
    SET {new_properties}'''

    statement = import_statement.format(path=feat_path,
                                        corpus_name=corpus_context.cypher_safe_name,
                                        new_properties=properties)
    corpus_context.execute_cypher(statement)
    for h, v in typed_data.items():
        try:
            corpus_context.execute_cypher('CREATE INDEX ON :Discourse(%s)' % h)
        except neo4j.exceptions.ClientError as e:
            if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                raise
    os.remove(path)


def import_utterance_csv(corpus_context, call_back=None, stop_check=None):
    """
    Import an utterance from csv file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.CorpusContext`
        the corpus to load into
    discourse : str
        the discourse the utterance is in
    """
    import time
    speakers = corpus_context.speakers
    if call_back is not None:
        call_back('Importing data...')
        call_back(0, len(speakers))
    try:
        corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:utterance) ASSERT node.id IS UNIQUE')
    except neo4j.exceptions.ClientError as e:
        if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
            raise
    for i, s in enumerate(speakers):
        discourses = corpus_context.get_discourses_of_speaker(s)
        for d in discourses:
            if stop_check is not None and stop_check():
                return
            if call_back is not None:
                call_back('Importing data for speaker {} of {} ({})...'.format(i, len(speakers), s))
                call_back(i)

            path = os.path.join(corpus_context.config.temporary_directory('csv'), '{}_{}_utterance.csv'.format(re.sub(r'\W', '_', s), d))
            if corpus_context.config.debug:
                print('Importing utterances for speaker {} in discourse {}, using import file {}'.format(s, d, path))

            # If on the Docker version, the files live in /site/proj
            if os.path.exists('/site/proj') and not path.startswith('/site/proj'):
                csv_path = 'file:///site/proj/{}'.format(make_path_safe(path))
            else:
                csv_path = 'file:///{}'.format(make_path_safe(path))

            begin = time.time()
            node_statement = '''
            USING PERIODIC COMMIT 1000
                    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
                    MATCH (begin:{word_type}:{corpus}:speech {{id: csvLine.begin_word_id}}),
                    (end:{word_type}:{corpus}:speech {{id: csvLine.end_word_id}})
                    WITH csvLine, begin, end
                    CREATE (utt:utterance:{corpus}:speech {{id: csvLine.id, begin: begin.begin, end: end.end}})-[:is_a]->(u_type:utterance_type:{corpus})
            '''

            statement = node_statement.format(path=csv_path,
                                              corpus=corpus_context.cypher_safe_name,
                                              word_type=corpus_context.word_name)
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print('Utterance node creation took {} seconds.'.format(time.time() - begin))

            begin = time.time()
            rel_statement = '''USING PERIODIC COMMIT 1000
                    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
                    MATCH (d:Discourse:{corpus})<-[:spoken_in]-(begin:{word_type}:{corpus}:speech {{id: csvLine.begin_word_id}})-[:spoken_by]->(s:Speaker:{corpus}),
                    (utt:utterance:{corpus}:speech {{id: csvLine.id}})
                    CREATE
                        (d)<-[:spoken_in]-(utt),
                        (s)<-[:spoken_by]-(utt)
            '''
            statement = rel_statement.format(path=csv_path,
                                             corpus=corpus_context.cypher_safe_name,
                                             word_type=corpus_context.word_name)
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print('Spoken relationship creation took {} seconds.'.format(time.time() - begin))

            begin = time.time()
            rel_statement = '''USING PERIODIC COMMIT 1000
                    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
                    MATCH (begin:{word_type}:{corpus}:speech {{id: csvLine.begin_word_id}}),
                    (utt:utterance:{corpus}:speech {{id: csvLine.id}}),
                    (prev:utterance {{id:csvLine.prev_id}})
                    CREATE (prev)-[:precedes]->(utt)
            '''
            statement = rel_statement.format(path=csv_path,
                                             corpus=corpus_context.cypher_safe_name,
                                             word_type=corpus_context.word_name)
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print('Precedence relationship creation took {} seconds.'.format(time.time() - begin))

            begin = time.time()
            word_statement = '''USING PERIODIC COMMIT 1000
                    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
                    MATCH (begin:{word_type}:{corpus}:speech {{id: csvLine.begin_word_id}}),
                    (utt:utterance:{corpus}:speech {{id: csvLine.id}}),
                    (end:{word_type}:{corpus}:speech {{id: csvLine.end_word_id}}),
                    path = shortestPath((begin)-[:precedes*0..]->(end))
                    WITH utt, nodes(path) as words
                    UNWIND words as w
                    CREATE (w)-[:contained_by]->(utt)
            '''
            statement = word_statement.format(path=csv_path,
                                              corpus=corpus_context.cypher_safe_name,
                                              word_type=corpus_context.word_name)
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print('Hierarchical relationship creation took {} seconds.'.format(time.time() - begin))
            os.remove(path)


def import_syllable_csv(corpus_context, call_back=None, stop_check=None):
    """
    Import a syllable from csv file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.syllabic.SyllabicContext`
        the corpus to load into
    """
    import time
    speakers = corpus_context.speakers
    if call_back is not None:
        call_back('Importing syllables...')
        call_back(0, len(speakers))
    try:
        corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:syllable) ASSERT node.id IS UNIQUE')
    except neo4j.exceptions.ClientError as e:
        if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
            raise
    try:
        corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:syllable_type) ASSERT node.id IS UNIQUE')
    except neo4j.exceptions.ClientError as e:
        if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
            raise
    try:
        corpus_context.execute_cypher('CREATE INDEX ON :syllable(begin)')
    except neo4j.exceptions.ClientError as e:
        if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
            raise
    try:
        corpus_context.execute_cypher('CREATE INDEX ON :syllable(prev_id)')
    except neo4j.exceptions.ClientError as e:
        if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
            raise
    try:
        corpus_context.execute_cypher('CREATE INDEX ON :syllable(end)')
    except neo4j.exceptions.ClientError as e:
        if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
            raise
    try:
        corpus_context.execute_cypher('CREATE INDEX ON :syllable(label)')
    except neo4j.exceptions.ClientError as e:
        if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
            raise
    try:
        corpus_context.execute_cypher('CREATE INDEX ON :syllable_type(label)')
    except neo4j.exceptions.ClientError as e:
        if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
            raise
    for i, s in enumerate(speakers):
        if stop_check is not None and stop_check():
            return
        if call_back is not None:
            call_back('Importing syllables for speaker {} of {} ({})...'.format(i, len(speakers), s))
            call_back(i)
        discourses = corpus_context.get_discourses_of_speaker(s)
        for d in discourses:
            path = os.path.join(corpus_context.config.temporary_directory('csv'),
                                '{}_{}_syllable.csv'.format(re.sub(r'\W', '_', s), d))
            if corpus_context.config.debug:
                print('Importing syllables for speaker {} in discourse {}, using import file {}'.format(s, d, path))
            # If on the Docker version, the files live in /site/proj
            if os.path.exists('/site/proj') and not path.startswith('/site/proj'):
                csv_path = 'file:///site/proj/{}'.format(make_path_safe(path))
            else:
                csv_path = 'file:///{}'.format(make_path_safe(path))

            begin = time.time()
            nucleus_statement = '''
            USING PERIODIC COMMIT 2000
            LOAD CSV WITH HEADERS FROM "{path}" as csvLine
            MATCH (n:{phone_name}:{corpus}:speech {{id: csvLine.vowel_id}})-[r:contained_by]->(w:{word_name}:{corpus}:speech)
            SET n :nucleus, n.syllable_position = 'nucleus'
            '''
            statement = nucleus_statement.format(path=csv_path,
                                                 corpus=corpus_context.cypher_safe_name,
                                                 word_name=corpus_context.word_name,
                                                 phone_name=corpus_context.phone_name)
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print('Nucleus definition took {} seconds.'.format(time.time() - begin))

            begin = time.time()
            node_statement = '''
            USING PERIODIC COMMIT 2000
            LOAD CSV WITH HEADERS FROM "{path}" as csvLine
            MERGE (s_type:syllable_type:{corpus} {{id: csvLine.type_id}})
            ON CREATE SET s_type.label = csvLine.label
            WITH s_type, csvLine
            CREATE (s:syllable:{corpus}:speech {{id: csvLine.id, prev_id: csvLine.prev_id,
                                label: csvLine.label,
                                begin: toFloat(csvLine.begin), end: toFloat(csvLine.end)}}),
                    (s)-[:is_a]->(s_type)
            '''
            statement = node_statement.format(path=csv_path,
                                              corpus=corpus_context.cypher_safe_name)
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print('Syllable node creation took {} seconds.'.format(time.time() - begin))

            begin = time.time()
            rel_statement = '''
            USING PERIODIC COMMIT 2000
            LOAD CSV WITH HEADERS FROM "{path}" as csvLine
            MATCH (n:{phone_name}:{corpus}:speech:nucleus {{id: csvLine.vowel_id}})-[:contained_by]->(w:{word_name}:{corpus}:speech),
                    (s:syllable:{corpus}:speech {{id: csvLine.id}})
            WITH n, w, s
            CREATE (s)-[:contained_by]->(w),
                    (n)-[:contained_by]->(s)
            '''
            statement = rel_statement.format(path=csv_path,
                                             corpus=corpus_context.cypher_safe_name,
                                             word_name=corpus_context.word_name,
                                             phone_name=corpus_context.phone_name)
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print('Hierarchical relationship creation took {} seconds.'.format(time.time() - begin))

            begin = time.time()
            rel_statement = '''
            USING PERIODIC COMMIT 2000
            LOAD CSV WITH HEADERS FROM "{path}" as csvLine
            MATCH (n:{phone_name}:{corpus}:speech:nucleus {{id: csvLine.vowel_id}}),
                    (s:syllable:{corpus}:speech {{id: csvLine.id}}),
                    (n)-[:spoken_by]->(sp:Speaker),
                    (n)-[:spoken_in]->(d:Discourse)
            WITH sp, d, s
            CREATE (s)-[:spoken_by]->(sp),
                    (s)-[:spoken_in]->(d)
            '''
            statement = rel_statement.format(path=csv_path,
                                             corpus=corpus_context.cypher_safe_name,
                                             word_name=corpus_context.word_name,
                                             phone_name=corpus_context.phone_name)
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print('Spoken relationship creation took {} seconds.'.format(time.time() - begin))

            begin = time.time()
            prev_rel_statement = '''
            USING PERIODIC COMMIT 2000
            LOAD CSV WITH HEADERS FROM "{path}" as csvLine
            MATCH (s:syllable:{corpus}:speech {{id: csvLine.id}})
            with csvLine, s
            MATCH (prev:syllable {{id:csvLine.prev_id}})
              CREATE (prev)-[:precedes]->(s)
            '''
            statement = prev_rel_statement.format(path=csv_path,
                                                  corpus=corpus_context.cypher_safe_name,
                                                  word_name=corpus_context.word_name,
                                                  phone_name=corpus_context.phone_name)
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print('Precedence relationship creation took {} seconds.'.format(time.time() - begin))

            begin = time.time()
            del_rel_statement = '''
            USING PERIODIC COMMIT 2000
            LOAD CSV WITH HEADERS FROM "{path}" as csvLine
            MATCH (n:{phone_name}:{corpus}:speech:nucleus {{id: csvLine.vowel_id}})-[r:contained_by]->(w:{word_name}:{corpus}:speech)
            DELETE r
            '''
            statement = del_rel_statement.format(path=csv_path,
                                                 corpus=corpus_context.cypher_safe_name,
                                                 word_name=corpus_context.word_name,
                                                 phone_name=corpus_context.phone_name)
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print('Phone-word relationship deletion took {} seconds.'.format(time.time() - begin))

            begin = time.time()
            onset_statement = '''
            USING PERIODIC COMMIT 2000
            LOAD CSV WITH HEADERS FROM "{path}" as csvLine
            MATCH (n:{phone_name}:nucleus:{corpus}:speech)-[:contained_by]->(s:syllable:{corpus}:speech {{id: csvLine.id}})-[:contained_by]->(w:{word_name}:{corpus}:speech)
            WITH csvLine, s, w, n
            OPTIONAL MATCH
                    (onset:{phone_name}:{corpus} {{id: csvLine.onset_id}}),
                    onspath = (onset)-[:precedes*1..10]->(n)
    
            with n, w,s, csvLine, onspath
            UNWIND (case when onspath is not null then nodes(onspath)[0..-1] else [null] end) as o
    
            OPTIONAL MATCH (o)-[r:contained_by]->(w)
            with n, w,s, csvLine, [x in collect(o) WHERE x is not NULL| x] as ons,
            [x in collect(r) WHERE x is not NULL | x] as rels
            FOREACH (o in ons | SET o :onset, o.syllable_position = 'onset')
            FOREACH (o in ons | CREATE (o)-[:contained_by]->(s))
            FOREACH (r in rels | DELETE r)
            '''
            statement = onset_statement.format(path=csv_path,
                                               corpus=corpus_context.cypher_safe_name,
                                               word_name=corpus_context.word_name,
                                               phone_name=corpus_context.phone_name)
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print('Onset hierarchical relationship creation took {} seconds.'.format(time.time() - begin))

            begin = time.time()
            coda_statment = '''
            USING PERIODIC COMMIT 2000
            LOAD CSV WITH HEADERS FROM "{path}" as csvLine
            MATCH (n:nucleus:{corpus}:speech)-[:contained_by]->(s:syllable:{corpus}:speech {{id: csvLine.id}})-[:contained_by]->(w:{word_name}:{corpus}:speech)
            WITH csvLine, s, w, n
            OPTIONAL MATCH
                    (coda:{phone_name}:{corpus} {{id: csvLine.coda_id}}),
                codapath = (n)-[:precedes*1..10]->(coda)
            WITH n, w, s, codapath
            UNWIND (case when codapath is not null then nodes(codapath)[1..] else [null] end) as c
    
            OPTIONAL MATCH (c)-[r:contained_by]->(w)
            WITH n, w,s, [x in collect(c) WHERE x is not NULL | x] as cod,
            [x in collect(r) WHERE x is not NULL | x] as rels
            FOREACH (c in cod | SET c :coda, c.syllable_position = 'coda')
            FOREACH (c in cod | CREATE (c)-[:contained_by]->(s))
            FOREACH (r in rels | DELETE r)
            '''
            statement = coda_statment.format(path=csv_path,
                                             corpus=corpus_context.cypher_safe_name,
                                             word_name=corpus_context.word_name,
                                             phone_name=corpus_context.phone_name)
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print('Coda hierarchical relationship creation took {} seconds.'.format(time.time() - begin))
            os.remove(path)


def import_nonsyl_csv(corpus_context, call_back=None, stop_check=None):
    """
    Import a nonsyllable from csv file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.syllabic.SyllabicContext`
        the corpus to load into
    split_name : str
        the identifier of the file
    """
    import time
    speakers = corpus_context.speakers
    if call_back is not None:
        call_back('Importing degenerate syllables...')
        call_back(0, len(speakers))
    try:
        corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:syllable) ASSERT node.id IS UNIQUE')
    except neo4j.exceptions.ClientError as e:
        if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
            raise
    try:
        corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:syllable_type) ASSERT node.id IS UNIQUE')
    except neo4j.exceptions.ClientError as e:
        if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
            raise
    try:
        corpus_context.execute_cypher('CREATE INDEX ON :syllable(begin)')
    except neo4j.exceptions.ClientError as e:
        if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
            raise
    try:
        corpus_context.execute_cypher('CREATE INDEX ON :syllable(end)')
    except neo4j.exceptions.ClientError as e:
        if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
            raise
    try:
        corpus_context.execute_cypher('CREATE INDEX ON :syllable(label)')
    except neo4j.exceptions.ClientError as e:
        if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
            raise
    try:
        corpus_context.execute_cypher('CREATE INDEX ON :syllable_type(label)')
    except neo4j.exceptions.ClientError as e:
        if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
            raise
    for i, s in enumerate(speakers):
        if stop_check is not None and stop_check():
            return
        if call_back is not None:
            call_back('Importing degenerate syllables for speaker {} of {} ({})...'.format(i, len(speakers), s))
            call_back(i)
        discourses = corpus_context.get_discourses_of_speaker(s)
        for d in discourses:
            path = os.path.join(corpus_context.config.temporary_directory('csv'),
                                '{}_{}_nonsyl.csv'.format(re.sub(r'\W', '_', s), d))

            if corpus_context.config.debug:
                print('Importing degenerate syllables for speaker {} in discourse {}, using import file {}'.format(s, d,
                                                                                                                   path))
            # If on the Docker version, the files live in /site/proj
            if os.path.exists('/site/proj') and not path.startswith('/site/proj'):
                csv_path = 'file:///site/proj/{}'.format(make_path_safe(path))
            else:
                csv_path = 'file:///{}'.format(make_path_safe(path))

            begin = time.time()
            node_statement = '''USING PERIODIC COMMIT 2000
            LOAD CSV WITH HEADERS FROM "{path}" as csvLine
            MERGE (s_type:syllable_type:{corpus} {{id: csvLine.type_id}})
            ON CREATE SET s_type.label = csvLine.label
            WITH s_type, csvLine
        CREATE (s:syllable:{corpus}:speech {{id: csvLine.id, prev_id: csvLine.prev_id,
                                        begin: toFloat(csvLine.begin), end: toFloat(csvLine.end),
                                        label: csvLine.label}}),
                    (s)-[:is_a]->(s_type) 
            '''

            statement = node_statement.format(path=csv_path,
                                              corpus=corpus_context.cypher_safe_name)
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print('Syllable node creation took {} seconds.'.format(time.time() - begin))

            begin = time.time()
            rel_statement = '''
            USING PERIODIC COMMIT 2000
            LOAD CSV WITH HEADERS FROM "{path}" as csvLine
        MATCH (o:{phone_name}:{corpus}:speech {{id: csvLine.onset_id}})-[r:contained_by]->(w:{word_name}:{corpus}:speech),
                    (o)-[:spoken_by]->(sp:Speaker),
                    (o)-[:spoken_in]->(d:Discourse),
                    (s:syllable:{corpus}:speech {{id: csvLine.id}})
            WITH w, csvLine, sp, d, s
            CREATE (s)-[:contained_by]->(w),
                    (s)-[:spoken_by]->(sp),
                    (s)-[:spoken_in]->(d)
            '''
            statement = rel_statement.format(path=csv_path,
                                             corpus=corpus_context.cypher_safe_name,
                                             word_name=corpus_context.word_name,
                                             phone_name=corpus_context.phone_name)
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print('Hierarchical and spoken relationship creation took {} seconds.'.format(time.time() - begin))

            begin = time.time()
            rel_statement = '''
            USING PERIODIC COMMIT 2000
            LOAD CSV WITH HEADERS FROM "{path}" as csvLine
        MATCH (s:syllable:{corpus}:speech {{id: csvLine.id}})
            with csvLine, s
            MATCH (prev:syllable {{id:csvLine.prev_id}})
              CREATE (prev)-[:precedes]->(s)
            '''
            statement = rel_statement.format(path=csv_path,
                                             corpus=corpus_context.cypher_safe_name,
                                             word_name=corpus_context.word_name,
                                             phone_name=corpus_context.phone_name)
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print('First precedence relationship creation took {} seconds.'.format(time.time() - begin))

            begin = time.time()
            rel_statement = '''
            USING PERIODIC COMMIT 2000
            LOAD CSV WITH HEADERS FROM "{path}" as csvLine
        MATCH (s:syllable:{corpus}:speech {{id: csvLine.id}})
            with csvLine, s
            MATCH (foll:syllable {{prev_id:csvLine.id}})
              CREATE (s)-[:precedes]->(foll)
            '''
            statement = rel_statement.format(path=csv_path,
                                             corpus=corpus_context.cypher_safe_name,
                                             word_name=corpus_context.word_name,
                                             phone_name=corpus_context.phone_name)
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print('Second precedence relationship creation took {} seconds.'.format(time.time() - begin))

            begin = time.time()
            phone_statement = '''USING PERIODIC COMMIT 2000
            LOAD CSV WITH HEADERS FROM "{path}" as csvLine
        MATCH (o:{phone_name}:{corpus}:speech {{id: csvLine.onset_id}}),
        (s:syllable:{corpus}:speech {{id: csvLine.id}})-[:contained_by]->(w:{word_name}:{corpus}:speech)
        with o, w, csvLine, s
        OPTIONAL MATCH
        (c:{phone_name}:{corpus}:speech {{id: csvLine.coda_id}})-[:contained_by]->(w),
        p = (o)-[:precedes*..10]->(c)
        with o, w, s, p, csvLine
            UNWIND (case when p is not null then nodes(p) else [o] end) as c
    
            OPTIONAL MATCH (c)-[r:contained_by]->(w)
            with w,s, toInteger(csvLine.break) as break, [x in collect(c) WHERE x is not NULL | x] as cod,
            [x in collect(r) WHERE x is not NULL| x] as rels
            FOREACH (c in cod[break..] | SET c :coda, c.syllable_position = 'coda')
            FOREACH (c in cod[..break] | SET c :onset, c.syllable_position = 'onset')
            FOREACH (c in cod | CREATE (c)-[:contained_by]->(s))
            FOREACH (r in rels | DELETE r)
            '''
            statement = phone_statement.format(path=csv_path,
                                               corpus=corpus_context.cypher_safe_name,
                                               word_name=corpus_context.word_name,
                                               phone_name=corpus_context.phone_name)
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print('Onset/coda hierarchical relationship creation took {} seconds.'.format(time.time() - begin))
            os.remove(path)


def import_subannotation_csv(corpus_context, type, annotated_type, props):
    """
    Import a subannotation from csv file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.AnnotatedContext`
        the corpus to load into
    type : str
        the file name of the csv
    annotated_type : obj

    props : list

    """
    path = os.path.join(corpus_context.config.temporary_directory('csv'),
                        '{}_subannotations.csv'.format(type))

    # If on the Docker version, the files live in /site/proj
    if os.path.exists('/site/proj') and not path.startswith('/site/proj'):
        csv_path = 'file:///site/proj/{}'.format(make_path_safe(path))
    else:
        csv_path = 'file:///{}'.format(make_path_safe(path))

    prop_temp = '''{name}: csvLine.{name}'''
    properties = []
    try:
        corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:%s) ASSERT node.id IS UNIQUE' % type)
    except neo4j.exceptions.ClientError as e:
        if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
            raise

    for p in props:
        if p in ['id', 'annotated_id', 'begin', 'end']:
            continue
        properties.append(prop_temp.format(name=p))
    if properties:
        properties = ', ' + ', '.join(properties)
    else:
        properties = ''
    statement = '''USING PERIODIC COMMIT 500
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            MATCH (annotated:{a_type}:{corpus} {{id: csvLine.annotated_id}})
            CREATE (annotated) <-[:annotates]-(annotation:{type}:{corpus}
                {{id: csvLine.id, type: $type, begin: toFloat(csvLine.begin),
                end: toFloat(csvLine.end){properties}}})
            '''
    statement = statement.format(path=csv_path,
                                 corpus=corpus_context.cypher_safe_name,
                                 a_type=annotated_type,
                                 type=type,
                                 properties=properties)
    corpus_context.execute_cypher(statement, type=type)
    for p in props:
        if p in ['id', 'annotated_id']:
            continue
        try:
            corpus_context.execute_cypher('CREATE INDEX ON :%s(%s)' % (type, p))
        except neo4j.exceptions.ClientError as e:
            if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                raise
    os.remove(path)


def import_token_csv(corpus_context, path, annotated_type, id_column, properties=None):
    """
    Adds new properties to a list of tokens of a given type.

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.AnnotatedContext`
        the corpus to load into
    path : str
        the file name of the csv
    annotated_type : str
        the type of the tokens that are being updated
    id_column : str
        the header name for the column containing IDs
    properties : list
        a list of column names to update, if None, assume all columns will be updated(default)
    """
    if properties is None:
        with open(path, 'r') as f:
            properties = [x.strip() for x in f.readline().split(',') if x.strip() != id_column]

    is_subann = not annotated_type in corpus_context.hierarchy.annotation_types

    if is_subann:
        found_subann = False
        for k, v in corpus_context.hierarchy.subannotations.items():
            if annotated_type in v:
                found_subann = True
        if not found_subann:
            raise KeyError("Subannotation {} does not exist in this corpus".format(annotated_type))

    props_to_add = []
    for p in properties:
        if is_subann:
            if not corpus_context.hierarchy.has_subannotation_property(annotated_type, p):
                props_to_add.append((p, str))
        else:
            if not corpus_context.hierarchy.has_token_property(annotated_type, p):
                props_to_add.append((p, str))

    if props_to_add:
        if is_subann:
            corpus_context.hierarchy.add_subannotation_properties(corpus_context, annotated_type, props_to_add)
        else:
            corpus_context.hierarchy.add_token_properties(corpus_context, annotated_type, props_to_add)
        corpus_context.encode_hierarchy()

    property_update = ', '.join(["x.{} = csvLine.{}".format(p, p) for p in properties])
    statement = '''USING PERIODIC COMMIT 500
            LOAD CSV WITH HEADERS FROM "file://{path}" AS csvLine
            MATCH (x:{a_type}:{corpus} {{id: csvLine.{id_column}}})
            SET {property_update}
            '''.format(path=path, a_type=annotated_type, corpus=corpus_context.cypher_safe_name,
                       id_column=id_column, property_update=property_update)
    corpus_context.execute_cypher(statement)
    os.remove(path)
