import os
import logging
import time
from collections import defaultdict

from .base import BaseContext

from ..sql.models import (Base, Word, WordProperty, WordNumericProperty, WordPropertyType,
                    InventoryItem, AnnotationType, Discourse, Speaker,
                    SoundFile)

from ..sql.helper import get_or_create

from ..acoustics.io import add_acoustic_info

from ..io.importer import (data_to_graph_csvs, import_csvs,
                    data_to_type_csvs, import_type_csvs)

from py2neo.cypher.error.schema import IndexAlreadyExists

class ImportContext(BaseContext):
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
        data_to_type_csvs(self, parsed_data)
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
        self.encode_hierarchy()
        self.hierarchy = self.generate_hierarchy()
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
