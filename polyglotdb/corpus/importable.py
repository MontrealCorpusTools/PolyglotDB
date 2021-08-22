import os
import logging
import time
import csv
import re
from collections import defaultdict
import neo4j

from ..acoustics.io import setup_audio

from ..io.importer import (data_to_graph_csvs, import_csvs,
                           data_to_type_csvs, import_type_csvs)

from ..exceptions import ParseError
from .structured import StructuredContext


class ImportContext(StructuredContext):
    """
    Class that contains methods for dealing with the initial import of corpus data
    """
    def add_types(self, types, type_headers):
        """
        This function imports types of annotations into the corpus.

        Parameters
        ----------
        types: dict
            Dictionary of type information per annotation type (i.e., word, phone, etc)
        type_headers : dict
            Dictionary of header information for the CSV files
        """
        data_to_type_csvs(self, types, type_headers)
        import_type_csvs(self, type_headers)

    def initialize_import(self, speakers, token_headers, subannotations=None):
        """ prepares corpus for import of types of annotations """
        directory = self.config.temporary_directory('csv')
        for s in speakers:
            for k, v in token_headers.items():
                path = os.path.join(directory, '{}_{}.csv'.format(re.sub(r'\W', '_', s), k))
                with open(path, 'w', newline='', encoding='utf8') as f:
                    w = csv.DictWriter(f, v, delimiter=',')
                    w.writeheader()
            if subannotations is not None:
                for k, v in subannotations.items():
                    for sub in v:
                        path = os.path.join(directory, '{}_{}_{}.csv'.format(re.sub(r'\W', '_', s), k, sub))
                        with open(path, 'w', newline='', encoding='utf8') as f:
                            header = ['id', 'begin', 'end', 'annotation_id', 'label']
                            w = csv.DictWriter(f, header, delimiter=',')
                            w.writeheader()

        def _corpus_index(tx):
            tx.run('CREATE CONSTRAINT ON (node:Corpus) ASSERT node.name IS UNIQUE')

        def _discourse_index(tx):
            tx.run('CREATE INDEX ON :Discourse(name)')

        def _speaker_index(tx):
            tx.run('CREATE INDEX ON :Speaker(name)')

        def _corpus_create(tx, corpus_name):
            tx.run('MERGE (n:Corpus {name: $corpus_name}) return n', corpus_name=corpus_name)

        with self.graph_driver.session() as session:
            try:
                session.write_transaction(_corpus_index)
            except neo4j.exceptions.ClientError as e:
                if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                    raise
            try:
                session.write_transaction(_discourse_index)
            except neo4j.exceptions.ClientError as e:
                if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                    raise
            try:
                session.write_transaction(_speaker_index)
            except neo4j.exceptions.ClientError as e:
                if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                    raise
            session.write_transaction(_corpus_create, self.corpus_name)

    def finalize_import(self, speakers, token_headers, hierarchy, call_back=None, stop_check=None):
        """
        Finalize import of discourses through importing CSVs and saving the Hierarchy to the Neo4j database.

        See :meth:`~polyglotdb.io.importer.from_csv.import_csvs` for more details.

        Parameters
        ----------
        data_list : :class:`~polyglotdb.io.helper.DiscourseData` or list
            DiscourseData object or list of DiscourseData objects to import
        call_back : callable
            Function to monitor progress
        stop_check : callable or None
            Function to check whether process should be terminated early
        """
        import_csvs(self, speakers, token_headers, hierarchy, call_back, stop_check)
        self.encode_hierarchy()

    def add_discourse(self, data):
        """
        Set up a discourse to be imported to the Neo4j database

        Parameters
        ----------
        data : :class:`~polyglotdb.io.helper.DiscourseData`
            Data for the discourse to be added
        """
        if data.name in self.discourses:
            raise (ParseError('The discourse \'{}\' already exists in this corpus.'.format(data.name)))
        log = logging.getLogger('{}_loading'.format(self.corpus_name))
        log.info('Begin adding discourse {}...'.format(data.name))
        begin = time.time()

        def _create_speaker_discourse(tx, speaker_name, discourse_name, channel):
            tx.run('''MERGE (n:Speaker:{corpus_name} {{name: $speaker_name}})
                        MERGE (d:Discourse:{corpus_name} {{name: $discourse_name}})
                         MERGE (n)-[r:speaks_in]->(d)
                        WITH r
                        SET r.channel = $channel'''.format(corpus_name=self.cypher_safe_name),
                   speaker_name=speaker_name, discourse_name=discourse_name, channel=channel)

        with self.graph_driver.session() as session:
            for s in data.speakers:
                if s in data.speaker_channel_mapping:
                    session.write_transaction(_create_speaker_discourse, s, data.name, data.speaker_channel_mapping[s])
                else:
                    session.write_transaction(_create_speaker_discourse, s, data.name, 0)
        data.corpus_name = self.corpus_name
        data_to_graph_csvs(self, data)
        self.hierarchy.update(data.hierarchy)
        setup_audio(self, data)

        log.info('Finished adding discourse {}!'.format(data.name))
        log.debug('Total time taken: {} seconds'.format(time.time() - begin))

    def load(self, parser, path):
        """
        Use a specified parser on a path to either a directory or a single
        file

        Parameters
        ----------
        parser : :class:`~polyglotdb.io.parsers.BaseParser`
            The type of parser used for corpus

        path : str
            The location of the corpus

        Returns
        -------
        could_not_parse : list
            list of files that it could not parse
        """

        if os.path.isdir(path):
            print("loading {} with {}".format(path, parser))
            could_not_parse = self.load_directory(parser, path)
        else:
            could_not_parse = self.load_discourse(parser, path)
        return could_not_parse

    def load_discourse(self, parser, path):
        """
        initializes, adds types, adds data, and finalizes import

        Parameters
        ----------
        parser : :class:`~polyglotdb.io.parsers.BaseParser`
                the type of parser used for corpus
        path : str
            the location of the discourse

        Returns
        -------
        empty list

        """
        data = parser.parse_discourse(path)

        # If there is no data, e.g. empty TextGrid, return the empty list early.
        if data is None:
            return []

        self.initialize_import(data.speakers, data.token_headers, data.hierarchy.subannotations)
        self.add_types(*data.types(self.corpus_name))
        self.add_discourse(data)
        speakers = data.speakers
        token_headers = data.token_headers
        self.finalize_import(speakers, token_headers, parser.hierarchy, parser.call_back, parser.stop_check)
        return []

    def load_directory(self, parser, path):
        """
        Checks if it can parse each file in dir,
        initializes, adds types, adds data, and finalizes import

        Parameters
        ----------
        parser : :class:`~polyglotdb.io.parsers.BaseParser`
                the type of parser used for corpus
        path : str
            the location of the directory

        Returns
        -------
        could_not_parse : list
            list of files that were not able to be parsed
        """
        call_back = parser.call_back
        parser.call_back = None
        if call_back is not None:
            call_back('Finding  files...')
            call_back(0, 0)
        file_tuples = []
        for root, subdirs, files in os.walk(path, followlinks=True):
            for filename in files:
                if parser.stop_check is not None and parser.stop_check():
                    return
                if not parser.match_extension(filename):
                    continue
                file_tuples.append((root, filename))
        if len(file_tuples) == 0:
            raise (ParseError(
                'No files in the specified directory matched the parser. '
                'Please check to make sure you have the correct parser.'))
        if call_back is not None:
            call_back('Parsing types...')
            call_back(0, len(file_tuples))
            cur = 0
        speakers = set()
        types = defaultdict(set)
        type_headers = None
        token_headers = None
        subannotations = None
        could_not_parse = {}
        for i, t in enumerate(file_tuples):
            if parser.stop_check is not None and parser.stop_check():
                return
            if call_back is not None:
                call_back('Parsing types from file {} of {}...'.format(i + 1, len(file_tuples)))
                call_back(i)
            root, filename = t
            path = os.path.join(root, filename)
            try:
                information = parser.parse_information(path, self.corpus_name)
                if not information['type_headers']:
                    raise ParseError('There was an issue using this parser to parse the file {}.'.format(path))
                speakers.update(information['speakers'])
                type_headers = information['type_headers']
                token_headers = information['token_headers']
                subannotations = information['subannotations']
            except ParseError as e:
                could_not_parse[path] = str(e)
                continue
            for k, v in information['types'].items():
                types[k].update(v)
        if could_not_parse:
            error_template = '{}: {}'
            errors = [error_template.format(k, v) for k,v in could_not_parse.items()]
            raise ParseError('There were issues parsing the following files with {} parser: {}'.format(
                parser.name, '\n\n'.join(errors)))
        if call_back is not None:
            call_back('Importing types...')
        self.initialize_import(speakers, token_headers, subannotations)
        self.add_types(types, type_headers)

        if call_back is not None:
            call_back('Parsing files...')
            call_back(0, len(file_tuples))
            cur = 0
        for i, t in enumerate(file_tuples):
            if parser.stop_check is not None and parser.stop_check():
                return
            root, filename = t
            name = os.path.splitext(filename)[0]
            if call_back is not None:
                call_back('Parsing file {} of {} ({})...'.format(i + 1, len(file_tuples), name))
                call_back(i)
            path = os.path.join(root, filename)
            try:
                data = parser.parse_discourse(path)
            except ParseError:
                continue
            self.add_discourse(data)
        self.finalize_import(speakers, token_headers, parser.hierarchy, call_back, parser.stop_check)
        parser.call_back = call_back
