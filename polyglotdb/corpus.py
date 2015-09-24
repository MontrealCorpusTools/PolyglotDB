import os
import re
import shutil
from py2neo import Graph
from collections import defaultdict


from .io.graph import data_to_graph_csvs

from .graph.query import GraphQuery
from .graph.attributes import AnnotationAttribute

from .sql.models import Base, Word, WordProperty, WordPropertyType, InventoryItem, AnnotationType, SoundFile

from sqlalchemy import create_engine

from .sql.config import Session, session_scope

from .sql.helper import get_or_create

from .sql.query import Lexicon

class CorpusContext(object):
    def __init__(self, user, password, corpus_name, host = 'localhost', port = 7474):
        self.graph = Graph("http://{}:{}@{}:{}/db/data/".format(user, password, host, port))
        self.corpus_name = corpus_name
        self.base_dir = os.path.join(os.path.expanduser('~/Documents/SCT'), self.corpus_name)

        self.log_dir = os.path.join(self.base_dir, 'logs')
        os.makedirs(self.log_dir, exist_ok = True)

        self.temp_dir = os.path.join(self.base_dir, 'temp')
        os.makedirs(self.temp_dir, exist_ok = True)

        self.data_dir = os.path.join(self.base_dir, 'data')
        os.makedirs(self.data_dir, exist_ok = True)

        db_path = os.path.join(self.data_dir, self.corpus_name)
        engine_string = 'sqlite:///{}.db'.format(db_path)
        self.engine = create_engine(engine_string)
        Session.configure(bind=self.engine)
        if not os.path.exists(db_path):
            Base.metadata.create_all(self.engine)

        self.relationship_types = self.lookup_relationship_types()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        if exc_type is None:
            shutil.rmtree(self.temp_dir)
            return True

    def __getattr__(self, key):
        if key in self.relationship_types:
            return AnnotationAttribute(key)
        if key == 'lexicon':
            return Lexicon()
        elif key == 'inventory':
            return {}
        return getattr(self, key)

    def lookup_relationship_types(self):
        cypher = '''MATCH (n)-[r]->()
                    WHERE n.corpus = '%s'
                    RETURN DISTINCT type(r) AS relationship_type''' % self.corpus_name
        results = self.graph.cypher.execute(cypher)
        return [x['relationship_type'] for x in results]

    def reset_graph(self):
        self.graph.cypher.execute('''MATCH (n {corpus: '%s'})-[r]->() DELETE n, r''' % self.corpus_name)

    def reset(self):
        self.reset_graph()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def remove_discourse(self, name):
        self.graph.cypher.execute('''MATCH (n {corpus: '%s', discourse: '%s'})-[r]->() DELETE n, r'''
                                    % (self.corpus_name, name))

    def query_graph(self, annotation_type):
        if annotation_type.name not in self.relationship_types:
            raise(AttributeError('The graph does not have any annotations of type \'{}\''.format(annotation_type.name)))
        return GraphQuery(self, annotation_type)

    def import_csvs(self, name, annotation_types, token_properties):
        node_path = 'file:{}'.format(os.path.join(self.temp_dir, '{}_nodes.csv'.format(name)).replace('\\','/'))

        node_import_statement = '''LOAD CSV WITH HEADERS FROM "%s" AS csvLine
CREATE (n:Anchor { id: toInt(csvLine.id),
time: toFloat(csvLine.time), label: csvLine.label, corpus: csvLine.corpus,
discourse: csvLine.discourse })'''
        self.graph.cypher.execute(node_import_statement % node_path)
        self.graph.cypher.execute('CREATE INDEX ON :Anchor(corpus)')
        self.graph.cypher.execute('CREATE INDEX ON :Anchor(discourse)')
        self.graph.cypher.execute('CREATE CONSTRAINT ON (node:Anchor) ASSERT node.id IS UNIQUE')
        self.graph.cypher.execute('CREATE CONSTRAINT ON (node:Anchor) ASSERT node.label IS UNIQUE')

        for at in annotation_types:
            rel_path = 'file:{}'.format(os.path.join(self.temp_dir, '{}_{}.csv'.format(name, at)).replace('\\','/'))

            if at == 'word':
                token_temp = '''{name}: csvLine.{name}'''
                properties = []
                for x in token_properties:
                    properties.append(token_temp.format(name=x))
                if properties:
                    prop_string = ', ' + ', '.join(properties)
                else:
                    prop_string = ''
                rel_import_statement = '''USING PERIODIC COMMIT 1000
    LOAD CSV WITH HEADERS FROM "%%s" AS csvLine
    MATCH (begin_node:Anchor { id: toInt(csvLine.from_id)}),(end_node:Anchor { id: toInt(csvLine.to_id)})
    CREATE (begin_node)-[:%%s { label: csvLine.label%s, id: csvLine.id }]->(end_node)''' % prop_string
            else:
                rel_import_statement = '''USING PERIODIC COMMIT 1000
    LOAD CSV WITH HEADERS FROM "%s" AS csvLine
    MATCH (begin_node:Anchor { id: toInt(csvLine.from_id)}),(end_node:Anchor { id: toInt(csvLine.to_id)})
    CREATE (begin_node)-[:%s { label: csvLine.label, id: csvLine.id }]->(end_node)'''
            self.graph.cypher.execute(rel_import_statement % (rel_path,at))
            self.graph.cypher.execute('CREATE INDEX ON :%s(label)' % at)
            if at == 'word':
                for x in token_properties:
                    self.graph.cypher.execute('CREATE INDEX ON :%s(%s)' % (at,x))
        self.graph.cypher.execute('DROP CONSTRAINT ON (node:Anchor) ASSERT node.id IS UNIQUE')
        self.graph.cypher.execute('''MATCH (n)
                                    WHERE n:Anchor
                                    REMOVE n.id''')

    def add_discourse(self, data):
        data.corpus_name = self.corpus_name
        data_to_graph_csvs(data, self.temp_dir)
        token_properties = data.token_properties
        if 'transcription' in data and not data['transcription'].base:
            token_properties.append('transcription')
        self.import_csvs(data.name, data.output_types, token_properties)
        self.relationship_types = self.lookup_relationship_types()
        self.update_sql_database(data)

    def update_sql_database(self, data):
        word_property_types = {}
        annotation_types = {}
        inventory_items = defaultdict(dict)
        words = {}
        with session_scope() as session:
            transcription_type, _ =  get_or_create(session, AnnotationType, label = 'transcription')
            base_levels = data.base_levels
            for i, level in enumerate(data.process_order):
                for d in data[level]:
                    if i != 0:
                        continue
                    trans = None
                    if len(base_levels) > 0:
                        b = base_levels[0]
                        if b not in annotation_types:
                            base_type, _ = get_or_create(session, AnnotationType, label = b)
                            annotation_types[b] = base_type
                        else:
                            base_type = annotation_types[b]
                        begin, end = d[b]
                        base_sequence = data[b][begin:end]
                        for j, first in enumerate(base_sequence):
                            if first.label not in inventory_items[b]:
                                p, _ = get_or_create(session, InventoryItem, label = first.label, annotation_type = base_type)
                                inventory_items[b][first.label] = p
                        if 'transcription' in d.additional:
                            trans = d.additional['transcription']
                        elif not data[b].token:
                            trans = [x.label for x in base_sequence]
                    if trans is None:
                        trans = ''
                    elif isinstance(trans, list):
                        for seg in trans:
                            if seg not in inventory_items['transcription']:
                                p, _ = get_or_create(session, InventoryItem, label = seg, annotation_type = transcription_type)
                                inventory_items['transcription'][seg] = p
                        trans = '.'.join(trans)
                    else:
                        print(trans)
                        raise(ValueError)
                    if (d.label, trans) not in words:
                        word,_ = get_or_create(session, Word, defaults = {'frequency':0}, orthography = d.label, transcription = trans)
                        words[(d.label, trans)] = word
                    else:
                        word = words[(d.label, trans)]
                    word.frequency += 1
                    for k,v in d.additional.items():
                        if v is None:
                            continue
                        if k not in word_property_types:

                            prop_type, _ = get_or_create(session, WordPropertyType, label = k)
                            word_property_types[k] = prop_type
                        else:
                            prop_type = word_property_types[k]
                        if isinstance(v, (int,float)):
                            prop, _ = get_or_create(session, WordNumericProperty, word = word, property_type = prop_type, value = v)
                        elif isinstance(v, (list, tuple)):
                            prop, _ = get_or_create(session, WordProperty, word = word, property_type = prop_type, value = '.'.join(v))
                        else:
                            prop, _ = get_or_create(session, WordProperty, word = word, property_type = prop_type, value = v)
            session.commit()


