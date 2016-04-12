
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

    def encode_syllables(self):
        onsets = self.find_onsets()
        onsets = {k: v / sum(onsets.values()) for k,v in onsets.items()}
        codas = self.find_codas()
        codas = {k: v / sum(codas.values()) for k,v in codas.items()}

        statement = '''MATCH (n:{corpus_name}:syllabic) return n.label as label'''.format(self.corpus_name)
        res = self.execute_cypher(statement)
        syllabics = set(x.label for x in res)

        word = getattr(self, self.word_name)
        phones = getattr(word, self.phone_name)
        q = self.query_graph(word)
        q = q.columns(word.id.column_name('id'), phones.id.column_name('phone_id'),
                    phones.label.column_name('phones'))
        results = q.all()
        boundaries = []
        for w in results:
            cons = []
            cur_vow_id = None
            cur_ons_id = None
            cur_coda_id = None
            phones = [x for x in w.phones]
            phone_ids = [x for x in w.phone_id]
            intervocalic = []
            while len(phones) > 0:
                p = phones.pop(0)
                id = phone_ids.pop(0)
                if p in syllabics:
                    if cur_vow_id is None:
                        cur_vow_id = id
                    else:
                        #syllabic
                        pass
                elif cur_ons_id is None:
                    cur_ons_id = id
