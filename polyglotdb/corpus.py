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
    """
    Base CorpusContext class.  Inherit from this and extend to create
    more functionality.

    Parameters
    ----------
    args : arguments or :class:`polyglotdb.config.CorpusConfig`
        If the first argument is not a CorpusConfig object, it is
        the name of the corpus
    kwargs : keyword arguments
        If a :class:`polyglotdb.config.CorpusConfig` object is not specified, all arguments and
        keyword arguments are passed to a CorpusConfig object
    """
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

        self.relationship_types = set()
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
        '''
        Return a list of all discourses in the corpus.
        '''
        q = self.sql_session.query(Discourse)
        results = [d.name for d in q.all()]
        return results

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
        self.relationship_types.add('pause')

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
        if key in self.relationship_types:
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
        raise(GraphQueryError('The graph does not have any annotations of type \'{}\'.  Possible types are: {}'.format(key, ', '.join(sorted(self.relationship_types)))))

    def reset_graph(self):
        '''
        Remove all nodes and relationships in the graph that are apart
        of this corpus.
        '''

        self.graph.cypher.execute('''MATCH (n:%s) DETACH DELETE n''' % (self.corpus_name))

        self.relationship_types = set()
        self.hierarchy = {}

    def reset(self):
        '''
        Reset the graph and SQL databases for a corpus.
        '''
        self.reset_graph()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def remove_discourse(self, name):
        '''
        Remove the nodes and relationships associated with a single
        discourse in the corpus.

        Parameters
        ----------
        name : str
            Name of the discourse to remove
        '''
        self.graph.cypher.execute('''MATCH (n:%s:%s)-[r]->() DELETE n, r'''
                                    % (self.corpus_name, name))

    def discourse(self, name, annotations = None):
        '''
        Get all words spoken in a discourse.

        Parameters
        ----------
        name : str
            Name of the discourse
        '''
        return discourse_query(self, name, annotations)

    def query_graph(self, annotation_type):
        '''
        Return a :class:`polyglotdb.config.GraphQuery` for the specified annotation type.

        When extending :class:`polyglotdb.config.GraphQuery` functionality, this function must be
        overwritten.

        Parameters
        ----------
        annotation_type : str
            The type of annotation to look for in the corpus
        '''
        if annotation_type.type not in self.relationship_types:
            raise(GraphQueryError('The graph does not have any annotations of type \'{}\'.  Possible types are: {}'.format(annotation_type.name, ', '.join(sorted(self.relationship_types)))))
        return GraphQuery(self, annotation_type, self.is_timed)

    @property
    def lowest_annotation(self):
        '''
        Returns the annotation type that is the lowest in the hierarchy
        of containment.
        '''
        values = self.hierarchy.values()
        for k in self.hierarchy.keys():
            if k not in values:
                return getattr(self, k)
        return None


    def add_types(self, parsed_data):
        '''
        This function imports types of annotations into the corpus.

        Parameters
        ----------
        parsed_data: dict
            Dictionary with keys for discourse names and values of :class:`polyglotdb.io.helper.DiscourseData`
            objects
        '''
        data = list(parsed_data.values())[0]
        self.relationship_types.update(data.output_types)
        self.hierarchy = {}
        for x in data.output_types:
            if x == 'word':
                self.hierarchy[x] = data[data.word_levels[0]].supertype
            else:
                supertype = data[x].supertype
                if supertype is not None and data[supertype].anchor:
                    supertype = 'word'
                self.hierarchy[x] = supertype
        data_to_type_csvs(parsed_data, self.config.temporary_directory('csv'))
        import_type_csvs(self, list(parsed_data.values())[0].type_properties)

    def initialize_import(self, data):
        return
        #initialize_csvs_header(data, self.config.temporary_directory('csv'))

    def finalize_import(self, data):
        return
        #import_csvs(self, data)

    def add_discourse(self, data):
        '''
        Add a discourse to the graph database for corpus.

        Parameters
        ----------
        data : :class:`polyglotdb.io.helper.DiscourseData`
            Data for the discourse to be added
        '''
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

    def update_sql_database(self, data):
        '''
        Update the SQL database given a discourse's data.  This function
        adds new words and updates frequencies given occurences in the
        discourse

        Parameters
        ----------
        data : :class:`polyglotdb.io.helper.DiscourseData`
            Data for the discourse
        '''
        log = logging.getLogger('{}_loading'.format(self.corpus_name))
        log.info('Beginning to import {} into the SQL database...'.format(data.name))
        initial_begin = time.time()

        discourse, _ =  get_or_create(self.sql_session, Discourse, name = data.name)
        phone_cache = defaultdict(set)
        base_levels = data.base_levels
        created_words = set()
        for level in data.output_types:
            if not data[level].anchor:
                continue
            log.info('Beginning to import annotations...'.format(level))
            begin = time.time()
            for d in data[level]:
                trans = None
                if len(base_levels) > 0:
                    b = base_levels[0]
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
