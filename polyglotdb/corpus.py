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

from .io.graph import (data_to_graph_csvs, import_csvs, time_data_to_csvs,
                    import_utterance_csv, import_syllable_csv,
                    data_to_type_csvs, import_type_csvs, initialize_csv,
                    initialize_csvs_header)

from .graph.query import GraphQuery
from .graph.func import Max
from .graph.attributes import AnnotationAttribute, PauseAnnotation

from .sql.models import (Base, Word, WordProperty, WordPropertyType,
                    InventoryItem, AnnotationType, SoundFile, Discourse)

from sqlalchemy import create_engine

from .sql.config import Session

from .sql.helper import get_or_create

from .sql.query import Lexicon, Inventory

from .graph.cypher import discourse_query

from .acoustics.io import add_acoustic_info

from .acoustics import acoustic_analysis

from .acoustics.query import AcousticQuery

from .exceptions import NoSoundFileError, CorpusConfigError, GraphQueryError

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

        self.engine = create_engine(self.config.sql_connection_string)
        Session.configure(bind=self.engine)
        if not os.path.exists(self.config.db_path):
            Base.metadata.create_all(self.engine)

        self.relationship_types = set()
        self.is_timed = False
        self.hierarchy = {}
        self._has_sound_files = None

        self.lexicon = Lexicon(self)

        self.inventory = Inventory(self)

    @property
    def discourses(self):
        q = self.sql_session.query(Discourse)
        results = [d.name for d in q.all()]
        return results

    def discourse_sound_file(self, discourse):
        q = self.sql_session.query(SoundFile).join(SoundFile.discourse)
        q = q.filter(Discourse.name == discourse)
        sound_file = q.first()
        return sound_file

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

        self.graph.cypher.execute('''MATCH (n:%s) DETACH DELETE n''' % (self.corpus_name))

        self.relationship_types = set()
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
        if annotation_type.type not in self.relationship_types:
            raise(GraphQueryError('The graph does not have any annotations of type \'{}\'.  Possible types are: {}'.format(annotation_type.name, ', '.join(sorted(self.relationship_types)))))
        return GraphQuery(self, annotation_type, self.is_timed)

    @property
    def has_sound_files(self):
        if self._has_sound_files is None:
            self._has_sound_files = self.sql_session.query(SoundFile).first() is not None
        return self._has_sound_files

    @property
    def lowest_annotation(self):
        values = self.hierarchy.values()
        for k in self.hierarchy.keys():
            if k not in values:
                return getattr(self, k)
        return None

    def query_acoustics(self, graph_query):
        if not self.has_sound_files:
            raise(NoSoundFileError)
        return AcousticQuery(self, graph_query)

    def analyze_acoustics(self):
        if not self.has_sound_files:
            raise(NoSoundFileError)
        acoustic_analysis(self)

    def encode_pauses(self, pause_words):
        q = self.query_graph(self.word)
        if isinstance(pause_words, (list, tuple, set)):
            q = q.filter(self.word.label.in_(pause_words))
        elif isinstance(pause_words, str):
            q = q.filter(self.word.label.regex(pause_words))
        else:
            raise(NotImplementedError)
        q.set(pause = True)

    def encode_utterances(self, min_pause_length = 0.5, min_utterance_length = 0):
        initialize_csv('utterance', self.config.temporary_directory('csv'))
        for d in self.discourses:
            utterances = self.get_utterances(d, min_pause_length, min_utterance_length)
            time_data_to_csvs('utterance', self.config.temporary_directory('csv'), d, utterances)
        import_utterance_csv(self)
        self.hierarchy['word'] = 'utterance'
        self.hierarchy['utterance'] = None
        self.relationship_types.add('utterance')

    def encode_syllables(self, syllable_phones):
        base = self.lowest_annotation
        for d in self.discourses:
            syllables = self.get_syllables(d, syllable_phones)
            time_data_to_csvs('syllable', self.config.temporary_directory('csv'), d, syllables)
            import_syllable_csv(self, d, base.type)
        self.hierarchy[base.type] = 'syllable'
        self.hierarchy['syllable'] = 'word'
        self.relationship_types.add('syllable')

    def get_syllables(self, discourse, syllable_phones):
        base = self.lowest_annotation

        q = self.query_graph(self.word).filter(self.word.discourse == discourse)
        q = q.times().order_by(self.word.begin)
        utterances = q.all()

        if not utterances:
            q = self.query_graph(self.word).filter(self.word.discourse == discourse)
            q = q.times().order_by(self.word.begin)

            results = q.all()
            begin = results[0].begin
            end = results[-1].end
            utterances = [{'begin':begin, 'end':end}]

        q = self.query_graph(base).filter(base.label.in_(syllable_phones))
        q = q.filter(base.discourse == discourse)
        q = q.times().duration().order_by(base.begin)
        results = q.all()

        syllables = []
        utterance_ind = 0
        r_ind = 0
        for i, u in enumerate(utterances):
            bounds = (u['begin'], u['end'])
            syl_begins = []
            while True:
                try:
                    if results[r_ind].begin >= u['end']:
                        break
                except IndexError:
                    break
                syl_begins.append(results[r_ind].begin)
                r_ind += 1
            syl_begins = syl_begins[1:]
            if syl_begins:
                for b in range(len(syl_begins)):
                    end = syl_begins[b]
                    if b == 0:
                        begin = bounds[0]
                    else:
                        begin = syl_begins[b-1]
                    syllables.append((begin, end))
                syllables.append((syl_begins[b], bounds[1]))
            else:
                syllables.append(bounds)
        return syllables

    def get_utterances(self, discourse, pause_words,
                min_pause_length = 0.5, min_utterance_length = 0):

        q = self.query_graph(self.pause).filter(self.pause.discourse == discourse)
        q = q.filter(self.pause.duration >= min_pause_length)
        q = q.clear_columns().times().duration().order_by(self.pause.begin)
        results = q.all()
        collapsed_results = []
        for i, r in enumerate(results):
            if len(collapsed_results) == 0:
                collapsed_results.append(r)
                continue
            if r.begin == collapsed_results[-1].end:
                collapsed_results[-1].end = r.end
            else:
                collapsed_results.append(r)
        utterances = []
        q = self.query_graph(self.word).filter(self.word.discourse == discourse)
        maxt = q.aggregate(Max(self.word.end))
        if len(results) < 2:
            begin = 0
            if len(results) == 0:
                return [(begin,maxt)]
            if results[0].begin == 0:
                return [(results[0].end, maxt)]
            if results[0].end == maxt:
                return [(begin, results[0].end)]

        if results[0].begin != 0:
            current = 0
        else:
            current = None
        for i, r in enumerate(collapsed_results):
            if current is not None:
                if r.begin - current > min_utterance_length:
                    utterances.append((current, r.begin))
                elif i == len(results) - 1:
                    utterances[-1] = (utterances[-1][0], r.begin)
                elif len(utterances) != 0:
                    dist_to_prev = current - utterances[-1][1]
                    dist_to_foll = r.end - r.begin
                    if dist_to_prev <= dist_to_foll:
                        utterances[-1] = (utterances[-1][0], r.begin)
            current = r.end
        if current < maxt:
            utterances.append((current, maxt))
        return utterances

    def add_types(self, parsed_data):
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
        add_acoustic_info(self, data)

        log.info('Finished adding discourse {}!'.format(data.name))
        log.debug('Total time taken: {} seconds'.format(time.time() - begin))

    def update_sql_database(self, data):
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
