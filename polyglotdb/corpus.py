import os
import re
import shutil
import pickle
import logging
import time
from collections import defaultdict

from py2neo import Graph
from py2neo.packages.httpstream import http
http.socket_timeout = 9999

from .config import CorpusConfig

from .io.graph import data_to_graph_csvs, import_csvs

from .graph.query import GraphQuery
from .graph.attributes import AnnotationAttribute

from .sql.models import (Base, Word, WordProperty, WordPropertyType,
                    InventoryItem, AnnotationType, SoundFile, Discourse)

from sqlalchemy import create_engine

from .sql.config import Session

from .sql.helper import get_or_create

from .sql.query import Lexicon, Inventory

from .graph.cypher import discourse_query

from .acoustics.io import add_acoustic_info

from .acoustics import acoustic_analysis

from .acoustics.query import AcousticQuery

from .exceptions import NoSoundFileError, CorpusConfigError, GraphQueryError

class CorpusContext(object):
    def __init__(self, *args, **kwargs):
        if len(args) == 0:
            raise(CorpusConfigError('Need to specify a corpus name or CorpusConfig.'))
        if isinstance(args[0], CorpusConfig):
            self.config = args[0]
        else:
            self.config = CorpusConfig(*args, **kwargs)
        self.config.init()
        self.graph = Graph(self.config.graph_connection_string)
        self.corpus_name = self.config.corpus_name

        self.engine = create_engine(self.config.sql_connection_string)
        Session.configure(bind=self.engine)
        if not os.path.exists(self.config.db_path):
            Base.metadata.create_all(self.engine)

        self.relationship_types = set()
        self.is_timed = False
        self.hierarchy = {}
        self._has_sound_files = None

        self.lexicon = Lexicon(self)

        self.inventory = Inventory(self)

    @property
    def discourses(self):
        q = self.sql_session.query(Discourse)
        results = [d.name for d in q.all()]
        return results

    def discourse_sound_file(self, discourse):
        q = self.sql_session.query(SoundFile).join(SoundFile.discourse)
        q = q.filter(Discourse.name == discourse)
        sound_file = q.first()
        return sound_file

    def load_variables(self):
        try:
            with open(os.path.join(self.config.data_dir, 'variables'), 'rb') as f:
                var = pickle.load(f)
            self.relationship_types = var['relationship_types']
            self.is_timed = var['is_timed']
            self.hierarchy = var['hierarchy']
        except FileNotFoundError:
            self.relationship_types = set()
            self.is_timed = False
            self.hierarchy = {}

    def save_variables(self):
        with open(os.path.join(self.config.data_dir, 'variables'), 'wb') as f:
            pickle.dump({'relationship_types':self.relationship_types,
                        'is_timed': self.is_timed,
                        'hierarchy': self.hierarchy}, f)

    def __enter__(self):
        self.load_variables()
        self.sql_session = Session()
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        self.save_variables()
        if exc_type is None:
            try:
                shutil.rmtree(self.config.temp_dir)
            except FileNotFoundError:
                pass
            self.sql_session.commit()
            return True
        else:
            self.sql_session.rollback()
        self.sql_session.expunge_all()
        self.sql_session.close()

    def __getattr__(self, key):
        if key in self.relationship_types:
            return AnnotationAttribute(key, corpus = self.corpus_name)
        raise(GraphQueryError('The graph does not have any annotations of type \'{}\'.  Possible types are: {}'.format(key, ', '.join(sorted(self.relationship_types)))))

    def reset_graph(self):
        self.graph.cypher.execute('''MATCH (:%s)-[r:is_a]->() DELETE r''' % (self.corpus_name))

        self.graph.cypher.execute('''MATCH (n:%s)-[r]->()-[r2]->(:%s) DELETE n, r, r2''' % (self.corpus_name, self.corpus_name))

        self.relationship_types = set()

    def reset(self):
        self.reset_graph()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def remove_discourse(self, name):
        self.graph.cypher.execute('''MATCH (n:%s:%s)-[r]->() DELETE n, r'''
                                    % (self.corpus_name, name))

    def discourse(self, name, annotations = None):
        return discourse_query(self, name, annotations)

    def query_graph(self, annotation_type):
        if annotation_type.type not in self.relationship_types:
            raise(GraphQueryError('The graph does not have any annotations of type \'{}\'.  Possible types are: {}'.format(annotation_type.name, ', '.join(sorted(self.relationship_types)))))
        return GraphQuery(self, annotation_type, self.is_timed)

    @property
    def has_sound_files(self):
        if self._has_sound_files is None:
            self._has_sound_files = self.sql_session.query(SoundFile).first() is not None
        return self._has_sound_files

    def query_acoustics(self, graph_query):
        if not self.has_sound_files:
            raise(NoSoundFileError)
        return AcousticQuery(self, graph_query)

    def analyze_acoustics(self):
        if not self.has_sound_files:
            raise(NoSoundFileError)
        acoustic_analysis(self)

    def get_utterances(self, discourse):
        pass

    def add_discourse(self, data):
        log = logging.getLogger('{}_loading'.format(self.corpus_name))
        log.info('Begin adding discourse {}...'.format(data.name))
        begin = time.time()
        data.corpus_name = self.corpus_name
        data_to_graph_csvs(data, self.config.temp_dir)
        import_csvs(self, data)
        self.relationship_types.update(data.output_types)
        if data.is_timed:
            self.is_timed = True
        else:
            self.is_timed = False
        self.update_sql_database(data)
        add_acoustic_info(self, data)
        self.hierarchy = {}
        for x in data.output_types:
            if x == 'word':
                self.hierarchy[x] = data[data.word_levels[0]].supertype
            else:
                supertype = data[x].supertype
                if supertype is not None and data[supertype].anchor:
                    supertype = 'word'
                self.hierarchy[x] = supertype
        log.info('Finished adding discourse {}!'.format(data.name))
        log.debug('Total time taken: {} seconds'.format(time.time() - begin))

    def update_sql_database(self, data):
        log = logging.getLogger('{}_loading'.format(self.corpus_name))
        log.info('Beginning to import {} into the SQL database...'.format(data.name))
        initial_begin = time.time()

        discourse, _ =  get_or_create(self.sql_session, Discourse, name = data.name)
        try:
            transcription_type = self.inventory.get_annotation_type('transcription')
        except:
            transcription_type = AnnotationType(label = 'transcription')
            self.sql_session.add(transcription_type)
            self.inventory.type_cache['transcription'] = transcription_type
        base_levels = data.base_levels
        for level in data.output_types:
            if not data[level].anchor:
                continue
            log.info('Beginning to import annotations...'.format(level))
            begin = time.time()
            for d in data[level]:
                trans = None
                if len(base_levels) > 0:
                    b = base_levels[0]
                    try:
                        base_type = self.inventory.get_annotation_type(b)
                    except:
                        base_type = AnnotationType(label = b)
                        self.sql_session.add(base_type)
                        self.inventory.type_cache[b] = base_type
                    begin, end = d[b]
                    base_sequence = data[b][begin:end]
                    for j, first in enumerate(base_sequence):
                        p = self.inventory.get_or_create_item(first.label, base_type)
                    if 'transcription' in d.type_properties:
                        trans = d.type_properties['transcription']
                    elif not data[b].token:
                        trans = [x.label for x in base_sequence]
                if trans is None:
                    trans = ''
                elif isinstance(trans, list):
                    for seg in trans:
                        p = self.inventory.get_or_create_item(first.label, transcription_type)
                    trans = '.'.join(trans)
                word = self.lexicon.get_or_create_word(d.label, trans)
                word.frequency += 1
                for k,v in d.type_properties.items():
                    if v is None:
                        continue
                    try:
                        prop_type = self.lexicon.get_property_type(k)
                    except:
                        prop_type = WordPropertyType(label = k)
                        self.sql_session.add(prop_type)
                        self.lexicon.prop_type_cache[k] = prop_type
                    if isinstance(v, (int,float)):
                        prop, _ = get_or_create(self.sql_session, WordNumericProperty, word = word, property_type = prop_type, value = v)
                    elif isinstance(v, (list, tuple)):
                        prop, _ = get_or_create(self.sql_session, WordProperty, word = word, property_type = prop_type, value = '.'.join(map(str,v)))
                    else:
                        prop, _ = get_or_create(self.sql_session, WordProperty, word = word, property_type = prop_type, value = v)

            log.info('Finished importing {} annotations!'.format(level))
            log.debug('Importing {} annotations took: {} seconds.'.format(level, time.time()-begin))
        log.info('Finished importing {} to the SQL database!'.format(data.name))
        log.debug('SQL importing took: {} seconds'.format(time.time() - initial_begin))

