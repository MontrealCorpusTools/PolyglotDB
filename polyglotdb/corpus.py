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

from .io.graph import (data_to_graph_csvs, import_csvs,
                    data_to_type_csvs, import_type_csvs, initialize_csv,
                    initialize_csvs_header)

from .graph.query import GraphQuery
from .graph.func import Max, Min
from .graph.attributes import AnnotationAttribute, PauseAnnotation

from .sql.models import (Base, Word, WordProperty, WordPropertyType,
                    InventoryItem, AnnotationType, Discourse)

from sqlalchemy import create_engine

from .sql.config import Session

from .sql.helper import get_or_create

from .sql.query import Lexicon, Inventory

from .graph.cypher import discourse_query

from .exceptions import CorpusConfigError, GraphQueryError

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
        self.init_sql()

        self.annotation_types = set()
        self.is_timed = False
        self.hierarchy = {}

        self.lexicon = Lexicon(self)

        self.inventory = Inventory(self)

    def init_sql(self):
        self.engine = create_engine(self.config.sql_connection_string)
        Session.configure(bind=self.engine)
        if not os.path.exists(self.config.db_path):
            Base.metadata.create_all(self.engine)

    @property
    def discourses(self):
        q = self.sql_session.query(Discourse)
        results = [d.name for d in q.all()]
        return results

    def load_variables(self):
        try:
            with open(os.path.join(self.config.data_dir, 'variables'), 'rb') as f:
                var = pickle.load(f)
            self.annotation_types = var['annotation_types']
            self.hierarchy = var['hierarchy']
        except FileNotFoundError:
            self.annotation_types = set()
            self.hierarchy = {}

    def save_variables(self):
        with open(os.path.join(self.config.data_dir, 'variables'), 'wb') as f:
            pickle.dump({'annotation_types':self.annotation_types,
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
            except:
                pass
            self.sql_session.commit()
            return True
        else:
            self.sql_session.rollback()
        self.sql_session.expunge_all()
        self.sql_session.close()

    def __getattr__(self, key):
        if key == 'pause':
            return PauseAnnotation(corpus = self.corpus_name)
        if key in self.annotation_types:
            supertype = self.hierarchy[key]


            contains = sorted(self.hierarchy.keys())
            supertypes = [supertype, key]
            if supertype is not None:
                while True:
                    supertype = self.hierarchy[supertype]
                    if supertype is None:
                        break
                    supertypes.append(supertype)
            contains = [x for x in contains if x not in supertypes]
            return AnnotationAttribute(key, corpus = self.corpus_name, contains = contains)
        raise(GraphQueryError('The graph does not have any annotations of type \'{}\'.  Possible types are: {}'.format(key, ', '.join(sorted(self.annotation_types)))))

    def reset_graph(self):

        self.graph.cypher.execute('''MATCH (n:%s) DETACH DELETE n''' % (self.corpus_name))

        self.annotation_types = set()
        self.hierarchy = {}

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
        if annotation_type.type not in self.annotation_types:
            raise(GraphQueryError('The graph does not have any annotations of type \'{}\'.  Possible types are: {}'.format(annotation_type.name, ', '.join(sorted(self.annotation_types)))))
        return GraphQuery(self, annotation_type, self.is_timed)

    @property
    def lowest_annotation(self):
        values = self.hierarchy.values()
        for k in self.hierarchy.keys():
            if k not in values:
                return getattr(self, k)
        return None


    def add_types(self, parsed_data):
        data = list(parsed_data.values())[0]
        self.annotation_types.update(data.annotation_types)
        self.hierarchy = data.hierarchy
        data_to_type_csvs(parsed_data, self.config.temporary_directory('csv'))
        import_type_csvs(self, list(parsed_data.values())[0])

    def initialize_import(self, data):
        return
        #initialize_csvs_header(data, self.config.temporary_directory('csv'))

    def finalize_import(self, data):
        return
        #import_csvs(self, data)

    def add_discourse(self, data):
        log = logging.getLogger('{}_loading'.format(self.corpus_name))
        log.info('Begin adding discourse {}...'.format(data.name))
        begin = time.time()
        data.corpus_name = self.corpus_name
        data_to_graph_csvs(data, self.config.temporary_directory('csv'))
        import_csvs(self, data)
        self.update_sql_database(data)
        if data.is_timed:
            self.is_timed = True
        else:
            self.is_timed = False

        log.info('Finished adding discourse {}!'.format(data.name))
        log.debug('Total time taken: {} seconds'.format(time.time() - begin))

    def load(self, parser, path):
        if os.path.isdir(path):
            self.load_directory(parser, path)
        else:
            self.load_discourse(parser, path)

    def load_discourse(self, parser, path):
        data = parser.parse_discourse(path)
        self.add_types({data.name: data})
        self.initialize_import(data)
        self.add_discourse(data)
        self.finalize_import(data)

    def load_directory(self, parser, path):
        if parser.call_back is not None:
            parser.call_back('Finding  files...')
            parser.call_back(0, 0)
        file_tuples = []
        for root, subdirs, files in os.walk(path, followlinks = True):
            for filename in files:
                if parser.stop_check is not None and parser.stop_check():
                    return
                if not parser.match_extension(filename):
                    continue
                file_tuples.append((root, filename))
        if parser.call_back is not None:
            parser.call_back('Parsing files...')
            parser.call_back(0,len(file_tuples))
            cur = 0
        parsed_data = {}

        for i, t in enumerate(file_tuples):
            if parser.stop_check is not None and parser.stop_check():
                return
            if parser.call_back is not None:
                parser.call_back('Parsing file {} of {}...'.format(i+1, len(file_tuples)))
                parser.call_back(i)
            root, filename = t
            name = os.path.splitext(filename)[0]
            path = os.path.join(root,filename)
            data = parser.parse_discourse(path)
            parsed_data[t] = data

        if parser.call_back is not None:
            parser.call_back('Parsing annotation types...')
        self.add_types(parsed_data)
        self.initialize_import(data)
        for i,(t,data) in enumerate(sorted(parsed_data.items(), key = lambda x: x[0])):
            if parser.call_back is not None:
                name = t[1]
                parser.call_back('Importing discourse {} of {} ({})...'.format(i+1, len(file_tuples), name))
                parser.call_back(i)
            self.add_discourse(data)
        self.finalize_import(data)

    def update_sql_database(self, data):
        log = logging.getLogger('{}_loading'.format(self.corpus_name))
        log.info('Beginning to import {} into the SQL database...'.format(data.name))
        initial_begin = time.time()

        discourse, _ =  get_or_create(self.sql_session, Discourse, name = data.name)
        phone_cache = defaultdict(set)
        segment_type = data.segment_type
        created_words = set()
        for level in data.annotation_types:
            continue
            if not data[level].is_word:
                continue
            log.info('Beginning to import annotations...'.format(level))
            begin = time.time()
            for d in data[level]:
                trans = None
                if len(base_levels) > 0:
                    b = segment_type
                    begin, end = d[b]
                    base_sequence = data[b][begin:end]
                    phone_cache[b].update(x.label for x in base_sequence)
                    if 'transcription' in d.type_properties:
                        trans = d.type_properties['transcription']
                    elif not data[b].token:
                        trans = [x.label for x in base_sequence]
                if trans is None:
                    trans = ''
                elif isinstance(trans, list):
                    phone_cache['transcription'].update(trans)
                    trans = '.'.join(trans)
                word, created = self.lexicon.get_or_create_word(d.label, trans)
                word.frequency += 1
                if created:
                    created_words.add(d.label)
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

        for level, phones in phone_cache.items():
            try:
                base_type = self.inventory.get_annotation_type(level)
            except:
                base_type = AnnotationType(label = level)
                self.sql_session.add(base_type)
                self.inventory.type_cache[level] = base_type

            for seg in phones:
                p, _ = self.inventory.get_or_create_item(seg, base_type)
        log.info('Finished importing {} to the SQL database!'.format(data.name))
        log.debug('SQL importing took: {} seconds'.format(time.time() - initial_begin))
