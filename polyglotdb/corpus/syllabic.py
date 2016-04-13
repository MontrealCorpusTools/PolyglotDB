
from .featured import FeaturedContext


class SyllabicContext(FeaturedContext):
    def find_onsets(self):
        statement = '''match (w:{word_name}:{corpus_name})
where (w)<-[:contained_by]-()-[:is_a]->(:syllabic)
with w
match (n:{phone_name}:{corpus_name})-[:is_a]->(t:{corpus_name}:syllabic),
(n)-[:contained_by]->(w)
with w, n
order by n.begin
with w,collect(n)[0..2] as coll unwind coll as n

MATCH (pn:{phone_name}:{corpus_name})-[:contained_by]->(w)
where not (pn)<-[:precedes]-()-[:contained_by]->(w)
with w, n,pn
match p = shortestPath((pn)-[:precedes*0..10]->(n))
with extract(x in nodes(p)[0..size(nodes(p))-1]|x.label) as onset
return onset, count(onset) as freq'''.format(corpus_name = self.corpus_name,
                                            word_name = self.word_name,
                                            phone_name = self.phone_name)

        res = self.execute_cypher(statement)
        data = {}
        for r in res:
            data[tuple(r.onset)] = r.freq
        return data

    def find_codas(self):
        statement = '''match (w:{word_name}:{corpus_name})
where (w)<-[:contained_by]-()-[:is_a]->(:syllabic)
with w
match (n:{phone_name}:{corpus_name})-[:is_a]->(t:{corpus_name}:syllabic),
(n)-[:contained_by]->(w)
with w, n
order by n.begin DESC
with w,collect(n)[0..2] as coll unwind coll as n

MATCH (pn:{phone_name}:{corpus_name})-[:contained_by]->(w)
where not (pn)-[:precedes]->()-[:contained_by]->(w)
with w, n,pn
match p = shortestPath((n)-[:precedes*0..10]->(pn))
with extract(x in nodes(p)[1..size(nodes(p))]|x.label) as coda
return coda, count(coda) as freq'''.format(corpus_name = self.corpus_name,
                                            word_name = self.word_name,
                                            phone_name = self.phone_name)

        res = self.execute_cypher(statement)
        data = {}
        for r in res:
            data[tuple(r.coda)] = r.freq
        return data

    def encode_syllabic_segments(self, phones):
        self.encode_class(phones, 'syllabic')

    def encode_number_of_syllables(self):
        pass

    def encode_syllables(self, call_back = None, stop_check = None):
        import math
        onsets = self.find_onsets()
        onsets[None] = len(onsets.keys()) / 10
        onsets = {k: math.log(v / sum(onsets.values())) for k,v in onsets.items()}
        codas = self.find_codas()
        codas[None] = len(codas.keys()) / 5
        codas = {k: math.log(v / sum(codas.values())) for k,v in codas.items()}

        def split_ons_coda(string):
            if len(string) == 0:
                return None
            max_prob = -10000
            best = None
            for i in range(len(string) + 1):
                prob = 0
                ons = string[:i]
                cod = string[i:]
                if ons not in onsets:
                    prob += onsets[None]
                else:
                    prob += onsets[ons]
                if cod not in codas:
                    prob += codas[None]
                else:
                    prob += codas[cod]
                if prob > max_prob:
                    max_prob = prob
                    best = i
            return best

        statement = '''MATCH (n:{corpus_name}:syllabic) return n.label as label'''.format(self.corpus_name)
        res = self.execute_cypher(statement)
        syllabics = set(x.label for x in res)

        word = getattr(self, self.word_name)
        phones = getattr(word, self.phone_name)
        if self.config.query_behavior == 'discourse':
            splits = self.discourses
            process_string = 'Processing discourse {} of {} ({})...'
        else:
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
            q = self.query_graph(word)
            if self.config.query_behavior == 'discourse':
                q.filter(word.discourse.name == s)
            else:
                q.filter(word.speaker.name == s)
            q = q.columns(word.id.column_name('id'), phones.id.column_name('phone_id'),
                        phones.label.column_name('phones'))
            results = q.all()
            boundaries = []
            for w in results:
                phones = w.phones
                phone_ids = w.phone_id
                vow_inds = [i for i,x in enumerate(phones) if x in syllabic]
                for j, i in enumerate(vow_inds):
                    cur_vow_id = phone_ids[i]
                    if j == 0:
                        if i != 0:
                            cur_ons_id = phone_ids[0]
                        else:
                            cur_ons_id = None
                    else:
                        prev_vowel_ind = vow_inds[j - 1]
                        cons_string = phones[prev_vowel_ind + 1:i]
                        split = split_ons_coda(cons_string)
                        if split is None:
                            cur_ons_id = None
                        else:
                            cur_ons_id = phone_ids[prev_vowel_ind + 1 + split]

                    if j == len(vow_inds) < 1:
                        if i != len(phones) - 1:
                            cur_coda_id = phone_ids[-1]
                        else:
                            cur_coda_id = None
                    else:
                        foll_vowel_ind = vow_inds[j + 1]
                        cons_string = phones[i + 1:foll_vowel_ind]
                        split = split_ons_coda(cons_string)
                        if split is None:
                            cur_coda_id = None
                        else:
                            cur_coda_id = phone_ids[i + split]
                    row = {'vowel_id': cur_vow_id, 'onset_id': cur_ons_id,
                            'coda_id':cur_coda_id}
                    boundaries.append(row)
            syllables_data_to_csvs(self, boundaries, s)

