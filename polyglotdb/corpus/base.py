import os
import pickle
import shutil
import sys
import time
from decimal import Decimal

from neo4j.v1 import GraphDatabase

from ..query.annotations.attributes import AnnotationNode, PauseAnnotation
from ..query.annotations import GraphQuery, SpeakerGraphQuery, DiscourseGraphQuery
from ..query.lexicon import LexiconQuery, LexiconNode
from ..query.speaker import SpeakerQuery, SpeakerNode
from ..query.discourse import DiscourseQuery, DiscourseNode
from ..config import CorpusConfig
from ..exceptions import (CorpusConfigError, GraphQueryError,
                          ConnectionError, AuthorizationError, TemporaryConnectionError,
                          NetworkAddressError)
from ..structure import Hierarchy


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
            raise (CorpusConfigError('Need to specify a corpus name or CorpusConfig.'))
        if isinstance(args[0], CorpusConfig):
            self.config = args[0]
        else:
            self.config = CorpusConfig(*args, **kwargs)
        self.config.init()
        self.graph_driver = GraphDatabase.driver(self.config.graph_connection_string)
        self.corpus_name = self.config.corpus_name

        self.hierarchy = Hierarchy({}, corpus_name=self.corpus_name)

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
        from neo4j.exceptions import ServiceUnavailable
        for k, v in parameters.items():
            if isinstance(v, Decimal):
                parameters[k] = float(v)
        try:
            with self.graph_driver.session() as session:
                results = session.run(statement, **parameters)
            return results
        except Exception as e:
            raise
    @property
    def cypher_safe_name(self):
        return '`{}`'.format(self.corpus_name)

    @property
    def discourses(self):
        '''
        Return a list of all discourses in the corpus.
        '''
        res = self.execute_cypher('''MATCH (d:Discourse:{corpus_name}) RETURN d.name as discourse'''.format(
            corpus_name=self.cypher_safe_name))
        return [x['discourse'] for x in res]

    @property
    def speakers(self):
        """
        Gets a list of speakers in the corpus

        Returns
        -------
        names : list
            all the speaker names
        """
        res = self.execute_cypher('''MATCH (s:Speaker:{corpus_name}) RETURN s.name as speaker'''.format(
            corpus_name=self.cypher_safe_name))
        return [x['speaker'] for x in res]

    def __enter__(self):
        if self.corpus_name:
            if not os.path.exists(self.hierarchy_path):
                self.hierarchy = self.generate_hierarchy()
                self.cache_hierarchy()
            else:
                self.load_hierarchy()
        return self

    @property
    def hierarchy_path(self):
        return os.path.join(self.config.base_dir, 'hierarchy')

    def cache_hierarchy(self):
        import pickle
        with open(self.hierarchy_path, 'wb') as f:
            pickle.dump(obj=self.hierarchy, file=f)

    def load_hierarchy(self):
        import pickle
        with open(self.hierarchy_path, 'rb') as f:
            self.hierarchy = pickle.load(file=f)

    def __exit__(self, exc_type, exc, exc_tb):
        self.graph_driver.close()
        if exc_type is None:
            # try:
            #    shutil.rmtree(self.config.temp_dir)
            # except:
            #    pass
            return True
        else:
            return False

    def __getattr__(self, key):
        if key == 'speaker':
            return SpeakerNode(corpus=self.corpus_name, hierarchy=self.hierarchy)
        if key == 'discourse':
            return DiscourseNode(corpus=self.corpus_name, hierarchy=self.hierarchy)
        if key == 'pause':
            return PauseAnnotation(corpus=self.corpus_name, hierarchy=self.hierarchy)
        if key + 's' in self.hierarchy.annotation_types:
            key += 's'  # FIXME
        if key in self.hierarchy.annotation_types:
            return AnnotationNode(key, corpus=self.corpus_name, hierarchy=self.hierarchy)
        if key.startswith('lexicon_'):
            key = key.split('_')[1]
            if key in self.hierarchy.annotation_types:
                return LexiconNode(key, corpus=self.corpus_name, hierarchy=self.hierarchy)
        raise (GraphQueryError(
            'The graph does not have any annotations of type \'{}\'.  Possible types are: {}'.format(key, ', '.join(
                sorted(self.hierarchy.annotation_types)))))

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
            if at.startswith('word'):  # FIXME need a better way for storing word name
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

    def reset_graph(self, call_back=None, stop_check=None):
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
            number = self.execute_cypher(
                '''MATCH (n:{}) return count(*) as number '''.format(self.cypher_safe_name))['number']
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
                    deleted = self.execute_cypher(delete_statement.format(corpus=self.cypher_safe_name, anno=a),
                                                  speaker=s).single()['deleted_count']
                    num_deleted += deleted
                    if call_back is not None:
                        call_back(num_deleted)

            deleted = 1000
            while deleted > 0:
                if stop_check is not None and stop_check():
                    break
                deleted = self.execute_cypher(
                    delete_type_statement.format(corpus=self.cypher_safe_name, anno=a)).single()['deleted_count']
                num_deleted += deleted
                if call_back is not None:
                    call_back(num_deleted)

        self.execute_cypher('''MATCH (n:{}:Speaker) DETACH DELETE n '''.format(self.cypher_safe_name))
        self.execute_cypher('''MATCH (n:{}:Discourse) DETACH DELETE n '''.format(self.cypher_safe_name))
        self.reset_hierarchy()
        self.execute_cypher('''MATCH (n:Corpus) where n.name = {corpus_name} DELETE n ''', corpus_name=self.corpus_name)
        self.hierarchy = Hierarchy({})

    def reset(self, call_back=None, stop_check=None):
        '''
        Reset the graph databases for a corpus.
        '''
        self.reset_acoustics(call_back, stop_check)
        self.reset_graph(call_back, stop_check)

    def query_graph(self, annotation_type):
        '''
        Return a Query object for the specified annotation type.

        Parameters
        ----------
        annotation_type : :class:`polyglotdb.query.attributes.AnnotationNode`
            The type of annotation to look for in the corpus

        Returns
        -------
        GraphQuery
            Query object

        '''
        if annotation_type.node_type not in self.hierarchy.annotation_types \
                and annotation_type.node_type != 'pause':  # FIXME make more general
            raise (GraphQueryError(
                'The graph does not have any annotations of type \'{}\'.  Possible types are: {}'.format(
                    annotation_type.name, ', '.join(sorted(self.hierarchy.annotation_types)))))
        if self.config.query_behavior == 'speaker':
            cls = SpeakerGraphQuery
        elif self.config.query_behavior == 'discourse':
            cls = DiscourseGraphQuery
        else:
            cls = GraphQuery
        return cls(self, annotation_type)

    def query_lexicon(self, annotation_type):
        '''
        Return a Query object for the specified annotation type.

        Parameters
        ----------
        annotation_type : :class:`polyglotdb.query.attributes.AnnotationNode`
            The type of annotation to look for in the corpus

        Returns
        -------
        GraphQuery
            Query object

        '''
        if annotation_type.node_type not in self.hierarchy.annotation_types \
                and annotation_type.node_type != 'pause':  # FIXME make more general
            raise (GraphQueryError(
                'The graph does not have any annotations of type \'{}\'.  Possible types are: {}'.format(
                    annotation_type.node_type, ', '.join(sorted(self.hierarchy.annotation_types)))))
        return LexiconQuery(self, annotation_type)

    def query_discourses(self):
        """
        query for an individual speaker's property

        Parameters
        ----------
        name : str
            the speaker's name
        property : str
            the name of the property
        """
        return DiscourseQuery(self)

    def query_speakers(self):
        """
        query for an individual speaker's property

        Parameters
        ----------
        name : str
            the speaker's name
        property : str
            the name of the property
        """
        return SpeakerQuery(self)


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

    def discourse_annotations(self, name, annotations=None):
        '''
        Get all words spoken in a discourse.

        Parameters
        ----------
        name : str
            Name of the discourse
        '''

        w = getattr(self, self.word_name)  # FIXME make more general
        q = GraphQuery(self, w)
        q = q.filter(w.discourse.name == name)
        q = q.order_by(w.begin)
        return q.all()

    @property
    def phones(self):
        statement = '''MATCH (p:{phone_name}_type:{corpus_name}) return p.label as label'''.format(
            phone_name=self.phone_name, corpus_name=self.cypher_safe_name)
        results = self.execute_cypher(statement)
        return [r['label'] for r in results]

    @property
    def words(self):
        statement = '''MATCH (p:{word_name}_type:{corpus_name}) return p.label as label'''.format(
            word_name=self.word_name, corpus_name=self.cypher_safe_name)
        results = self.execute_cypher(statement)
        return [r['label'] for r in results]
