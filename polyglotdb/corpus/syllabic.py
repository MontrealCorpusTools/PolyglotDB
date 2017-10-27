from uuid import uuid1

import re
from ..io.importer import (syllables_data_to_csvs, import_syllable_csv,
                           nonsyls_data_to_csvs, import_nonsyl_csv,
                           create_syllabic_csvs, create_nonsyllabic_csvs,
                           syllables_enrichment_data_to_csvs, import_syllable_enrichment_csvs)

# from ..io.importer import syllables_enrichment_data_to_csvs
from ..io.helper import make_type_id

from ..syllabification.probabilistic import norm_count_dict, split_nonsyllabic_prob, split_ons_coda_prob
from ..syllabification.maxonset import split_nonsyllabic_maxonset, split_ons_coda_maxonset
from .utterance import UtteranceContext


class SyllabicContext(UtteranceContext):
    def find_onsets(self):
        """
        Gets syllable onsets

        Returns
        -------
        data : dict
            A dictionary with onset values as keys and frequency values as values

        """
        statement = '''match (w:{word_name}:{corpus_name})
where (w)<-[:contained_by*1..2]-()-[:is_a]->(:syllabic)
with w
match (n:{phone_name}:{corpus_name})-[:is_a]->(t:{corpus_name}:syllabic),
(n)-[:contained_by*1..2]->(w)
with w, n
order by n.begin
with w,collect(n)[0..1] as coll unwind coll as n

MATCH (pn:{phone_name}:{corpus_name})-[:contained_by*1..2]->(w)
where not (pn)<-[:precedes]-()-[:contained_by*1..2]->(w)
with w, n,pn
match p = shortestPath((pn)-[:precedes*0..10]->(n))
with extract(x in nodes(p)[0..-1]|x.label) as onset
return onset, count(onset) as freq'''.format(corpus_name=self.cypher_safe_name,
                                             word_name=self.word_name,
                                             phone_name=self.phone_name)
        res = self.execute_cypher(statement)
        data = {}
        for r in res:
            data[tuple(r['onset'])] = r['freq']
        return data

    def find_codas(self):
        """
        Gets syllable codas

        Returns
        -------
        data : dict
            A dictionary with coda values as keys and frequency values as values
        """
        statement = '''match (w:{word_name}:{corpus_name})
where (w)<-[:contained_by*1..2]-()-[:is_a]->(:syllabic)
with w
match (n:{phone_name}:{corpus_name})-[:is_a]->(t:{corpus_name}:syllabic),
(n)-[:contained_by*1..2]->(w)
with w, n
order by n.begin DESC
with w,collect(n)[0..1] as coll unwind coll as n

MATCH (pn:{phone_name}:{corpus_name})-[:contained_by*1..2]->(w)
where not (pn)-[:precedes]->()-[:contained_by*1..2]->(w)
with w, n,pn
match p = shortestPath((n)-[:precedes*0..10]->(pn))
with extract(x in nodes(p)[1..]|x.label) as coda
return coda, count(coda) as freq'''.format(corpus_name=self.cypher_safe_name,
                                           word_name=self.word_name,
                                           phone_name=self.phone_name)

        res = self.execute_cypher(statement)
        data = {}
        for r in res:
            data[tuple(r['coda'])] = r['freq']
        return data

    def encode_syllabic_segments(self, phones):
        """
        Encode a list of phones as 'syllabic'

        Parameters
        ----------
        phones : list
            A list of vowels and syllabic consonants
        """
        self.encode_class(phones, 'syllabic')

    def reset_syllables(self, call_back=None, stop_check=None):
        """ Resets syllables, removes syllable annotation, removes onset, coda, and nucleus labels """
        if call_back is not None:
            call_back('Resetting syllables...')
            number = self.execute_cypher(
                '''MATCH (n:syllable:%s) return count(*) as number ''' % (self.cypher_safe_name)).single()['number']
            call_back(0, number)
        statement = '''MATCH (st:syllable_type:{corpus})
                WITH st
                LIMIT 1
                MATCH (p:{phone_name}:{corpus})-[:contained_by]->(s),
                (s:syllable:{corpus})-[:is_a]->(st),
                (s)-[:contained_by]->(w:{word_name}:{corpus})
                with p,s,st,w
                CREATE (p)-[:contained_by]->(w)
                with p, s, st
                DETACH DELETE s, st
                with p,s
                REMOVE p:onset, p:nucleus, p:coda, p.syllable_position
                RETURN count(s) as deleted_count'''.format(corpus=self.cypher_safe_name,
                                                           word_name=self.word_name,
                                                           phone_name=self.phone_name)
        num_deleted = 0
        deleted = 1000
        while deleted > 0:
            if stop_check is not None and stop_check():
                break
            deleted = self.execute_cypher(statement).single()['deleted_count']
            num_deleted += deleted
            if call_back is not None:
                call_back(num_deleted)
        try:
            self.hierarchy.remove_annotation_type('syllable')
            self.hierarchy.remove_token_labels(self, self.phone_name, ['onset', 'coda', 'nucleus'])
            self.hierarchy.remove_token_properties(self, self.phone_name, ['syllable_position'])
            # self.reset_to_old_label()
            self.encode_hierarchy()
        except KeyError:
            pass

    @property
    def has_syllabics(self):
        return 'syllabic' in self.hierarchy.subset_types[self.phone_name]

    @property
    def has_syllables(self):
        return 'syllable' in self.hierarchy.annotation_types

    def encode_syllables(self, algorithm='maxonset', call_back=None, stop_check=None):
        """
        Encodes syllables to a corpus

        Parameters
        ----------
        algorithm : str defaults to 'probabilistic'
            determines which algorithm will be used to encode syllables
        """

        self.reset_syllables(call_back, stop_check)

        onsets = self.find_onsets()
        if algorithm == 'probabilistic':
            onsets = norm_count_dict(onsets, onset=True)
            codas = self.find_codas()
            codas = norm_count_dict(codas, onset=False)
        elif algorithm == 'maxonset':
            onsets = set(onsets.keys())
        else:
            raise (NotImplementedError)

        statement = '''MATCH (n:{}:syllabic) return n.label as label'''.format(self.cypher_safe_name)
        res = self.execute_cypher(statement)
        syllabics = set(x['label'] for x in res)

        word_type = getattr(self, self.word_name)
        phone_type = getattr(word_type, self.phone_name)

        create_syllabic_csvs(self)
        create_nonsyllabic_csvs(self)

        splits = self.speakers
        process_string = 'Processing speaker {} of {} ({})...'
        if call_back is not None:
            call_back(0, len(splits))

        for i, s in enumerate(splits):
            if stop_check is not None and stop_check():
                break
            if call_back is not None:
                call_back(i)
                call_back(process_string.format(i, len(splits), s))
            q = self.query_graph(word_type)
            q = q.filter(word_type.speaker.name == s)
            q = q.order_by(word_type.discourse.name.column_name('discourse'))
            q = q.order_by(word_type.begin)
            q = q.columns(word_type.id.column_name('id'), phone_type.id.column_name('phone_id'),
                          phone_type.label.column_name('phones'),
                          phone_type.begin.column_name('begins'),
                          phone_type.end.column_name('ends'),
                          word_type.discourse.name.column_name('discourse'))
            results = q.all()
            speaker_boundaries = {s: []}
            speaker_non_syls = {s: []}
            prev_id = None
            cur_discourse = None
            for w in results:
                phones = w['phones']
                phone_ids = w['phone_id']
                phone_begins = w['begins']
                phone_ends = w['ends']
                discourse = w['discourse']
                if discourse != cur_discourse:
                    prev_id = None
                    cur_discourse = discourse
                vow_inds = [i for i, x in enumerate(phones) if x in syllabics]
                if len(vow_inds) == 0:
                    cur_id = uuid1()
                    if algorithm == 'probabilistic':
                        split = split_nonsyllabic_prob(phones, onsets, codas)
                    elif algorithm == 'maxonset':
                        split = split_nonsyllabic_maxonset(phones, onsets)
                    label = '.'.join(phones)
                    row = {'id': cur_id, 'prev_id': prev_id,
                           'onset_id': phone_ids[0],
                           'break': split,
                           'coda_id': phone_ids[-1],
                           'begin': phone_begins[0],
                           'label': label,
                           'type_id': make_type_id([label], self.corpus_name),
                           'end': phone_ends[-1]}
                    speaker_non_syls[s].append(row)
                    prev_id = cur_id
                    continue
                for j, i in enumerate(vow_inds):
                    cur_id = uuid1()
                    cur_vow_id = phone_ids[i]
                    begin = phone_begins[i]
                    end = phone_ends[i]
                    if j == 0:
                        begin_ind = 0
                        if i != 0:
                            cur_ons_id = phone_ids[begin_ind]
                            begin = phone_begins[begin_ind]
                        else:
                            cur_ons_id = None
                    else:
                        prev_vowel_ind = vow_inds[j - 1]
                        cons_string = phones[prev_vowel_ind + 1:i]
                        if algorithm == 'probabilistic':
                            split = split_ons_coda_prob(cons_string, onsets, codas)
                        elif algorithm == 'maxonset':
                            split = split_ons_coda_maxonset(cons_string, onsets)
                        if split is None:
                            cur_ons_id = None
                            begin_ind = i
                        else:
                            begin_ind = prev_vowel_ind + 1 + split
                            cur_ons_id = phone_ids[begin_ind]

                    if j == len(vow_inds) - 1:
                        end_ind = len(phones) - 1
                        if i != len(phones) - 1:
                            cur_coda_id = phone_ids[end_ind]
                            end = phone_ends[end_ind]
                        else:
                            cur_coda_id = None
                    else:
                        foll_vowel_ind = vow_inds[j + 1]
                        cons_string = phones[i + 1:foll_vowel_ind]
                        if algorithm == 'probabilistic':
                            split = split_ons_coda_prob(cons_string, onsets, codas)
                        elif algorithm == 'maxonset':
                            split = split_ons_coda_maxonset(cons_string, onsets)
                        if split is None:
                            cur_coda_id = None
                            end_ind = i
                        else:
                            end_ind = i + split
                            cur_coda_id = phone_ids[end_ind]
                    begin = phone_begins[begin_ind]
                    end = phone_ends[end_ind]
                    label = '.'.join(phones[begin_ind:end_ind + 1])
                    row = {'id': cur_id, 'prev_id': prev_id,
                           'vowel_id': cur_vow_id, 'onset_id': cur_ons_id,
                           'label': label,
                           'type_id': make_type_id([label], self.corpus_name),
                           'coda_id': cur_coda_id, 'begin': begin, 'end': end}
                    speaker_boundaries[s].append(row)
                    prev_id = cur_id
            syllables_data_to_csvs(self, speaker_boundaries)
            nonsyls_data_to_csvs(self, speaker_non_syls)
        import_syllable_csv(self, call_back, stop_check)
        import_nonsyl_csv(self, call_back, stop_check)
        if stop_check is not None and stop_check():
            return

        if call_back is not None:
            call_back('Cleaning up...')
        self.execute_cypher(
            'MATCH (n:{}:syllable) where n.prev_id is not Null REMOVE n.prev_id'.format(self.cypher_safe_name))

        self.hierarchy.add_annotation_type('syllable', above=self.phone_name, below=self.word_name)
        self.hierarchy.add_token_labels(self, self.phone_name, ['onset', 'coda', 'nucleus'])
        self.hierarchy.add_token_properties(self, self.phone_name, [('syllable_position', str)])
        self.encode_hierarchy()
        if call_back is not None:
            call_back('Finished!')
            call_back(1, 1)

    def enrich_syllables(self, syllable_data, type_data=None):
        """
        Sets the data type and syllable data, initializes importers for syllable data, adds features to hierarchy for a phone

        Parameters
        ----------
        syllable_data : dict
            the enrichment data
        type_data : dict
            By default None
        """

        if type_data is None:
            type_data = {k: type(v) for k, v in next(iter(syllable_data.values())).items()}

            # labels = set(self.lexicon.syllables())
            #  syllable_data = {k: v for k,v in syllable_data.items() if k in labels}
        syllables_enrichment_data_to_csvs(self, syllable_data)
        import_syllable_enrichment_csvs(self, type_data)
        # self.hierarchy.add_type_labels(self, 'syllable', ['test'])
        self.hierarchy.add_type_properties(self, 'syllable', type_data.items())

        self.encode_hierarchy()

    def _generate_stress_enrichment(self, pattern):
        """
        encode stress based off of CMUDict cues

        """

        syllable = self.syllable
        all_syls = self.query_graph(syllable).all()
        enrich_dict = {}

        for i, x in enumerate(all_syls.cursors):
            for item in x:
                syl = item[0]['label']
                splitsyl = syl.split('.')
                nucleus = splitsyl[0]
                for j, seg in enumerate(splitsyl):
                    if re.search(pattern, seg) is not None:
                        nucleus = seg

                r = re.search(pattern, nucleus)
                if r is not None:
                    end = nucleus[r.start(0):r.end(0)].replace("_", "")
                    nucleus = re.sub(pattern, "", nucleus)
                    fullpatt = str(nucleus) + str(pattern).replace("$", "")
                    syl = re.sub(fullpatt, nucleus, syl)

                    enrich_dict.update({syl: {'stress': end}})

        return enrich_dict

    def _generate_tone_enrichment(self, pattern):
        """
        encode tone based off of CMUDict cues
        """
        syllable = self.syllable
        all_syls = self.query_graph(syllable).all()
        enrich_dict = {}
        for x in all_syls.cursors:
            for item in x:
                syl = item[0]['label']
                splitsyl = syl.split('.')
                nucleus = splitsyl[0]
                for seg in splitsyl:
                    if re.search(pattern, seg) is not None:
                        nucleus = seg
                # enrich_dict.update({syl:{}})

                r = re.search(pattern, nucleus)
                if r is not None:
                    end = nucleus[r.start(0):r.end(0)].replace("_", "")
                    nucleus = re.sub(pattern, "", nucleus)
                    fullpatt = str(nucleus) + str(pattern).replace("$", "")
                    syl = re.sub(fullpatt, nucleus, syl)

                    enrich_dict.update({syl: {'tone': end}})
        return enrich_dict

    def encode_stress_to_syllables(self, regex=None, clean_phone_label=True):
        if regex is None:
            regex = '[0-9]'

        enrich_dict = self._generate_stress_enrichment(regex)

        if clean_phone_label:
            self.remove_pattern(regex)
        self.enrich_syllables(enrich_dict)
        self.encode_hierarchy()

    def encode_tone_to_syllables(self, regex=None, clean_phone_label=True):
        if regex is None:
            regex = '[0-9]'

        enrich_dict = self._generate_tone_enrichment(regex)

        if clean_phone_label:
            self.remove_pattern(regex)
        self.enrich_syllables(enrich_dict)
        self.encode_hierarchy()

    def encode_stress_from_word_property(self, word_property_name):
        if 'syllable' not in self.annotation_types:
            raise Exception('Syllables have not been encoded.')
        if not self.hierarchy.has_type_property(self.word_name, word_property_name):
            raise Exception('Word types do not have a property {}.'.format(word_property_name))
        if not self.hierarchy.has_type_property(self.word_name, 'num_syllables'):
            self.encode_count('word', 'syllable', 'num_syllables')
        if not self.hierarchy.has_type_property('syllable', 'position_in_word'):
            self.encode_position('word', 'syllable', 'position_in_word')

        for s in self.speakers:
            statement = '''MATCH (s:syllable:{corpus_name})-[:spoken_by]->(speaker:Speaker:{corpus_name}),
                        (s)-[:contained_by]->(w:word:{corpus_name})-[:is_a]->(wt:word_type:{corpus_name})
                        WHERE speaker.name = $speaker_name
                        AND wt.{word_property_name} is not null
                        WITH s, w, split(wt.{word_property_name}, '-') as stresses
                        WHERE length(stresses) = w.num_syllables
                        SET s.stress = stresses[s.position_in_word-1]'''.format(
                corpus_name=self.cypher_safe_name, word_property_name=word_property_name)
            self.execute_cypher(statement, speaker_name=s)
        self.hierarchy.add_token_properties(self, 'syllable', [('stress', str)])
        self.encode_hierarchy()
