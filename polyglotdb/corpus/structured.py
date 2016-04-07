
from .base import BaseContext

from ..structure import Hierarchy

from ..graph.helper import value_for_cypher

class StructuredContext(BaseContext):
    def generate_hierarchy(self):
        exists_statement = '''MATCH (c:Corpus)<-[:contained_by]-(s)
        WHERE c.name = {corpus_name} RETURN c LIMIT 1'''
        if self.execute_cypher(exists_statement, corpus_name = self.corpus_name):
            hierarchy_statement = '''MATCH
            path = (c:Corpus)<-[:contained_by*]-(n)-[:is_a]->(nt)
            where c.name = {corpus_name}
            WITH n, nt, path
            OPTIONAL MATCH (n)<-[:annotates]-(subs)
            return n,nt, path, collect(subs) as subs
            order by size(nodes(path))'''
            results = self.execute_cypher(hierarchy_statement, corpus_name = self.corpus_name)
            sup = None
            data = {}
            subs = {}
            token_properties = {}
            type_properties = {}
            type_subsets = {}
            token_subsets = {}
            for r in results:
                at = list(r.n.labels)[0]
                data[at] = sup
                sup = at
                if r.subs is not None:
                    subs[at] = set([list(x.labels)[0] for x in r.subs])
                token_subsets[at] = set()
                type_subsets[at] = set()
                token_properties[at] = set([('id', type(''))])
                type_properties[at] = set()
                for k, v in r.n.properties.items():
                    if k == 'subsets':
                        token_subsets[at].update(v)
                    else:
                        token_properties[at].add((k, type(v)))

                for k, v in r.nt.properties.items():
                    if k == 'subsets':
                        type_subsets[at].update(v)
                    else:
                        type_properties[at].add((k, type(v)))
            h = Hierarchy(data)
            h.subannotations = subs
            h.subset_types = type_subsets
            h.token_properties = token_properties
            h.subset_tokens = token_subsets
            h.type_properties = type_properties
        else:
            all_labels = self.graph.node_labels
            linguistic_labels = []
            discourses = set(self.discourses)
            reserved = set(['Speaker', 'Discourse', 'speech', 'pause'])
            exists_statement = '''MATCH (n:«labels») RETURN 1 LIMIT 1'''
            for label in all_labels:
                if label in discourses:
                    continue
                if label in reserved:
                    continue
                if label == self.corpus_name:
                    continue
                if not self.execute_cypher(exists_statement, labels = [self.corpus_name, label]):
                    continue
                if label.endswith('_type'):
                    continue
                linguistic_labels.append(label)
            h = {}
            subs = {}
            contain_statement = '''MATCH (t:{corpus_name}:«super_label»)<-[:contained_by]-(n:{corpus_name}:«sub_label») RETURN 1 LIMIT 1'''.format(corpus_name = self.corpus_name)
            annotate_statement = '''MATCH (t:{corpus_name}:«super_label»)<-[:annotates]-(n:{corpus_name}:«sub_label») RETURN 1 LIMIT 1'''.format(corpus_name = self.corpus_name)
            for sub_label in linguistic_labels:
                for sup_label in linguistic_labels:
                    if sub_label == sup_label:
                        continue
                    if self.execute_cypher(contain_statement, super_label = sup_label, sub_label = sub_label):
                        h[sub_label] = sup_label
                        break
                    if self.execute_cypher(annotate_statement, super_label = sup_label, sub_label = sub_label):
                        if sup_label not in subs:
                            subs[sup_label] = set([])
                        subs[sup_label].add(sub_label)
                        break
                else:
                    h[sub_label] = None
            h = Hierarchy(h)
            h.subannotations = subs
        return h

    def reset_hierarchy(self):
        self.execute_cypher('''MATCH (c:Corpus)<-[:contained_by*]-(n)-[:is_a]->(t)
                                WHERE c.name = '{}'
                                WITH n, t, c
                                OPTIONAL MATCH (t)<-[:annotates]-(a)
                                DETACH DELETE a, t, n'''.format(self.corpus_name))

    def encode_hierarchy(self):
        self.reset_hierarchy()
        hierarchy_template = '''({super})<-[:contained_by]-({sub})-[:is_a]->({sub_type})'''
        subannotation_template = '''({super})<-[:annotates]-({sub})'''
        statement = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MERGE {merge_statement}'''
        merge_statements = []
        for at in self.hierarchy.highest_to_lowest:
            sup = self.hierarchy[at]
            if sup is None:
                sup = 'c'
            else:
                sup = '{}'.format(sup)
            try:
                token_props = []
                for name, t in self.hierarchy.token_properties[at]:
                    if name == 'id':
                        continue
                    v = ''
                    if t == int:
                        v = 0
                    elif t == float:
                        v = 0.0
                    elif t in (list, tuple, set):
                        v = []
                    token_props.append('{}: {}'.format(name, value_for_cypher(v)))
                if token_props:
                    token_props = ', '+ ', '.join(token_props)
                else:
                    token_props = ''
            except KeyError:
                token_props = ''
            try:
                type_props = []
                for name, t in self.hierarchy.type_properties[at]:
                    v = ''
                    if t == int:
                        v = 0
                    elif t == float:
                        v = 0.0
                    elif t in (list, tuple, set):
                        v = []
                    type_props.append('{}: {}'.format(name, value_for_cypher(v)))
                if type_props:
                    type_props = ', '+ ', '.join(type_props)
                else:
                    type_props = ''
            except KeyError:
                type_props = ''

            try:
                type_subsets = sorted(self.hierarchy.subset_types[at])
            except KeyError:
                type_subsets = []

            try:
                token_subsets = sorted(self.hierarchy.subset_tokens[at])
            except KeyError:
                token_subsets = []
            try:
                subannotations = sorted(self.hierarchy.subannotations[at])
            except KeyError:
                subannotations = []
            sub = "{0}:{0} {{label: '', subsets: {2}, begin:0, end: 0{1}}}".format(at, token_props, token_subsets)
            sub_type = "{0}_type:{0}_type {{label: '', subsets: {2}{1}}}".format(at, type_props, type_subsets)
            merge_statements.append(hierarchy_template.format(super = sup, sub = sub,
                                                    sub_type = sub_type))
            for sa in subannotations:
                sa = "{0}:{0} {{label: '', begin:0, end: 0}}".format(sa)
                merge_statements.append(subannotation_template.format(super = at, sub = sa))


        statement = statement.format(merge_statement = '\nMERGE '.join(merge_statements))
        self.execute_cypher(statement, corpus_name = self.corpus_name)
