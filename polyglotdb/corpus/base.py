import os
import re
import sys
import shutil
import pickle
import logging
import time
from collections import defaultdict

import sqlalchemy
import py2neo

from py2neo import Graph

from py2neo.database.status import (ClientError, DatabaseError, Forbidden,
                    TransientError, Unauthorized, ConstraintError)

from sqlalchemy import create_engine
from ..sql.models import Base, Discourse, Speaker
from ..sql.config import Session
from ..sql.query import Lexicon, Census

from ..config import CorpusConfig

from ..structure import Hierarchy

from ..graph.attributes import AnnotationAttribute, PauseAnnotation

from ..graph.query import GraphQuery, SpeakerGraphQuery, DiscourseGraphQuery

from ..exceptions import (CorpusConfigError, GraphQueryError,
        ConnectionError, AuthorizationError, TemporaryConnectionError,
        NetworkAddressError, NoSoundFileError)


class BaseContext(object):
    """
    Base CorpusContext class.  Inherit from this and extend to create
    more functionality.

    Parameters
    ----------
    *args
        If the first argument is not a :class:`~polyglotdb.config.CorpusConfig` object, it is
        the name of the corpus
    **kwargs
        If a :class:`~polyglotdb.config.CorpusConfig` object is not specified, all arguments and
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
        self.graph = Graph(**self.config.graph_connection_kwargs)
        self.corpus_name = self.config.corpus_name
        if self.corpus_name:
            self.init_sql()

        self.hierarchy = Hierarchy({})

        self.lexicon = Lexicon(self)
        self.census = Census(self)

        self._has_sound_files = None
        self._has_all_sound_files = None
        if getattr(sys, 'frozen', False):
            self.config.reaper_path = os.path.join(sys.path[-1], 'reaper')
        else:
            self.config.reaper_path = shutil.which('reaper')

        if sys.platform == 'win32':
            praat_exe = 'praatcon.exe'
        else:
            praat_exe = 'praat'

        if getattr(sys, 'frozen', False):
            self.config.praat_path = os.path.join(sys.path[-1], praat_exe)
        else:
            self.config.praat_path = shutil.which(praat_exe)

        self.config.query_behavior = 'speaker'

    def exists(self):
        statement = '''MATCH (c:Corpus) where c.name = '{}' return c '''.format(self.corpus_name)
        res = list(self.execute_cypher(statement))
        return len(res) > 0

    def load_variables(self):
        """
        Loads variables into Hierarchy
        """
        try:
            with open(os.path.join(self.config.data_dir, 'variables'), 'rb') as f:
                var = pickle.load(f)
            self.hierarchy = var['hierarchy']
        except FileNotFoundError:
            if self.corpus_name:
                self.hierarchy = self.generate_hierarchy()
                self.save_variables()

    def save_variables(self):
        """ saves variables to hierarchy"""
        with open(os.path.join(self.config.data_dir, 'variables'), 'wb') as f:
            pickle.dump({'hierarchy': self.hierarchy}, f)

    def init_sql(self):
        """
        initializes sql connection
        """
        self.engine = create_engine(self.config.sql_connection_string)
        Session.configure(bind=self.engine)
        if not os.path.exists(self.config.db_path):
            Base.metadata.create_all(self.engine)

    def execute_cypher(self, statement, **parameters):
        """
        Executes a cypher query

        Parameters
        ----------
        statement : str
            the cypher statement
        parameters : dict
            keyword arguments to execute a cypher statement

        Returns
        -------
        query result :
        or
        raises error

        """
        try:
            return self.graph.run(statement, **parameters)
        except (py2neo.packages.httpstream.http.SocketError,
                py2neo.packages.neo4j.v1.exceptions.ProtocolError):
            raise(ConnectionError('PolyglotDB could not connect to the server specified.'))
        except ClientError:
            raise
        except (Unauthorized):
            raise(AuthorizationError('The specified user and password were not authorized by the server.'))
        except Forbidden:
            raise(NetworkAddressError('The server specified could not be found.  Please double check the server address for typos or check your internet connection.'))
        except (TransientError):
            raise(TemporaryConnectionError('The server is (likely) temporarily unavailable.'))
        except ConstraintError as e:
            pass
        except Exception:
            raise

    @property
    def cypher_safe_name(self):
        return '`{}`'.format(self.corpus_name)

    @property
    def discourses(self):
        '''
        Return a list of all discourses in the corpus.
        '''
        q = self.sql_session.query(Discourse).all()
        if not len(q):
            res = self.execute_cypher('''MATCH (d:Discourse:{corpus_name}) RETURN d.name as discourse'''.format(corpus_name = self.cypher_safe_name))
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
        """
        Gets a list of speakers in the corpus

        Returns
        -------
        names : list
            all the speaker names
        """
        q = self.sql_session.query(Speaker).order_by(Speaker.name).all()
        if not len(q):
            res = self.execute_cypher('''MATCH (s:Speaker:{corpus_name}) RETURN s.name as speaker'''.format(corpus_name = self.cypher_safe_name))

            speakers = []
            for s in res:
                instance = Speaker(name = s['speaker'])
                self.sql_session.add(instance)
                speakers.append(s['speaker'])
            self.sql_session.flush()
            return sorted(speakers)
        return [x.name for x in q]

    def __enter__(self):
        self.sql_session = Session()
        self.load_variables()
        #if self.corpus_name:
        #    self.hierarchy = self.generate_hierarchy()
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        if exc_type is None:
            #try:
            #    shutil.rmtree(self.config.temp_dir)
            #except:
            #    pass
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

    @property
    def word_name(self):
        """
        Gets the word label

        Returns
        -------
        word : str
            word name
        """
        for at in self.hierarchy.annotation_types:
            if at.startswith('word'): #FIXME need a better way for storing word name
                return at
        return 'word'

    @property
    def phone_name(self):
        """
        Gets the phone label

        Returns
        -------
        phone : str
            phone name
        """
        name = self.hierarchy.lowest
        if name is None:
            name = 'phone'
        return name

    def reset_graph(self, call_back = None, stop_check = None):
        '''
        Remove all nodes and relationships in the corpus.
        '''

        delete_statement = '''MATCH (n:{corpus}:{anno})-[:spoken_by]->(s:{corpus}:Speaker)
        where s.name = {{speaker}}
        with n LIMIT 1000 DETACH DELETE n return count(n) as deleted_count'''

        delete_type_statement = '''MATCH (n:{corpus}:{anno}_type)
        with n LIMIT 1000 DETACH DELETE n return count(n) as deleted_count'''

        if call_back is not None:
            call_back('Resetting database...')
            number = self.execute_cypher('''MATCH (n:{}) return count(*) as number '''.format(self.cypher_safe_name)).evaluate()
            call_back(0, number)
        num_deleted = 0
        for a in self.hierarchy.annotation_types:
            if stop_check is not None and stop_check():
                break
            for s in self.speakers:
                if stop_check is not None and stop_check():
                    break
                deleted = 1000
                while deleted > 0:
                    if stop_check is not None and stop_check():
                        break
                    deleted = self.execute_cypher(delete_statement.format(corpus = self.cypher_safe_name, anno = a), speaker = s).evaluate()
                    num_deleted += deleted
                    if call_back is not None:
                        call_back(num_deleted)

            deleted = 1000
            while deleted > 0:
                if stop_check is not None and stop_check():
                    break
                deleted = self.execute_cypher(delete_type_statement.format(corpus = self.cypher_safe_name, anno = a)).evaluate()
                num_deleted += deleted
                if call_back is not None:
                    call_back(num_deleted)

        self.execute_cypher('''MATCH (n:{}:Speaker) DETACH DELETE n '''.format(self.cypher_safe_name))
        self.execute_cypher('''MATCH (n:{}:Discourse) DETACH DELETE n '''.format(self.cypher_safe_name))
        self.reset_hierarchy()
        self.execute_cypher('''MATCH (n:Corpus) where n.name = {corpus_name} DELETE n ''', corpus_name = self.corpus_name)
        self.hierarchy = Hierarchy({})

    def reset(self, call_back = None, stop_check = None):
        '''
        Reset the graph and SQL databases for a corpus.
        '''
        self.reset_acoustics(call_back, stop_check)
        self.reset_graph(call_back, stop_check)
        try:
            Base.metadata.drop_all(self.engine)
        except sqlalchemy.exc.OperationalError:
            pass
        Base.metadata.create_all(self.engine)

    def query_graph(self, annotation_type):
        '''
        Return a Query object for the specified annotation type.

        Parameters
        ----------
        annotation_type : str
            The type of annotation to look for in the corpus

        Returns
        -------
        GraphQuery
            Query object

        '''
        if annotation_type.type not in self.hierarchy.annotation_types \
                and annotation_type.type != 'pause': #FIXME make more general
            raise(GraphQueryError('The graph does not have any annotations of type \'{}\'.  Possible types are: {}'.format(annotation_type.name, ', '.join(sorted(self.hierarchy.annotation_types)))))
        if self.config.query_behavior == 'speaker':
            cls = SpeakerGraphQuery
        elif self.config.query_behavior == 'discourse':
            cls = DiscourseGraphQuery
        else:
            cls = GraphQuery
        return cls(self, annotation_type)

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

    def remove_discourse(self, name):
        '''
        Remove the nodes and relationships associated with a single
        discourse in the corpus.

        Parameters
        ----------
        name : str
            Name of the discourse to remove
        '''
        self.execute_cypher('''MATCH (n:{}:{})-[r]->() DELETE n, r'''.format(self.cypher_safe_name, name))

    def discourse(self, name, annotations = None):
        '''
        Get all words spoken in a discourse.

        Parameters
        ----------
        name : str
            Name of the discourse
        '''

        w = getattr(self, self.word_name) #FIXME make more general
        q = GraphQuery(self, w)
        q = q.filter(w.discourse.name == name)
        q = q.order_by(w.begin)
        return q.all()

    def query_speaker(self, name, property):
        """
        query for an individual speaker's property

        Parameters
        ----------
        name : str
            the speaker's name
        property : str
            the name of the property
        """
        res = self.census.get_speaker_annotations(property, name)

        return res