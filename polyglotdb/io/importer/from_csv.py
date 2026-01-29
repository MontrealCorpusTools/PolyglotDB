import csv
import logging
import os
import re
import time

import neo4j
import numpy as np


def make_path_safe(path):
    """Takes a path and returns it with the associated Javascript URL-safe characters"""
    replacements = [
        ("%", "%25"),
        ("\\", "/"),
        (" ", "%20"),
        ("'", "\\'"),
        ("?", "%3F"),
        (";", "%3B"),
        ("<", "%3C"),
        ("=", "%3D"),
        (">", "%3E"),
        (":", "%3A"),
        ("*", "%2A"),
        ("&", "%26"),
        ("(", "%28"),
        (")", "%29"),
        ("@", "%40"),
        ("!", "%21"),
        ("#", "%23"),
    ]
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
    log = logging.getLogger("{}_loading".format(corpus_context.corpus_name))
    prop_temp = """{name}: csvLine.{name}"""
    for at, h in type_headers.items():
        path = os.path.join(
            corpus_context.config.temporary_directory("csv"), "{}_type.csv".format(at)
        )
        # If on the Docker version, the files live in /site/proj
        if os.path.exists("/site/proj") and not path.startswith("/site/proj"):
            type_path = "file:///site/proj/{}".format(make_path_safe(path))
        else:
            type_path = "file:///{}".format(make_path_safe(path))
        try:
            corpus_context.execute_cypher(
                "CREATE CONSTRAINT FOR (node:%s_type) REQUIRE node.id IS UNIQUE" % at
            )
        except neo4j.exceptions.ClientError as e:
            if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
                raise

        properties = []
        for x in h:
            properties.append(prop_temp.format(name=x))
        if "label" in h:
            properties.append("label_insensitive: toLower(csvLine.label)")
            try:
                corpus_context.execute_cypher(
                    "CREATE INDEX FOR (n:%s_type) ON (n.label_insensitive)" % at
                )
            except neo4j.exceptions.ClientError as e:
                if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
                    raise
        for x in h:
            if x != "id":
                try:
                    corpus_context.execute_cypher(
                        "CREATE INDEX FOR (n:%s_type) ON (n.%s)" % (at, x)
                    )
                except neo4j.exceptions.ClientError as e:
                    if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
                        raise
        if properties:
            type_prop_string = ", ".join(properties)
        else:
            type_prop_string = ""
        type_import_statement = """
        LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
        CALL (csvLine) {{
            MERGE (n:{annotation_type}_type:{corpus_name} {{ {type_property_string} }})
        }} IN TRANSACTIONS OF 2000 ROWS
        """
        kwargs = {
            "path": type_path,
            "annotation_type": at,
            "type_property_string": type_prop_string,
            "corpus_name": corpus_context.cypher_safe_name,
        }
        statement = type_import_statement.format(**kwargs)
        log.info("Loading {} types...".format(at))
        begin = time.time()
        try:
            corpus_context.execute_cypher(statement)
        finally:
            #    with open(path, 'w'):
            #        pass
            os.remove(path)

        log.info("Finished loading {} types!".format(at))
        log.debug("{} type loading took: {} seconds.".format(at, time.time() - begin))


