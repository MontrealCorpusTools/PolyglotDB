import os
import logging
import time
import csv
from collections import defaultdict

from ..sql.models import (Base, Annotation, Property, NumericProperty, SpeaksIn,
                    AnnotationType, PropertyType, Discourse, Speaker, SoundFile)

from ..sql.helper import get_or_create

from ..acoustics.io import setup_audio

from ..io.importer import (data_to_graph_csvs, import_csvs,
                    data_to_type_csvs, import_type_csvs)

from ..exceptions import ParseError

class ImportContext(object):
    def add_types(self, types, type_headers):
        '''
        This function imports types of annotations into the corpus.

        Parameters
        ----------
        parsed_data: dict
            Dictionary with keys for discourse names and values of :class:`~polyglotdb.io.helper.DiscourseData`
            objects
        '''
        data_to_type_csvs(self, types, type_headers)
        import_type_csvs(self, type_headers)

    def initialize_import(self, speakers, token_headers, subannotations = None):
        """ prepares corpus for import of types of annotations """
        directory = self.config.temporary_directory('csv')
        for s in speakers:
            for k, v in token_headers.items():
                path = os.path.join(directory, '{}_{}.csv'.format(s, k))
                with open(path, 'w', newline = '', encoding = 'utf8') as f:
                    w = csv.DictWriter(f, v, delimiter = ',')
                    w.writeheader()
            if subannotations is not None:
                for k,v in subannotations.items():
                    for sub in v:
                        path = os.path.join(directory,'{}_{}_{}.csv'.format(s, k, sub))
                        with open(path, 'w', newline = '', encoding = 'utf8') as f:
                            header = ['id', 'begin', 'end', 'annotation_id', 'label']
                            w = csv.DictWriter(f, header, delimiter = ',')
                            w.writeheader()
        self.execute_cypher('CREATE CONSTRAINT ON (node:Corpus) ASSERT node.name IS UNIQUE')
        self.execute_cypher('CREATE INDEX ON :Discourse(name)')
        self.execute_cypher('CREATE INDEX ON :Speaker(name)')

        self.execute_cypher('''MERGE (n:Corpus {{name: '{}'}}) return n'''.format(self.corpus_name))

    def finalize_import(self, data, call_back = None, stop_check = None):
        """ generates hierarchy and saves variables"""
        import_csvs(self, data, call_back, stop_check)
        self.encode_hierarchy()
        self.hierarchy = self.generate_hierarchy()
        self.save_variables()

    def add_discourse(self, data):
        '''
        Add a discourse to the graph database for corpus.

        Parameters
        ----------
        data : :class:`~polyglotdb.io.helper.DiscourseData`
            Data for the discourse to be added
        '''
        if data.name in self.discourses:
            raise(ParseError('The discourse \'{}\' already exists in this corpus.'.format(data.name)))
        log = logging.getLogger('{}_loading'.format(self.corpus_name))
        log.info('Begin adding discourse {}...'.format(data.name))
        begin = time.time()

        self.execute_cypher(
            '''MERGE (n:Discourse:{corpus_name} {{name: {{discourse_name}}}})'''.format(corpus_name = self.cypher_safe_name),
                    discourse_name = data.name)
        for s in data.speakers:
            self.execute_cypher(
                '''MERGE (n:Speaker:{corpus_name} {{name: {{speaker_name}}}})'''.format(corpus_name = self.cypher_safe_name),
                        speaker_name = s)
        data.corpus_name = self.corpus_name
        data_to_graph_csvs(self, data)
        self.update_sql_database(data)
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
        self.initialize_import(data.speakers, data.token_headers, data.hierarchy.subannotations)
        self.add_types(*data.types(self.corpus_name))
        self.add_discourse(data)
        self.finalize_import(data)
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
        for root, subdirs, files in os.walk(path, followlinks = True):
            for filename in files:
                if parser.stop_check is not None and parser.stop_check():
                    return
                if not parser.match_extension(filename):
                    continue
                file_tuples.append((root, filename))
        if len(file_tuples) == 0:
            raise(ParseError('No files in the specified directory matched the parser. Please check to make sure you have the correct parser.'))
        if call_back is not None:
            call_back('Parsing types...')
            call_back(0,len(file_tuples))
            cur = 0
        speakers = set()
        types = defaultdict(set)
        type_headers = None
        token_headers = None
        for i, t in enumerate(file_tuples):
            if parser.stop_check is not None and parser.stop_check():
                return
            if call_back is not None:
                call_back('Parsing types from file {} of {}...'.format(i+1, len(file_tuples)))
                call_back(i)
            root, filename = t
            path = os.path.join(root,filename)
            try:
                information = parser.parse_information(path, self.corpus_name)
                speakers.update(information['speakers'])
                type_headers = information['type_headers']
                token_headers = information['token_headers']
                subannotations = information['subannotations']
            except ParseError:
                continue
            for k, v in information['types'].items():
                types[k].update(v)
        if call_back is not None:
            call_back('Importing types...')
        self.initialize_import(speakers, token_headers, subannotations)
        self.add_types(types, type_headers)

        if call_back is not None:
            call_back('Parsing files...')
            call_back(0,len(file_tuples))
            cur = 0
        could_not_parse = []
        for i, t in enumerate(file_tuples):
            if parser.stop_check is not None and parser.stop_check():
                return
            root, filename = t
            name = os.path.splitext(filename)[0]
            if call_back is not None:
                call_back('Parsing file {} of {} ({})...'.format(i+1, len(file_tuples), name))
                call_back(i)
            path = os.path.join(root,filename)
            try:
                data = parser.parse_discourse(path)
            except ParseError:
                could_not_parse.append(path)
                continue
            self.add_discourse(data)
        self.finalize_import(data, call_back, parser.stop_check)
        parser.call_back = call_back
        return could_not_parse

    def update_sql_database(self, data):
        '''
        Update the SQL database given a discourse's data.  This function
        adds new words and updates frequencies given occurences in the
        discourse

        Parameters
        ----------
        data : :class:`~polyglotdb.io.helper.DiscourseData`
            Data for the discourse
        '''
        log = logging.getLogger('{}_loading'.format(self.corpus_name))
        log.info('Beginning to import {} into the SQL database...'.format(data.name))
        initial_begin = time.time()

        discourse, _ =  get_or_create(self.sql_session, Discourse, name = data.name)
        for s in data.speakers:
            speaker, _ = get_or_create(self.sql_session, Speaker, name = s)
            sin = SpeaksIn(speaker = speaker, discourse = discourse)
            if s in data.speaker_channel_mapping:
                sin.channel = data.speaker_channel_mapping[s]
            self.sql_session.add(sin)
            discourse.speakers.append(sin)
        phone_cache = defaultdict(set)
        segment_type = data.segment_type
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
                annotation, created = self.lexicon.get_or_create_annotation(d.label, self.word_name)
                if created:
                    for k,v in d.type_properties.items():
                        if v is None:
                            continue
                        prop_type = self.lexicon.get_or_create_property_type(k)
                        if isinstance(v, (int,float)):
                            prop, _ = get_or_create(self.sql_session, NumericProperty, annotation = annotation, property_type = prop_type, value = v)
                        elif isinstance(v, (list, tuple)):
                            prop, _ = get_or_create(self.sql_session, Property, annotation = annotation, property_type = prop_type, value = '.'.join(map(str,v)))
                        else:
                            prop, _ = get_or_create(self.sql_session, Property, annotation = annotation, property_type = prop_type, value = v)

            log.info('Finished importing {} annotations!'.format(level))
            log.debug('Importing {} annotations took: {} seconds.'.format(level, time.time()-begin))

        for level, phones in phone_cache.items():
            for seg in phones:
                p, _ = self.lexicon.get_or_create_annotation(seg, self.phone_name)
        log.info('Finished importing {} to the SQL database!'.format(data.name))
        log.debug('SQL importing took: {} seconds'.format(time.time() - initial_begin))
