import os
import re
import shutil
import pickle
import logging
import time
from collections import defaultdict

import py2neo
from py2neo import Graph
from py2neo.packages.httpstream import http
http.socket_timeout = 60
from py2neo.cypher.error.schema import IndexAlreadyExists

from .config import CorpusConfig

from .structure import Hierarchy

from .io.graph import (data_to_graph_csvs, import_csvs,
                    data_to_type_csvs, import_type_csvs)

from .graph.query import GraphQuery
from .graph.func import Max, Min
from .graph.attributes import AnnotationAttribute, PauseAnnotation

from .sql.models import (Base, Word, WordProperty, WordNumericProperty, WordPropertyType,
                    InventoryItem, AnnotationType, Discourse,Speaker)

from sqlalchemy import create_engine

from .sql.config import Session

from .sql.helper import get_or_create

from .sql.query import Lexicon, Inventory

from .graph.cypher import discourse_query

from .exceptions import (CorpusConfigError, GraphQueryError,
        ConnectionError, AuthorizationError, TemporaryConnectionError,
        NetworkAddressError)

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

        self.hierarchy = Hierarchy({})

        self.lexicon = Lexicon(self)

        self.inventory = Inventory(self)

    def generate_hierarchy(self):
        all_labels = self.graph.node_labels
        linguistic_labels = []
        discourses = set(self.discourses)
        reserved = set(['Speaker', 'Discourse', 'speech', 'pause'])
        exists_statement = '''MATCH (n:«labels») RETURN 1 LIMIT 1'''
        for label in all_labels:
            if label in discourses:
                continue
            if label in reserved:
                continue
            if label == self.corpus_name:
                continue
            if not self.execute_cypher(exists_statement, labels = [self.corpus_name, label]):
                continue
            linguistic_labels.append(label)
        h = {}
        subs = {}
        contain_statement = '''MATCH (t:{corpus_name}:«super_label»)<-[:contained_by]-(n:{corpus_name}:«sub_label») RETURN 1 LIMIT 1'''.format(corpus_name = self.corpus_name)
        annotate_statement = '''MATCH (t:{corpus_name}:«super_label»)<-[:annotates]-(n:{corpus_name}:«sub_label») RETURN 1 LIMIT 1'''.format(corpus_name = self.corpus_name)
        for sub_label in linguistic_labels:
            for sup_label in linguistic_labels:
                if sub_label == sup_label:
                    continue
                if self.execute_cypher(contain_statement, super_label = sup_label, sub_label = sub_label):
                    h[sub_label] = sup_label
                    break
                if self.execute_cypher(annotate_statement, super_label = sup_label, sub_label = sub_label):
                    if sup_label not in subs:
                        subs[sup_label] = set([])
                    subs[sup_label].add(sub_label)
                    break
            else:
                h[sub_label] = None
        h = Hierarchy(h)
        h.subannotations = subs
        return h

    def init_sql(self):
        self.engine = create_engine(self.config.sql_connection_string)
        Session.configure(bind=self.engine)
        if not os.path.exists(self.config.db_path):
            Base.metadata.create_all(self.engine)

    def execute_cypher(self, statement, **parameters):
        try:
            return self.graph.cypher.execute(statement, **parameters)
        except http.SocketError:
            raise(ConnectionError('PolyglotDB could not connect to the server specified.'))
        except py2neo.error.Unauthorized:
            raise(AuthorizationError('The specified user and password were not authorized by the server.'))
        except http.NetworkAddressError:
            raise(NetworkAddressError('The server specified could not be found.  Please double check the server address for typos or check your internet connection.'))
        except (py2neo.cypher.TransientError,
                #py2neo.cypher.error.network.UnknownFailure,
                py2neo.cypher.error.statement.ExternalResourceFailure):
            raise(TemporaryConnectionError('The server is (likely) temporarily unavailable.'))
        except Exception:
            raise

    @property
    def discourses(self):
        '''
        Return a list of all discourses in the corpus.
        '''
        q = self.sql_session.query(Discourse).all()
        if not len(q):
            res = self.execute_cypher('''MATCH (d:Discourse:{corpus_name}) RETURN d.name as discourse'''.format(corpus_name = self.corpus_name))
            discourses = []
            for d in res:
                instance = Discourse(name = d.discourse)
                self.sql_session.add(instance)
                discourses.append(d.discourse)
            self.sql_session.flush()
            return discourses
        return [x.name for x in q]

    @property
    def speakers(self):
        q = self.sql_session.query(Speaker).all()
        if not len(q):
            res = self.execute_cypher('''MATCH (s:Speaker:{corpus_name}) RETURN s.name as speaker'''.format(corpus_name = self.corpus_name))
            speakers = []
            for s in res:
                instance = Speaker(name = s.speaker)
                self.sql_session.add(instance)
                speakers.append(s.speaker)
            self.sql_session.flush()
            return speakers
        return [x.name for x in q]

    def load_variables(self):
        try:
            with open(os.path.join(self.config.data_dir, 'variables'), 'rb') as f:
                var = pickle.load(f)
            self.hierarchy = var['hierarchy']
        except FileNotFoundError:
            if self.corpus_name:
                self.hierarchy = self.generate_hierarchy()
                self.save_variables()

    def save_variables(self):
        with open(os.path.join(self.config.data_dir, 'variables'), 'wb') as f:
            pickle.dump({'hierarchy': self.hierarchy}, f)

    def __enter__(self):
        self.sql_session = Session()
        self.load_variables()
        return self

    def __exit__(self, exc_type, exc, exc_tb):
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
        if key + 's' in self.hierarchy.annotation_types:
            key += 's' # FIXME
        if key in self.hierarchy.annotation_types:
            return AnnotationAttribute(key, corpus = self.corpus_name, hierarchy = self.hierarchy)
        raise(GraphQueryError('The graph does not have any annotations of type \'{}\'.  Possible types are: {}'.format(key, ', '.join(sorted(self.hierarchy.annotation_types)))))

    def reset_graph(self):
        '''
        Remove all nodes and relationships in the graph that are apart
        of this corpus.
        '''

        self.execute_cypher('''MATCH (n:%s) DETACH DELETE n''' % (self.corpus_name))

        self.hierarchy = Hierarchy({})

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
        self.execute_cypher('''MATCH (n:%s:%s)-[r]->() DELETE n, r'''
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
        if annotation_type.type not in self.hierarchy.annotation_types:
            raise(GraphQueryError('The graph does not have any annotations of type \'{}\'.  Possible types are: {}'.format(annotation_type.name, ', '.join(sorted(self.hierarchy.annotation_types)))))
        return GraphQuery(self, annotation_type)

    @property
    def annotation_types(self):
        return self.hierarchy.annotation_types

    @property
    def lowest_annotation(self):
        '''
        Returns the annotation type that is the lowest in the hierarchy
        of containment.
        '''
        return self.hierarchy.lowest


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
        data_to_type_csvs(parsed_data, self.config.temporary_directory('csv'))
        import_type_csvs(self, list(parsed_data.values())[0])

    def initialize_import(self, data):
        try:
            self.execute_cypher('CREATE CONSTRAINT ON (node:Corpus) ASSERT node.name IS UNIQUE')
        except IndexAlreadyExists:
            pass

        try:
            self.execute_cypher('CREATE INDEX ON :Discourse(name)')
        except IndexAlreadyExists:
            pass
        try:
            self.execute_cypher('CREATE INDEX ON :Speaker(name)')
        except IndexAlreadyExists:
            pass
        self.execute_cypher('''MERGE (n:Corpus {name: {corpus_name}})''', corpus_name = self.corpus_name)

    def finalize_import(self, data):
        self.save_variables()
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

        self.execute_cypher(
            '''MERGE (n:Discourse:{corpus_name} {{name: {{discourse_name}}}})'''.format(corpus_name = self.corpus_name),
                    discourse_name = data.name)
        for s in data.speakers:
            self.execute_cypher(
                '''MERGE (n:Speaker:{corpus_name} {{name: {{speaker_name}}}})'''.format(corpus_name = self.corpus_name),
                        speaker_name = s)
        data.corpus_name = self.corpus_name
        data_to_graph_csvs(data, self.config.temporary_directory('csv'))
        import_csvs(self, data)
        self.update_sql_database(data)
        self.hierarchy.update(data.hierarchy)


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
        segment_type = data.segment_type
        created_words = set()
        for level in data.annotation_types:
            if not data[level].is_word:
                continue
            log.info('Beginning to import annotations...'.format(level))
            begin = time.time()
            for d in data[level]:
                trans = None
                if segment_type is not None:
                    base_sequence = data[segment_type].lookup_range(d.begin, d.end, speaker = d.speaker)
                    phone_cache[segment_type].update(x.label for x in base_sequence)
                elif 'transcription' in d.type_properties:
                    trans = d.type_properties['transcription']
                if trans is None:
                    trans = ''
                elif isinstance(trans, list):
                    phone_cache['transcription'].update(trans)
                    trans = '.'.join(trans)
                word, created = self.lexicon.get_or_create_word(d.label, trans)
                if 'frequency' in d.type_properties:
                    word.frequency = d.type_properties['frequency']
                else:
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
                        if isinstance(v, (int,float)) and k != 'frequency':
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


def get_corpora_list(config):
    with CorpusContext(config) as c:
        statement = '''MATCH (n:Corpus) RETURN n.name as name ORDER BY name'''
        results = c.execute_cypher(statement)
    return [x.name for x in results]