def import_csvs(
    corpus_context, speakers, token_headers, hierarchy, call_back=None, stop_check=None
):
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
    log = logging.getLogger("{}_loading".format(corpus_context.corpus_name))
    log.info("Beginning to import data into the graph database...")
    initial_begin = time.time()

    prop_temp = """{name}: csvLine.{name}"""

    directory = corpus_context.config.temporary_directory("csv")
    annotation_types = hierarchy.highest_to_lowest
    if call_back is not None:
        call_back("Importing data...")
        call_back(0, len(speakers) * len(annotation_types))
        cur = 0
    statements = []

    def _unique_function(tx, at):
        tx.run("CREATE CONSTRAINT FOR (node:%s) REQUIRE node.id IS UNIQUE" % at)

    def _prop_index(tx, at, prop):
        tx.run("CREATE INDEX FOR (n:%s) ON (n.%s)" % (at, prop))

    def _label_index(tx, at):
        tx.run("CREATE INDEX FOR (n:%s) ON (n.label_insensitive)" % at)

    def _begin_index(tx, at):
        tx.run("CREATE INDEX FOR (n:%s) ON (n.begin)" % at)

    def _end_index(tx, at):
        tx.run("CREATE INDEX FOR (n:%s) ON (n.end)" % at)

    corpus_name = corpus_context.cypher_safe_name
    with corpus_context.graph_driver.session() as session:
        for i, s in enumerate(speakers):
            speaker_statements = []
            for at in annotation_types:
                if stop_check is not None and stop_check():
                    return
                if call_back is not None:
                    call_back(cur)
                    cur += 1
                path = os.path.join(directory, "{}_{}.csv".format(re.sub(r"\W", "_", s), at))
                if not os.path.exists(path):  # Already imported
                    continue
                # If on the Docker version, the files live in /site/proj
                if os.path.exists("/site/proj") and not path.startswith("/site/proj"):
                    rel_path = "file:///site/proj/{}".format(make_path_safe(path))
                else:
                    rel_path = "file:///{}".format(make_path_safe(path))
                try:
                    session.execute_write(_unique_function, at)
                except neo4j.exceptions.ClientError as e:
                    if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
                        raise

                properties = []

                for x in token_headers[at]:
                    if x in [
                        "type_id",
                        "id",
                        "previous_id",
                        "speaker",
                        "discourse",
                        "begin",
                        "end",
                    ]:
                        continue
                    properties.append(prop_temp.format(name=x))
                    try:
                        session.execute_write(_prop_index, at, x)
                    except neo4j.exceptions.ClientError as e:
                        if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
                            raise
                if "label" in token_headers[at]:
                    properties.append("label_insensitive: toLower(csvLine.label)")
                    try:
                        session.execute_write(_label_index, at)
                    except neo4j.exceptions.ClientError as e:
                        if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
                            raise
                st = hierarchy[at]
                if properties:
                    token_prop_string = ", " + ", ".join(properties)
                else:
                    token_prop_string = ""
                node_import_statement = """
                LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
                CALL (csvLine) {{
                    CREATE (t:{annotation_type}:{corpus_name}:speech {{
                        id: csvLine.id,
                        begin: toFloat(csvLine.begin),
                        end: toFloat(csvLine.end){token_property_string}
                    }})
                }} IN TRANSACTIONS OF 2000 ROWS
                """

                node_kwargs = {
                    "path": rel_path,
                    "annotation_type": at,
                    "token_property_string": token_prop_string,
                    "corpus_name": corpus_context.cypher_safe_name,
                }
                if st is not None:
                    rel_import_statement = """
                    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
                    CALL (csvLine) {{
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
                    }} IN TRANSACTIONS OF 2000 ROWS"""
                    rel_kwargs = {
                        "path": rel_path,
                        "annotation_type": at,
                        "corpus_name": corpus_context.cypher_safe_name,
                        "stype": st,
                    }
                else:
                    rel_import_statement = """
                    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
                    CALL (csvLine) {{
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
                    }} IN TRANSACTIONS OF 2000 ROWS"""
                    rel_kwargs = {
                        "path": rel_path,
                        "annotation_type": at,
                        "corpus_name": corpus_context.cypher_safe_name,
                    }
                node_statement = node_import_statement.format(**node_kwargs)
                rel_statement = rel_import_statement.format(**rel_kwargs)
                speaker_statements.append((node_statement, rel_statement, path, at, s))
                begin = time.time()
                try:
                    session.execute_write(_begin_index, at)
                except neo4j.exceptions.ClientError as e:
                    if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
                        raise
                try:
                    session.execute_write(_end_index, at)
                except neo4j.exceptions.ClientError as e:
                    if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
                        raise
            statements.append(speaker_statements)

    for i, speaker_statements in enumerate(statements):
        if call_back is not None:
            call_back(
                "Importing data for speaker {} of {} ({})...".format(
                    i, len(statements), speaker_statements[0][4]
                )
            )
        for s in speaker_statements:
            log.info("Loading {} relationships...".format(s[3]))
            try:
                corpus_context.execute_cypher(s[0])
                corpus_context.execute_cypher(s[1])
            finally:
                os.remove(s[2])
            log.info("Finished loading {} relationships for speaker {}!".format(s[3], s[4]))
            log.debug(
                "{} relationships loading took: {} seconds.".format(s[3], time.time() - begin)
            )
    statement = f"""
    MATCH (subunit:{corpus_name}:speech)-[:contained_by*2..]->(superunit:{corpus_name}:speech)
    with subunit, superunit
    CREATE (subunit)-[:contained_by]->(superunit)
    """
    corpus_context.execute_cypher(statement)
    log.info("Finished importing into the graph database!")
    log.debug("Graph importing took: {} seconds".format(time.time() - initial_begin))

    for sp in speakers:
        for k, v in hierarchy.subannotations.items():
            for s in v:
                path = os.path.join(directory, "{}_{}_{}.csv".format(re.sub(r"\W", "_", sp), k, s))
                try:
                    corpus_context.execute_cypher(
                        "CREATE CONSTRAINT FOR (node:%s) REQUIRE node.id IS UNIQUE" % s
                    )
                except neo4j.exceptions.ClientError as e:
                    if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
                        raise
                # If on the Docker version, the files live in /site/proj
                if os.path.exists("/site/proj") and not path.startswith("/site/proj"):
                    sub_path = "file:///site/proj/{}".format(make_path_safe(path))
                else:
                    sub_path = "file:///{}".format(make_path_safe(path))

                rel_import_statement = """
                LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
                CALL (csvLine) {{
                    MATCH (n:{annotation_type} {{id: csvLine.annotation_id}})
                    CREATE (t:{subannotation_type}:{corpus_name}:speech {{
                        id: csvLine.id,
                        type: $subannotation_type,
                        begin: toFloat(csvLine.begin),
                        end: toFloat(csvLine.end),
                        label: CASE csvLine.label WHEN NULL THEN '' ELSE csvLine.label END
                    }})
                    CREATE (t)-[:annotates]->(n)
                }} IN TRANSACTIONS OF 1000 ROWS
                """

                kwargs = {
                    "path": sub_path,
                    "annotation_type": k,
                    "subannotation_type": s,
                    "corpus_name": corpus_context.cypher_safe_name,
                }
                statement = rel_import_statement.format(**kwargs)
                try:
                    corpus_context.execute_cypher(statement, subannotation_type=s)
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
    string_set_template = "n.{name} = csvLine.{name}"
    float_set_template = "n.{name} = toFloat(csvLine.{name})"
    int_set_template = "n.{name} = toInteger(csvLine.{name})"
    bool_set_template = (
        """n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)"""
    )
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
    properties = ",\n".join(properties)
    directory = corpus_context.config.temporary_directory("csv")
    path = os.path.join(directory, "lexicon_import.csv")
    # If on the Docker version, the files live in /site/proj
    if os.path.exists("/site/proj") and not path.startswith("/site/proj"):
        lex_path = "file:///site/proj/{}".format(make_path_safe(path))
    else:
        lex_path = "file:///{}".format(make_path_safe(path))
    if case_sensitive:
        import_statement = """
        LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
        CALL (csvLine) {{
            WITH csvLine
            MATCH (n:{word_type}_type:{corpus_name}) WHERE n.label = csvLine.label
            SET {new_properties}
        } IN TRANSACTIONS OF 3000 ROWS
        """

    else:
        import_statement = """
        LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
        CALL (csvLine) {{
            MATCH (n:{word_type}_type:{corpus_name}) WHERE n.label_insensitive = csvLine.label
            SET {new_properties}
        }} IN TRANSACTIONS OF 3000 ROWS
        """

    statement = import_statement.format(
        path=lex_path,
        corpus_name=corpus_context.cypher_safe_name,
        word_type=corpus_context.word_name,
        new_properties=properties,
    )
    corpus_context.execute_cypher(statement)
    for h, v in typed_data.items():
        try:
            corpus_context.execute_cypher(
                "CREATE INDEX FOR (n:%s) ON (n.%s)" % (corpus_context.word_name, h)
            )
        except neo4j.exceptions.ClientError as e:
            if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
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
    string_set_template = "n.{name} = csvLine.{name}"
    float_set_template = "n.{name} = toFloat(csvLine.{name})"
    int_set_template = "n.{name} = toInteger(csvLine.{name})"
    bool_set_template = (
        """n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)"""
    )
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
    properties = ",\n".join(properties)
    directory = corpus_context.config.temporary_directory("csv")
    path = os.path.join(directory, "feature_import.csv")

    # If on the Docker version, the files live in /site/proj
    if os.path.exists("/site/proj") and not path.startswith("/site/proj"):
        feat_path = "file:///site/proj/{}".format(make_path_safe(path))
    else:
        feat_path = "file:///{}".format(make_path_safe(path))

    import_statement = """
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    MATCH (n:{phone_type}_type:{corpus_name}) where n.label = csvLine.label
    SET {new_properties}"""

    statement = import_statement.format(
        path=feat_path,
        corpus_name=corpus_context.cypher_safe_name,
        phone_type=corpus_context.phone_name,
        new_properties=properties,
    )
    corpus_context.execute_cypher(statement)
    for h, v in typed_data.items():
        try:
            corpus_context.execute_cypher(
                "CREATE INDEX FOR (n:%s) ON (n.%s)" % (corpus_context.phone_name, h)
            )
        except neo4j.exceptions.ClientError as e:
            if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
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
    string_set_template = "n.{name} = csvLine.{name}"
    float_set_template = "n.{name} = toFloat(csvLine.{name})"
    int_set_template = "n.{name} = toInteger(csvLine.{name})"
    bool_set_template = (
        """n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)"""
    )
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
    properties = ",\n".join(properties)
    directory = corpus_context.config.temporary_directory("csv")
    path = os.path.join(directory, "syllable_import.csv")

    # If on the Docker version, the files live in /site/proj
    if os.path.exists("/site/proj") and not path.startswith("/site/proj"):
        syl_path = "file:///site/proj/{}".format(make_path_safe(path))
    else:
        syl_path = "file:///{}".format(make_path_safe(path))

    import_statement = """
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    MATCH (n:syllable_type:{corpus_name}) where n.label = csvLine.label
    SET {new_properties}"""

    statement = import_statement.format(
        path=syl_path,
        corpus_name=corpus_context.cypher_safe_name,
        phone_type="syllable",
        new_properties=properties,
    )
    corpus_context.execute_cypher(statement)
    for h, v in typed_data.items():
        try:
            corpus_context.execute_cypher("CREATE INDEX FOR (n:%s) ON (n.%s)" % ("syllable", h))
        except neo4j.exceptions.ClientError as e:
            if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
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
    string_set_template = "n.{name} = csvLine.{name}"
    float_set_template = "n.{name} = toFloat(csvLine.{name})"
    int_set_template = "n.{name} = toInteger(csvLine.{name})"
    bool_set_template = (
        """n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)"""
    )
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
    properties = ",\n".join(properties)
    directory = corpus_context.config.temporary_directory("csv")
    path = os.path.join(directory, "utterance_enrichment.csv")

    # If on the Docker version, the files live in /site/proj
    if os.path.exists("/site/proj") and not path.startswith("/site/proj"):
        utt_path = "file:///site/proj/{}".format(make_path_safe(path))
    else:
        utt_path = "file:///{}".format(make_path_safe(path))

    import_statement = """
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    MATCH (n:utterance:{corpus_name}) where n.id = csvLine.id
    SET {new_properties}"""

    statement = import_statement.format(
        path=utt_path,
        corpus_name=corpus_context.cypher_safe_name,
        phone_type="syllable",
        new_properties=properties,
    )
    corpus_context.execute_cypher(statement)
    for h, v in typed_data.items():
        try:
            corpus_context.execute_cypher("CREATE INDEX FOR (n:%s) ON (n.%s)" % ("utterance", h))
        except neo4j.exceptions.ClientError as e:
            if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
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
    string_set_template = "n.{name} = csvLine.{name}"
    float_set_template = "n.{name} = toFloat(csvLine.{name})"
    int_set_template = "n.{name} = toInteger(csvLine.{name})"
    bool_set_template = (
        """n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)"""
    )
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
    properties = ",\n".join(properties)
    directory = corpus_context.config.temporary_directory("csv")
    path = os.path.join(directory, "speaker_import.csv")

    # If on the Docker version, the files live in /site/proj
    if os.path.exists("/site/proj") and not path.startswith("/site/proj"):
        feat_path = "file:///site/proj/{}".format(make_path_safe(path))
    else:
        feat_path = "file:///{}".format(make_path_safe(path))

    import_statement = """
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    MATCH (n:Speaker:{corpus_name}) where n.name = toString(csvLine.name)
    SET {new_properties}"""

    statement = import_statement.format(
        path=feat_path,
        corpus_name=corpus_context.cypher_safe_name,
        new_properties=properties,
    )
    corpus_context.execute_cypher(statement)
    for h, v in typed_data.items():
        try:
            corpus_context.execute_cypher("CREATE INDEX FOR (s:Speaker) ON (s.%s)" % h)
        except neo4j.exceptions.ClientError as e:
            if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
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
    string_set_template = "n.{name} = csvLine.{name}"
    float_set_template = "n.{name} = toFloat(csvLine.{name})"
    int_set_template = "n.{name} = toInteger(csvLine.{name})"
    bool_set_template = (
        """n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)"""
    )
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
    properties = ",\n".join(properties)
    directory = corpus_context.config.temporary_directory("csv")
    path = os.path.join(directory, "discourse_import.csv")

    # If on the Docker version, the files live in /site/proj
    if os.path.exists("/site/proj") and not path.startswith("/site/proj"):
        feat_path = "file:///site/proj/{}".format(make_path_safe(path))
    else:
        feat_path = "file:///{}".format(make_path_safe(path))

    import_statement = """
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    MATCH (n:Discourse:{corpus_name}) where n.name = toString(csvLine.name)
    SET {new_properties}"""

    statement = import_statement.format(
        path=feat_path,
        corpus_name=corpus_context.cypher_safe_name,
        new_properties=properties,
    )
    corpus_context.execute_cypher(statement)
    for h, v in typed_data.items():
        try:
            corpus_context.execute_cypher("CREATE INDEX FOR (d:Discourse) ON (d.%s)" % h)
        except neo4j.exceptions.ClientError as e:
            if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
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
        call_back("Importing data...")
        call_back(0, len(speakers))
    try:
        corpus_context.execute_cypher(
            "CREATE CONSTRAINT FOR (node:utterance) REQUIRE node.id IS UNIQUE"
        )
    except neo4j.exceptions.ClientError as e:
        if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
            raise
    for i, s in enumerate(speakers):
        discourses = corpus_context.get_discourses_of_speaker(s)
        for d in discourses:
            if stop_check is not None and stop_check():
                return
            if call_back is not None:
                call_back(
                    "Importing data for speaker {} of {} ({})...".format(i, len(speakers), s)
                )
                call_back(i)

            path = os.path.join(
                corpus_context.config.temporary_directory("csv"),
                "{}_{}_utterance.csv".format(re.sub(r"\W", "_", s), d),
            )
            if corpus_context.config.debug:
                print(
                    "Importing utterances for speaker {} in discourse {}, using import file {}".format(
                        s, d, path
                    )
                )

            # If on the Docker version, the files live in /site/proj
            if os.path.exists("/site/proj") and not path.startswith("/site/proj"):
                csv_path = "file:///site/proj/{}".format(make_path_safe(path))
            else:
                csv_path = "file:///{}".format(make_path_safe(path))

            begin = time.time()
            node_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MATCH (begin:{word_type}:{corpus}:speech {{id: csvLine.begin_word_id}}),
                    (end:{word_type}:{corpus}:speech {{id: csvLine.end_word_id}})
                WITH csvLine, begin, end
                CREATE (utt:utterance:{corpus}:speech {{
                    id: csvLine.id,
                    begin: begin.begin,
                    end: end.end
                }})-[:is_a]->(u_type:utterance_type:{corpus})
            }} IN TRANSACTIONS OF 1000 ROWS
            """

            statement = node_statement.format(
                path=csv_path,
                corpus=corpus_context.cypher_safe_name,
                word_type=corpus_context.word_name,
            )
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print("Utterance node creation took {} seconds.".format(time.time() - begin))

            begin = time.time()
            rel_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MATCH (d:Discourse:{corpus})<-[:spoken_in]-(begin:{word_type}:{corpus}:speech {{id: csvLine.begin_word_id}})-[:spoken_by]->(s:Speaker:{corpus}),
                    (utt:utterance:{corpus}:speech {{id: csvLine.id}})
                CREATE
                    (d)<-[:spoken_in]-(utt),
                    (s)<-[:spoken_by]-(utt)
            }} IN TRANSACTIONS OF 1000 ROWS
            """

            statement = rel_statement.format(
                path=csv_path,
                corpus=corpus_context.cypher_safe_name,
                word_type=corpus_context.word_name,
            )
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print("Spoken relationship creation took {} seconds.".format(time.time() - begin))

            begin = time.time()
            rel_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MATCH (begin:{word_type}:{corpus}:speech {{id: csvLine.begin_word_id}}),
                    (utt:utterance:{corpus}:speech {{id: csvLine.id}}),
                    (prev:utterance {{id: csvLine.prev_id}})
                CREATE (prev)-[:precedes]->(utt)
            }} IN TRANSACTIONS OF 1000 ROWS
            """
            statement = rel_statement.format(
                path=csv_path,
                corpus=corpus_context.cypher_safe_name,
                word_type=corpus_context.word_name,
            )
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print(
                    "Precedence relationship creation took {} seconds.".format(time.time() - begin)
                )

            begin = time.time()
            word_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MATCH (begin:{word_type}:{corpus}:speech {{id: csvLine.begin_word_id}}),
                    (utt:utterance:{corpus}:speech {{id: csvLine.id}}),
                    (end:{word_type}:{corpus}:speech {{id: csvLine.end_word_id}}),
                    path = shortestPath((begin)-[:precedes*0..]->(end))
                WITH utt, nodes(path) AS words
                UNWIND words AS w
                CREATE (w)-[:contained_by]->(utt)
            }} IN TRANSACTIONS OF 1000 ROWS
            """
            statement = word_statement.format(
                path=csv_path,
                corpus=corpus_context.cypher_safe_name,
                word_type=corpus_context.word_name,
            )
            corpus_context.execute_cypher(statement)
            word_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MATCH (n)-[:contained_by*]->()-[:contained_by]->(utt:utterance:{corpus}:speech {{id: csvLine.id}})
                WITH utt, collect(n) AS subunits
                UNWIND subunits AS w
                CREATE (w)-[:contained_by]->(utt)
            }} IN TRANSACTIONS OF 1000 ROWS
            """
            statement = word_statement.format(
                path=csv_path,
                corpus=corpus_context.cypher_safe_name,
                word_type=corpus_context.word_name,
            )
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print(
                    "Hierarchical relationship creation took {} seconds.".format(
                        time.time() - begin
                    )
                )
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
        call_back("Importing syllables...")
        call_back(0, len(speakers))
    try:
        corpus_context.execute_cypher(
            "CREATE CONSTRAINT FOR (node:syllable) REQUIRE node.id IS UNIQUE"
        )
    except neo4j.exceptions.ClientError as e:
        if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
            raise
    try:
        corpus_context.execute_cypher(
            "CREATE CONSTRAINT FOR (node:syllable_type) REQUIRE node.id IS UNIQUE"
        )
    except neo4j.exceptions.ClientError as e:
        if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
            raise
    try:
        corpus_context.execute_cypher("CREATE INDEX FOR (s:syllable) ON (s.begin)")
    except neo4j.exceptions.ClientError as e:
        if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
            raise
    try:
        corpus_context.execute_cypher("CREATE INDEX FOR (s:syllable) ON (s.prev_id)")
    except neo4j.exceptions.ClientError as e:
        if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
            raise
    try:
        corpus_context.execute_cypher("CREATE INDEX FOR (s:syllable) ON (s.end)")
    except neo4j.exceptions.ClientError as e:
        if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
            raise
    try:
        corpus_context.execute_cypher("CREATE INDEX FOR (s:syllable) ON (s.label)")
    except neo4j.exceptions.ClientError as e:
        if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
            raise
    try:
        corpus_context.execute_cypher("CREATE INDEX FOR (s:syllable_type) ON (s.label)")
    except neo4j.exceptions.ClientError as e:
        if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
            raise
    for i, s in enumerate(speakers):
        if stop_check is not None and stop_check():
            return
        if call_back is not None:
            call_back(
                "Importing syllables for speaker {} of {} ({})...".format(i, len(speakers), s)
            )
            call_back(i)
        discourses = corpus_context.get_discourses_of_speaker(s)
        for d in discourses:
            path = os.path.join(
                corpus_context.config.temporary_directory("csv"),
                "{}_{}_syllable.csv".format(re.sub(r"\W", "_", s), d),
            )
            if corpus_context.config.debug:
                print(
                    "Importing syllables for speaker {} in discourse {}, using import file {}".format(
                        s, d, path
                    )
                )
            # If on the Docker version, the files live in /site/proj
            if os.path.exists("/site/proj") and not path.startswith("/site/proj"):
                csv_path = "file:///site/proj/{}".format(make_path_safe(path))
            else:
                csv_path = "file:///{}".format(make_path_safe(path))

            begin = time.time()
            nucleus_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MATCH (n:{phone_name}:{corpus}:speech {{id: csvLine.vowel_id}})-[r:contained_by]->(w:{word_name}:{corpus}:speech)
                SET n :nucleus, n.syllable_position = 'nucleus'
            }} IN TRANSACTIONS OF 2000 ROWS
            """
            statement = nucleus_statement.format(
                path=csv_path,
                corpus=corpus_context.cypher_safe_name,
                word_name=corpus_context.word_name,
                phone_name=corpus_context.phone_name,
            )
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print("Nucleus definition took {} seconds.".format(time.time() - begin))

            begin = time.time()
            node_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MERGE (s_type:syllable_type:{corpus} {{id: csvLine.type_id}})
                ON CREATE SET s_type.label = csvLine.label
                WITH s_type, csvLine
                CREATE (s:syllable:{corpus}:speech {{
                    id: csvLine.id,
                    prev_id: csvLine.prev_id,
                    label: csvLine.label,
                    begin: toFloat(csvLine.begin),
                    end: toFloat(csvLine.end)
                }}),
                (s)-[:is_a]->(s_type)
            }} IN TRANSACTIONS OF 2000 ROWS
            """
            statement = node_statement.format(
                path=csv_path, corpus=corpus_context.cypher_safe_name
            )
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print("Syllable node creation took {} seconds.".format(time.time() - begin))

            begin = time.time()
            rel_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MATCH (n:{phone_name}:{corpus}:speech:nucleus {{id: csvLine.vowel_id}})-[:contained_by]->(w:{word_name}:{corpus}:speech),
                    (s:syllable:{corpus}:speech {{id: csvLine.id}})
                WITH n, w, s
                CREATE (s)-[:contained_by]->(w),
                    (n)-[:contained_by]->(s)
            }} IN TRANSACTIONS OF 2000 ROWS
            """
            statement = rel_statement.format(
                path=csv_path,
                corpus=corpus_context.cypher_safe_name,
                word_name=corpus_context.word_name,
                phone_name=corpus_context.phone_name,
            )
            corpus_context.execute_cypher(statement)
            rel_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MATCH (s:syllable:{corpus}:speech {{id: csvLine.id}})-[:contained_by]->(w:{word_name}:{corpus}:speech),
                    (w)-[:contained_by]->(n)
                WITH s, collect(n) as superunits
                UNWIND superunits AS u
                CREATE (s)-[:contained_by]->(u)
            }} IN TRANSACTIONS OF 2000 ROWS
            """
            statement = rel_statement.format(
                path=csv_path,
                corpus=corpus_context.cypher_safe_name,
                word_name=corpus_context.word_name,
                phone_name=corpus_context.phone_name,
            )
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print(
                    "Hierarchical relationship creation took {} seconds.".format(
                        time.time() - begin
                    )
                )

            begin = time.time()
            rel_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MATCH (n:{phone_name}:{corpus}:speech:nucleus {{id: csvLine.vowel_id}}),
                    (s:syllable:{corpus}:speech {{id: csvLine.id}}),
                    (n)-[:spoken_by]->(sp:Speaker),
                    (n)-[:spoken_in]->(d:Discourse)
                WITH sp, d, s
                CREATE (s)-[:spoken_by]->(sp),
                    (s)-[:spoken_in]->(d)
            }} IN TRANSACTIONS OF 2000 ROWS
            """
            statement = rel_statement.format(
                path=csv_path,
                corpus=corpus_context.cypher_safe_name,
                word_name=corpus_context.word_name,
                phone_name=corpus_context.phone_name,
            )
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print("Spoken relationship creation took {} seconds.".format(time.time() - begin))

            begin = time.time()
            prev_rel_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MATCH (s:syllable:{corpus}:speech {{id: csvLine.id}})
                WITH csvLine, s
                MATCH (prev:syllable {{id: csvLine.prev_id}})
                CREATE (prev)-[:precedes]->(s)
            }} IN TRANSACTIONS OF 2000 ROWS
            """
            statement = prev_rel_statement.format(
                path=csv_path,
                corpus=corpus_context.cypher_safe_name,
                word_name=corpus_context.word_name,
                phone_name=corpus_context.phone_name,
            )
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print(
                    "Precedence relationship creation took {} seconds.".format(time.time() - begin)
                )

            begin = time.time()
            onset_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MATCH (n:{phone_name}:nucleus:{corpus}:speech)-[:contained_by]->(s:syllable:{corpus}:speech {{id: csvLine.id}})-[:contained_by]->(w:{word_name}:{corpus}:speech)
                WITH csvLine, s, w, n
                OPTIONAL MATCH
                    (onset:{phone_name}:{corpus} {{id: csvLine.onset_id}}),
                    onspath = (onset)-[:precedes*1..10]->(n)
                WITH n, w, s, csvLine, onspath
                UNWIND (CASE WHEN onspath IS NOT NULL THEN nodes(onspath)[0..-1] ELSE [NULL] END) AS o
                WITH n, s, csvLine, [x IN collect(o) WHERE x IS NOT NULL | x] AS ons
                FOREACH (o IN ons | SET o :onset, o.syllable_position = 'onset')
                FOREACH (o IN ons | CREATE (o)-[:contained_by]->(s))
            }} IN TRANSACTIONS OF 2000 ROWS
            """
            statement = onset_statement.format(
                path=csv_path,
                corpus=corpus_context.cypher_safe_name,
                word_name=corpus_context.word_name,
                phone_name=corpus_context.phone_name,
            )
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print(
                    "Onset hierarchical relationship creation took {} seconds.".format(
                        time.time() - begin
                    )
                )

            begin = time.time()
            coda_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MATCH (n:nucleus:{corpus}:speech)-[:contained_by]->(s:syllable:{corpus}:speech {{id: csvLine.id}})-[:contained_by]->(w:{word_name}:{corpus}:speech)
                WITH csvLine, s, w, n
                OPTIONAL MATCH
                    (coda:{phone_name}:{corpus} {{id: csvLine.coda_id}}),
                    codapath = (n)-[:precedes*1..10]->(coda)
                WITH n, w, s, codapath
                UNWIND (CASE WHEN codapath IS NOT NULL THEN nodes(codapath)[1..] ELSE [NULL] END) AS c
                WITH n, s, [x IN collect(c) WHERE x IS NOT NULL | x] AS cod
                FOREACH (c IN cod | SET c :coda, c.syllable_position = 'coda')
                FOREACH (c IN cod | CREATE (c)-[:contained_by]->(s))
            }} IN TRANSACTIONS OF 2000 ROWS
            """
            statement = coda_statement.format(
                path=csv_path,
                corpus=corpus_context.cypher_safe_name,
                word_name=corpus_context.word_name,
                phone_name=corpus_context.phone_name,
            )
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print(
                    "Coda hierarchical relationship creation took {} seconds.".format(
                        time.time() - begin
                    )
                )
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
        call_back("Importing degenerate syllables...")
        call_back(0, len(speakers))
    try:
        corpus_context.execute_cypher(
            "CREATE CONSTRAINT FOR (node:syllable) REQUIRE node.id IS UNIQUE"
        )
    except neo4j.exceptions.ClientError as e:
        if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
            raise
    try:
        corpus_context.execute_cypher(
            "CREATE CONSTRAINT FOR (node:syllable_type) REQUIRE node.id IS UNIQUE"
        )
    except neo4j.exceptions.ClientError as e:
        if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
            raise
    try:
        corpus_context.execute_cypher("CREATE INDEX FOR (s:syllable) ON (s.begin)")
    except neo4j.exceptions.ClientError as e:
        if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
            raise
    try:
        corpus_context.execute_cypher("CREATE INDEX FOR (s:syllable) ON (s.end)")
    except neo4j.exceptions.ClientError as e:
        if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
            raise
    try:
        corpus_context.execute_cypher("CREATE INDEX FOR (s:syllable) ON (s.label)")
    except neo4j.exceptions.ClientError as e:
        if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
            raise
    try:
        corpus_context.execute_cypher("CREATE INDEX FOR (s:syllable_type) ON (s.label)")
    except neo4j.exceptions.ClientError as e:
        if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
            raise
    for i, s in enumerate(speakers):
        if stop_check is not None and stop_check():
            return
        if call_back is not None:
            call_back(
                "Importing degenerate syllables for speaker {} of {} ({})...".format(
                    i, len(speakers), s
                )
            )
            call_back(i)
        discourses = corpus_context.get_discourses_of_speaker(s)
        for d in discourses:
            path = os.path.join(
                corpus_context.config.temporary_directory("csv"),
                "{}_{}_nonsyl.csv".format(re.sub(r"\W", "_", s), d),
            )

            if corpus_context.config.debug:
                print(
                    "Importing degenerate syllables for speaker {} in discourse {}, using import file {}".format(
                        s, d, path
                    )
                )
            # If on the Docker version, the files live in /site/proj
            if os.path.exists("/site/proj") and not path.startswith("/site/proj"):
                csv_path = "file:///site/proj/{}".format(make_path_safe(path))
            else:
                csv_path = "file:///{}".format(make_path_safe(path))

            begin = time.time()
            node_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MERGE (s_type:syllable_type:{corpus} {{id: csvLine.type_id}})
                ON CREATE SET s_type.label = csvLine.label
                WITH s_type, csvLine
                CREATE (s:syllable:{corpus}:speech {{
                    id: csvLine.id,
                    prev_id: csvLine.prev_id,
                    begin: toFloat(csvLine.begin),
                    end: toFloat(csvLine.end),
                    label: csvLine.label
                }}),
                (s)-[:is_a]->(s_type)
            }} IN TRANSACTIONS OF 2000 ROWS
            """

            statement = node_statement.format(
                path=csv_path, corpus=corpus_context.cypher_safe_name
            )
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print("Syllable node creation took {} seconds.".format(time.time() - begin))

            begin = time.time()
            rel_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MATCH (o:{phone_name}:{corpus}:speech {{id: csvLine.onset_id}})-[r:contained_by]->(w:{word_name}:{corpus}:speech),
                    (o)-[:spoken_by]->(sp:Speaker),
                    (o)-[:spoken_in]->(d:Discourse),
                    (s:syllable:{corpus}:speech {{id: csvLine.id}})
                WITH w, csvLine, sp, d, s
                CREATE (s)-[:contained_by]->(w),
                    (s)-[:spoken_by]->(sp),
                    (s)-[:spoken_in]->(d)
            }} IN TRANSACTIONS OF 2000 ROWS
            """
            statement = rel_statement.format(
                path=csv_path,
                corpus=corpus_context.cypher_safe_name,
                word_name=corpus_context.word_name,
                phone_name=corpus_context.phone_name,
            )
            corpus_context.execute_cypher(statement)
            rel_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MATCH (s:syllable:{corpus}:speech {{id: csvLine.id}})-[:contained_by]->(w:{word_name}:{corpus}:speech),
                    (w)-[:contained_by]->(n)
                WITH s, collect(n) as superunits
                UNWIND superunits AS u
                CREATE (s)-[:contained_by]->(u)
            }} IN TRANSACTIONS OF 2000 ROWS
            """
            statement = rel_statement.format(
                path=csv_path,
                corpus=corpus_context.cypher_safe_name,
                word_name=corpus_context.word_name,
                phone_name=corpus_context.phone_name,
            )
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print(
                    "Hierarchical and spoken relationship creation took {} seconds.".format(
                        time.time() - begin
                    )
                )

            begin = time.time()
            rel_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MATCH (s:syllable:{corpus}:speech {{id: csvLine.id}})
                with csvLine, s
                MATCH (prev:syllable {{id:csvLine.prev_id}})
                CREATE (prev)-[:precedes]->(s)
            }} IN TRANSACTIONS OF 2000 ROWS
            """
            statement = rel_statement.format(
                path=csv_path,
                corpus=corpus_context.cypher_safe_name,
                word_name=corpus_context.word_name,
                phone_name=corpus_context.phone_name,
            )
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print(
                    "First precedence relationship creation took {} seconds.".format(
                        time.time() - begin
                    )
                )

            begin = time.time()
            rel_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MATCH (s:syllable:{corpus}:speech {{id: csvLine.id}})
                with csvLine, s
                MATCH (foll:syllable {{prev_id:csvLine.id}})
                CREATE (s)-[:precedes]->(foll)
            }} IN TRANSACTIONS OF 2000 ROWS
            """
            statement = rel_statement.format(
                path=csv_path,
                corpus=corpus_context.cypher_safe_name,
                word_name=corpus_context.word_name,
                phone_name=corpus_context.phone_name,
            )
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print(
                    "Second precedence relationship creation took {} seconds.".format(
                        time.time() - begin
                    )
                )

            begin = time.time()
            phone_statement = """
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            CALL (csvLine) {{
                MATCH (o:{phone_name}:{corpus}:speech {{id: csvLine.onset_id}}),
                    (s:syllable:{corpus}:speech {{id: csvLine.id}})-[:contained_by]->(w:{word_name}:{corpus}:speech)
                WITH o, w, csvLine, s
                OPTIONAL MATCH
                    (c:{phone_name}:{corpus}:speech {{id: csvLine.coda_id}})-[:contained_by]->(w),
                    p = (o)-[:precedes*..10]->(c)
                WITH o, w, s, p, csvLine
                UNWIND (CASE WHEN p IS NOT NULL THEN nodes(p) ELSE [o] END) AS c
                WITH s, toInteger(csvLine.break) AS break, [x IN collect(c) WHERE x IS NOT NULL | x] AS cod
                FOREACH (c IN cod[break..] | SET c :coda, c.syllable_position = 'coda')
                FOREACH (c IN cod[..break] | SET c :onset, c.syllable_position = 'onset')
                FOREACH (c IN cod | CREATE (c)-[:contained_by]->(s))
            }} IN TRANSACTIONS OF 2000 ROWS
            """
            statement = phone_statement.format(
                path=csv_path,
                corpus=corpus_context.cypher_safe_name,
                word_name=corpus_context.word_name,
                phone_name=corpus_context.phone_name,
            )
            corpus_context.execute_cypher(statement)
            if corpus_context.config.debug:
                print(
                    "Onset/coda hierarchical relationship creation took {} seconds.".format(
                        time.time() - begin
                    )
                )
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
    path = os.path.join(
        corpus_context.config.temporary_directory("csv"),
        "{}_subannotations.csv".format(type),
    )

    # If on the Docker version, the files live in /site/proj
    if os.path.exists("/site/proj") and not path.startswith("/site/proj"):
        csv_path = "file:///site/proj/{}".format(make_path_safe(path))
    else:
        csv_path = "file:///{}".format(make_path_safe(path))

    prop_temp = """{name}: csvLine.{name}"""
    properties = []
    try:
        corpus_context.execute_cypher(
            "CREATE CONSTRAINT FOR (node:%s) REQUIRE node.id IS UNIQUE" % type
        )
    except neo4j.exceptions.ClientError as e:
        if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
            raise

    for p in props:
        if p in ["id", "annotated_id", "begin", "end"]:
            continue
        properties.append(prop_temp.format(name=p))
    if properties:
        properties = ", " + ", ".join(properties)
    else:
        properties = ""
    statement = """
        LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
        CALL (csvLine) {{
        MATCH (annotated:{a_type}:{corpus} {{id: csvLine.annotated_id}})
        CREATE (annotated) <-[:annotates]-(annotation:{type}:{corpus} {{
            id: csvLine.id,
            type: $type,
            begin: toFloat(csvLine.begin),
            end: toFloat(csvLine.end){properties}
        }})
    }} IN TRANSACTIONS OF 500 ROWS
    """
    statement = statement.format(
        path=csv_path,
        corpus=corpus_context.cypher_safe_name,
        a_type=annotated_type,
        type=type,
        properties=properties,
    )
    corpus_context.execute_cypher(statement, type=type)
    for p in props:
        if p in ["id", "annotated_id"]:
            continue
        try:
            corpus_context.execute_cypher("CREATE INDEX FOR (n:%s) ON (n.%s)" % (type, p))
        except neo4j.exceptions.ClientError as e:
            if e.code != "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
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
        with open(path, "r") as f:
            properties = [x.strip() for x in f.readline().split(",") if x.strip() != id_column]

    is_subann = annotated_type not in corpus_context.hierarchy.annotation_types

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
            corpus_context.hierarchy.add_subannotation_properties(
                corpus_context, annotated_type, props_to_add
            )
        else:
            corpus_context.hierarchy.add_token_properties(
                corpus_context, annotated_type, props_to_add
            )
        corpus_context.encode_hierarchy()

    type_map = _infer_csv_types(path, 30)

    type_functions = {
        "int": "toInteger",
        "float": "toFloat",
        "bool": "toBoolean",
        "date": "date",
        "datetime": "datetime",
        "string": "",
    }

    property_update = ", ".join(
        [
            "x.{p} = {func}(csvLine.{p})".format(
                p=p, func=type_functions.get(type_map.get(p, "string"), "")
            )
            if type_map.get(p, "string") != "string"
            else "x.{p} = csvLine.{p}".format(p=p)
            for p in properties
        ]
    )

    statement = """
    LOAD CSV WITH HEADERS FROM "file://{path}" AS csvLine
    CALL (csvLine) {{
        MATCH (x:{a_type}:{corpus} {{id: csvLine.{id_column}}})
        SET {property_update}
    }} IN TRANSACTIONS OF 500 ROWS
    """.format(
        path=path,
        a_type=annotated_type,
        corpus=corpus_context.cypher_safe_name,
        id_column=id_column,
        property_update=property_update,
    )
    corpus_context.execute_cypher(statement)
    os.remove(path)


