import os
import logging
import time
from collections import defaultdict

from .base import BaseContext

from ..sql.models import (Base, Annotation, Property, NumericProperty,
                    AnnotationType, PropertyType, Discourse, Speaker, SoundFile)

from ..sql.helper import get_or_create

from ..acoustics.io import add_acoustic_info

from ..io.importer import (data_to_graph_csvs, import_csvs,
                    data_to_type_csvs, import_type_csvs)

from py2neo.cypher.error.schema import IndexAlreadyExists

class ImportContext(BaseContext):
    def add_types(self, types, type_headers):
        '''
        This function imports types of annotations into the corpus.

        Parameters
        ----------
        parsed_data: dict
            Dictionary with keys for discourse names and values of :class:`polyglotdb.io.helper.DiscourseData`
            objects
        '''
        data_to_type_csvs(self, types, type_headers)
        import_type_csvs(self, type_headers)

    def initialize_import(self):
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

    def finalize_import(self):
        self.encode_hierarchy()
        self.hierarchy = self.generate_hierarchy()
        self.save_variables()

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
        data_to_graph_csvs(self, data)
        import_csvs(self, data)
        self.update_sql_database(data)
        self.hierarchy.update(data.hierarchy)
        add_acoustic_info(self, data)


        log.info('Finished adding discourse {}!'.format(data.name))
        log.debug('Total time taken: {} seconds'.format(time.time() - begin))

    def load(self, parser, path):
        if os.path.isdir(path):
            self.load_directory(parser, path)
        else:
            self.load_discourse(parser, path)

    def load_discourse(self, parser, path):
        data = parser.parse_discourse(path)
        self.initialize_import()
        self.add_types(*data.types(self.corpus_name))
        self.add_discourse(data)
        self.finalize_import()

    def load_directory(self, parser, path):
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
        self.initialize_import()
        if call_back is not None:
            call_back('Parsing types...')
            call_back(0,len(file_tuples))
            cur = 0
        types = defaultdict(set)
        type_headers = None
        for i, t in enumerate(file_tuples):
            if parser.stop_check is not None and parser.stop_check():
                return
            if call_back is not None:
                call_back('Parsing types from file {} of {}...'.format(i+1, len(file_tuples)))
                call_back(i)
            root, filename = t
            path = os.path.join(root,filename)
            discourse_types, headers = parser.parse_types(path, self.corpus_name)
            if type_headers is None:
                type_headers = headers
            for k, v in discourse_types.items():
                types[k].update(v)
        if call_back is not None:
            call_back('Importing types...')
        self.add_types(types, type_headers)

        if call_back is not None:
            call_back('Parsing files...')
            call_back(0,len(file_tuples))
            cur = 0

        for i, t in enumerate(file_tuples):
            if parser.stop_check is not None and parser.stop_check():
                return
            root, filename = t
            name = os.path.splitext(filename)[0]
            if call_back is not None:
                call_back('Parsing file {} of {} ({})...'.format(i+1, len(file_tuples), name))
                call_back(i)
            path = os.path.join(root,filename)
            data = parser.parse_discourse(path)
            self.add_discourse(data)
        self.finalize_import()
        parser.call_back = call_back

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
        for s in data.speakers:
            speaker, _ = get_or_create(self.sql_session, Speaker, name = s)
            discourse.speakers.append(speaker)
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
