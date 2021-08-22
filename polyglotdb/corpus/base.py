import os
import shutil
import sys
from decimal import Decimal

from neo4j import GraphDatabase

from ..query.annotations.attributes import AnnotationNode, PauseAnnotation
from ..query.annotations import SplitQuery
from ..query.lexicon import LexiconQuery, LexiconNode
from ..query.speaker import SpeakerQuery, SpeakerNode
from ..query.discourse import DiscourseQuery, DiscourseNode
from ..config import CorpusConfig
from ..exceptions import (CorpusConfigError, GraphQueryError)
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

    def exists(self):
        """
        Check whether the corpus has a Hierarchy schema in the Neo4j database

        Returns
        -------
        bool
            True if the corpus Hierarchy has been saved to the database
        """
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
        parameters : kwargs
            keyword arguments to execute a cypher statement

        Returns
        -------
        :class:`~neo4j.BoltStatementResult`
            Result of Cypher query
        """
        from neo4j.exceptions import ServiceUnavailable
        return_graph = False
        if 'return_graph' in parameters:
            return_graph = parameters.pop('return_graph')
        for k, v in parameters.items():
            if isinstance(v, Decimal):
                parameters[k] = float(v)
        try:
            with self.graph_driver.session() as session:
                if self.config.debug:
                    print('Statement:', statement)
                    print('Parameters:',parameters)
                results = session.run(statement, **parameters)
                if return_graph:
                    results = results.graph()
                else:
                    results = results.data()

            return results
        except Exception as e:
            raise

    @property
    def cypher_safe_name(self):
        """
        Escape the corpus name for use in Cypher queries

        Returns
        -------
        str
            Corpus name made safe for Cypher
        """
        return '`{}`'.format(self.corpus_name)

    @property
    def discourses(self):
        """
        Gets a list of discourses in the corpus

        Returns
        -------
        list
            Discourse names in the corpus
        """
        res = self.execute_cypher('''MATCH (d:Discourse:{corpus_name}) RETURN d.name as discourse'''.format(
            corpus_name=self.cypher_safe_name))
        return [x['discourse'] for x in res]

    @property
    def speakers(self):
        """
        Gets a list of speakers in the corpus

        Returns
        -------
        list
            Speaker names in the corpus
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
        """
        Get the path to cached hierarchy information

        Returns
        -------
        str
            Path to the cached hierarchy data on disk
        """
        return os.path.join(self.config.base_dir, 'hierarchy')

    def cache_hierarchy(self):
        """
        Save corpus Hierarchy to the disk
        """
        import json
        with open(self.hierarchy_path, 'w', encoding='utf8') as f:
            json.dump(self.hierarchy.to_json(), f)

    def load_hierarchy(self):
        """
        Load Hierarchy object from the cached version
        """
        import json
        with open(self.hierarchy_path, 'r', encoding='utf8') as f:
            self.hierarchy = Hierarchy(corpus_name=self.corpus_name)
            self.hierarchy.from_json(json.load(f))

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

    def encode_type_subset(self, annotation_type, annotation_labels, subset_label):
        """
        Encode a type subset from labels of annotations

        Parameters
        ----------
        annotation_type : str
            Annotation type of labels
        annotation_labels : list
            a list of labels of annotations to subset together
        subset_label : str
            the label for the subset
        """
        ann = getattr(self, 'lexicon_' + annotation_type)
        q = self.query_lexicon(ann).filter(ann.label.in_(annotation_labels))
        q.create_subset(subset_label)
        self.encode_hierarchy()

    def reset_type_subset(self, annotation_type, subset_label):
        """
        Reset and remove a type subset

        Parameters
        ----------
        annotation_type : str
            Annotation type of the subset
        subset_label : str
            the label for the subset
        """
        from ..exceptions import SubsetError
        ann = getattr(self, 'lexicon_' + annotation_type)
        try:
            q = self.query_lexicon(ann.filter_by_subset(subset_label))
            q.remove_subset(subset_label)
            self.encode_hierarchy()
        except SubsetError:
            pass

    @property
    def word_name(self):
        """
        Gets the word label

        Returns
        -------
        str
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
        str
            phone name
        """
        name = self.hierarchy.lowest
        if name is None:
            name = 'phone'
        return name

    def reset_graph(self, call_back=None, stop_check=None):
        """
        Remove all nodes and relationships in the corpus.
        """

        delete_statement = '''MATCH (n:{corpus}:{anno})-[:spoken_by]->(s:{corpus}:Speaker)
        where s.name = $speaker
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
                                                  speaker=s)[0]['deleted_count']
                    num_deleted += deleted
                    if call_back is not None:
                        call_back(num_deleted)

            deleted = 1000
            while deleted > 0:
                if stop_check is not None and stop_check():
                    break
                deleted = self.execute_cypher(
                    delete_type_statement.format(corpus=self.cypher_safe_name, anno=a))[0]['deleted_count']
                num_deleted += deleted
                if call_back is not None:
                    call_back(num_deleted)

        self.execute_cypher('''MATCH (n:{}:Speaker) DETACH DELETE n '''.format(self.cypher_safe_name))
        self.execute_cypher('''MATCH (n:{}:Discourse) DETACH DELETE n '''.format(self.cypher_safe_name))
        self.reset_hierarchy()
        self.execute_cypher('''MATCH (n:Corpus) where n.name = $corpus_name DELETE n ''', corpus_name=self.corpus_name)
        self.hierarchy = Hierarchy(corpus_name=self.corpus_name)
        self.cache_hierarchy()

    def reset(self, call_back=None, stop_check=None):
        """
        Reset the Neo4j and InfluxDB databases for a corpus

        Parameters
        ----------
        call_back : callable
            Function to monitor progress
        stop_check : callable
            Function the check whether the process should terminate early
        """
        self.reset_acoustics()
        self.reset_graph(call_back, stop_check)
        shutil.rmtree(self.config.base_dir, ignore_errors=True)

    def query_graph(self, annotation_node):
        """
        Start a query over the tokens of a specified annotation type (i.e. ``corpus.word``)

        Parameters
        ----------
        annotation_node : :class:`polyglotdb.query.attributes.AnnotationNode`
            The type of annotation to look for in the corpus

        Returns
        -------
        :class:`~polyglotdb.query.annotations.query.SplitQuery`
            SplitQuery object

        """
        if annotation_node.node_type not in self.hierarchy.annotation_types \
                and annotation_node.node_type != 'pause':  # FIXME make more general
            raise (GraphQueryError(
                'The graph does not have any annotations of type \'{}\'.  Possible types are: {}'.format(
                    annotation_node.name, ', '.join(sorted(self.hierarchy.annotation_types)))))

        return SplitQuery(self, annotation_node)

    def query_lexicon(self, annotation_node):
        """
        Start a query over types of a specified annotation type (i.e. ``corpus.lexicon_word``)

        Parameters
        ----------
        annotation_node : :class:`polyglotdb.query.attributes.AnnotationNode`
            The type of annotation to look for in the corpus's lexicon

        Returns
        -------
        :class:`~polyglotdb.query.lexicon.query.LexiconQuery`
            LexiconQuery object

        """
        if annotation_node.node_type not in self.hierarchy.annotation_types \
                and annotation_node.node_type != 'pause':  # FIXME make more general
            raise (GraphQueryError(
                'The graph does not have any annotations of type \'{}\'.  Possible types are: {}'.format(
                    annotation_node.node_type, ', '.join(sorted(self.hierarchy.annotation_types)))))
        return LexiconQuery(self, annotation_node)

    def query_discourses(self):
        """
        Start a query over discourses in the corpus

        Returns
        -------
        :class:`~polyglotdb.query.discourse.query.DiscourseQuery`
            DiscourseQuery object
        """
        return DiscourseQuery(self)

    def query_speakers(self):
        """
        Start a query over speakers in the corpus

        Returns
        -------
        :class:`~polyglotdb.query.speaker.query.SpeakerQuery`
            SpeakerQuery object
        """
        return SpeakerQuery(self)

    @property
    def annotation_types(self):
        """
        Get a list of all the annotation types in the corpus's Hierarchy

        Returns
        -------
        list
            Annotation types
        """
        return self.hierarchy.annotation_types

    @property
    def lowest_annotation(self):
        """
        Returns the annotation type that is the lowest in the Hierarchy.

        Returns
        -------
        str
            Lowest annotation type in the Hierarchy
        """
        return self.hierarchy.lowest

    def remove_discourse(self, name):
        """
        Remove the nodes and relationships associated with a single
        discourse in the corpus.

        Parameters
        ----------
        name : str
            Name of the discourse to remove
        """
        if name not in self.discourses:
            raise GraphQueryError('{} is not a discourse in this corpus.'.format(name))
        d = self.discourse_sound_file(name)
        if 'consonant_file_path' in d and d['consonant_file_path'] is not None and os.path.exists(d['consonant_file_path']):
            directory = self.discourse_audio_directory(name)
            if self.config.debug:
                print('Removing', directory)
            shutil.rmtree(directory, ignore_errors=True)

        # Remove orphaned type nodes
        for a in self.hierarchy.annotation_types:
            # Remove tokens in discourse
            statement = '''MATCH (d:{corpus_name}:Discourse)<-[:spoken_in]-(n:{corpus_name}:{atype})
            WHERE d.name = $discourse
            DETACH DELETE n'''.format(corpus_name=self.cypher_safe_name, atype=a)
            if self.config.debug:
                print(statement)
            result = self.execute_cypher(statement, discourse=name)
            if self.config.debug:
                for r in result:
                    print('RESULT', r)
        # Remove discourse node
        statement = '''MATCH (d:{corpus_name}:Discourse)
        WHERE d.name = $discourse
        DETACH DELETE d'''.format(corpus_name=self.cypher_safe_name)
        if self.config.debug:
            print(statement)
        result = self.execute_cypher(statement, discourse=name)
        if self.config.debug:
            for r in result:
                print('RESULT', r)

        for a in self.hierarchy.annotation_types:
            statement = '''MATCH (t:{type}_type:{corpus_name})
            WHERE NOT (t)<-[:is_a]-()
            DETACH DELETE t'''.format(type=a, corpus_name=self.cypher_safe_name)
            if self.config.debug:
                print(statement)
            result = self.execute_cypher(statement)
            if self.config.debug:
                for r in result:
                    print('RESULT', r)

        # Remove orphaned speaker nodes
        statement = '''MATCH (s:Speaker:{corpus_name})
        WHERE NOT (s)<-[:spoken_by]-()
        DETACH DELETE s'''.format(corpus_name=self.cypher_safe_name)
        if self.config.debug:
            print(statement)
        result = self.execute_cypher(statement)
        if self.config.debug:
            for r in result:
                print('RESULT', r)

    @property
    def phones(self):
        """
        Get a list of all phone labels in the corpus.

        Returns
        -------
        list
            All phone labels in the corpus
        """
        statement = '''MATCH (p:{phone_name}_type:{corpus_name}) return p.label as label'''.format(
            phone_name=self.phone_name, corpus_name=self.cypher_safe_name)
        results = self.execute_cypher(statement)
        return [r['label'] for r in results]

    @property
    def words(self):
        """
        Get a list of all word labels in the corpus.

        Returns
        -------
        list
            All word labels in the corpus
        """
        statement = '''MATCH (p:{word_name}_type:{corpus_name}) return p.label as label'''.format(
            word_name=self.word_name, corpus_name=self.cypher_safe_name)
        results = self.execute_cypher(statement)
        return [r['label'] for r in results]