def _infer_csv_types(path, sample_size=10):
    """
    Reads a sample of the CSV file and infers column types (integer, float, boolean, string only)
    """
    type_map = {}

    with open(path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        sample_rows = []

        for _ in range(sample_size):
            try:
                sample_rows.append(next(reader))
            except StopIteration:
                break

        if not sample_rows:
            return {}

    column_data = {key: [] for key in sample_rows[0].keys()}

    for row in sample_rows:
        for key, value in row.items():
            column_data[key].append(value.strip())

    for key, values in column_data.items():
        np_values = np.array(values, dtype=str)

        if np.all(np.char.lower(np_values) == "true") or np.all(
            np.char.lower(np_values) == "false"
        ):
            inferred_type = "bool"
        elif np.all(np.char.isnumeric(np_values)):
            inferred_type = "int"
        else:
            try:
                np.array(np_values, dtype=float)
                inferred_type = "float"
            except ValueError:
                inferred_type = "string"

        type_map[key] = inferred_type

    return type_map


def import_token_csv_with_timestamp(
    corpus_context,
    path,
    annotated_type,
    timestamp_column,
    discourse_column,
    properties=None,
):
    """
    Adds new properties to a list of tokens of a given type based on timestamp and discourse matching.

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.AnnotatedContext`
        The corpus to load into.
    path : str
        The file name of the CSV.
    annotated_type : str
        The type of the tokens that are being updated.
    timestamp_column : str
        The header name for the column containing timestamps.
    discourse_column : str
        The header name for the column containing discourse names.
    properties : list
        A list of column names to update; if None, assume all columns will be updated (default).
    """

    # If on the Docker version, the files live in /site/proj
    if os.path.exists("/site/proj") and not path.startswith("/site/proj"):
        csv_path = "file:///site/proj/{}".format(make_path_safe(path))
    else:
        csv_path = "file:///{}".format(make_path_safe(path))
    if properties is None:
        with open(path, "r") as f:
            properties = [
                x.strip()
                for x in f.readline().split(",")
                if x.strip() not in [timestamp_column, discourse_column]
            ]

    if annotated_type not in corpus_context.hierarchy.annotation_types:
        raise KeyError("Annotation type {} does not exist in this corpus".format(annotated_type))

    props_to_add = []
    for p in properties:
        if not corpus_context.hierarchy.has_token_property(annotated_type, p):
            props_to_add.append((p, str))

    if props_to_add:
        corpus_context.hierarchy.add_token_properties(corpus_context, annotated_type, props_to_add)
        corpus_context.encode_hierarchy()

    type_map = _infer_csv_types(path, 30)

    type_functions = {
        "int": "toInteger",
        "float": "toFloat",
        "bool": "toBoolean",
        "date": "date",
        "datetime": "datetime",
        "string": "",
    }

    property_update = ", ".join(
        [
            "x.{p} = {func}(csvLine.{p})".format(
                p=p, func=type_functions.get(type_map.get(p, "string"), "")
            )
            if type_map.get(p, "string") != "string"
            else "x.{p} = csvLine.{p}".format(p=p)
            for p in properties
        ]
    )

    statement = """
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
    CALL (csvLine) {{
        MATCH (d:Discourse {{name: csvLine.{discourse_column}}})
        MATCH (x:{a_type}:{corpus})-[:spoken_in]->(d)
        WHERE x.begin <= toFloat(csvLine.{timestamp_column}) <= x.end
        SET {property_update}
    }} IN TRANSACTIONS OF 500 ROWS
    """.format(
        path=csv_path,
        a_type=annotated_type,
        corpus=corpus_context.cypher_safe_name,
        timestamp_column=timestamp_column,
        discourse_column=discourse_column,
        property_update=property_update,
    )

    corpus_context.execute_cypher(statement)


def import_track_csv(corpus_context, acoustic_name, path, properties):
    """
    Reads a CSV file containing measurement tracks, and saves each track using the _save_measurement API.

    Parameters:
    corpus_context : object
        The corpus context for accessing the database and helper methods.
    acoustic_name : str
        The name of the acoustic measure.
    path : str
        Path to the CSV file containing the measurement data.
    properties : list
        list of properties to read from the csv
    """
    if acoustic_name not in corpus_context.hierarchy.acoustics:
        corpus_context.hierarchy.add_acoustic_properties(
            corpus_context, acoustic_name, [(p, float) for p in properties]
        )
        corpus_context.encode_hierarchy()
    with open(path, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        discourse = os.path.splitext(os.path.basename(path))[0]
        for row in reader:
            time = float(row["time"])

            track = {}

            measurements = {}
            for p in properties:
                measurements[p] = float(row[p])

            track[time] = measurements
            corpus_context._save_measurement(discourse, track, acoustic_name)


def import_track_csvs(self, acoustic_name, directory_path, properties):
    """
    Reads a directory of CSV files containing measurement tracks, identifies the corresponding utterance,
    and saves each track using the _save_measurement_tracks API.

    Parameters
    corpus_context : object
        The corpus context for accessing the database and helper methods.
    acoustic_name : str
        The name of the acoustic measure.
    directory_path : str
        Path to the CSV file containing the measurement data.
    properties : list
        list of properties to read from the csv
    """
    directory_path = os.path.expanduser(directory_path)
    for file_name in os.listdir(directory_path):
        if file_name.endswith(".csv"):
            full_path = os.path.join(directory_path, file_name)
            import_track_csv(self, acoustic_name, full_path, properties)
