import time
from ..query import value_for_cypher
from ..structure import Hierarchy
from .base import BaseContext


def generate_cypher_property_list(property_set):
    """
    Generates a list of properies of cypher queries

    Returns
    -------
    properties : str
        list of properties
    """
    props = []
    for name, t in property_set:
        if name == 'id':
            continue
        v = ''
        if t == int:
            v = 0
        elif t == float:
            v = 0.0
        elif t in (list, tuple, set):
            v = []
        props.append('{}: {}'.format(name, value_for_cypher(v)))
    return ', '.join(props)


class StructuredContext(BaseContext):
    def generate_hierarchy(self):
        """
        Creates the hierarchy, which is information on how the corpus is structured

        Returns
        -------
        :class:`~polyglotdb.structure.Hierarchy`
            the structure of the corpus

        """
        hierarchy_statement = '''MATCH
        path = (c:Corpus)<-[:contained_by*]-(n)-[:is_a]->(nt),
        (c)-[:spoken_by]->(s:Speaker),
        (c)-[:spoken_in]->(d:Discourse)
        where c.name = {corpus_name}
        WITH n, nt, path, s, d
        OPTIONAL MATCH (n)<-[:annotates]-(subs)
        return n,nt, path, collect(subs) as subs, s, d
        order by size(nodes(path))'''
        results = self.execute_cypher(hierarchy_statement, corpus_name=self.corpus_name)
        sup = None
        data = {}
        subs = {}
        token_properties = {}
        type_properties = {}
        type_subsets = {}
        token_subsets = {}
        speaker_properties = set()
        discourse_properties = set()
        for r in results:
            if not speaker_properties:
                for k, v in r['s'].items():
                    speaker_properties.add((k, type(v)))
            if not discourse_properties:
                for k, v in r['d'].items():
                    discourse_properties.add((k, type(v)))
            at = list(r['n'].labels)[0]
            data[at] = sup
            sup = at
            if r['subs'] is not None:
                subs[at] = set([list(x.labels)[0] for x in r['subs']])
            token_subsets[at] = set()
            type_subsets[at] = set()
            token_properties[at] = set([('id', type(''))])
            type_properties[at] = set()
            for k, v in r['n'].items():
                if k == 'subsets':
                    token_subsets[at].update(v)
                else:
                    token_properties[at].add((k, type(v)))

            for k, v in r['nt'].items():
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
        h.speaker_properties = speaker_properties
        h.discourse_properties = discourse_properties

        h.corpus_name = self.corpus_name
        return h

    def refresh_hierarchy(self):
        """
        Updates the hierarchy

        """
        h = self.generate_hierarchy()
        h.corpus_name = self.corpus_name
        self.hierarchy = h
        self.cache_hierarchy()

    def reset_hierarchy(self):
        """
        Resets the hierarchy
        """
        self.execute_cypher('''MATCH (c:Corpus)<-[:contained_by*]-(n)-[:is_a]->(t),
                                (c)-[:spoken_by]->(s:Speaker),
                                (c)-[:spoken_in]->(d:Discourse)
                                WHERE c.name = {corpus}
                                WITH n, t, c, s, d
                                OPTIONAL MATCH (t)<-[:annotates]-(a)
                                DETACH DELETE a, t, n, s, d''', corpus=self.corpus_name)

    def encode_hierarchy(self):
        """
        encodes hierarchy
        """
        self.reset_hierarchy()
        hierarchy_template = '''({super})<-[:contained_by]-({sub})-[:is_a]->({sub_type})'''
        subannotation_template = '''({super})<-[:annotates]-({sub})'''
        speaker_template = '''(c)-[:spoken_by]->(s:Speaker {%s})'''
        discourse_template = '''(c)-[:spoken_in]->(d:Discourse {%s})'''
        statement = '''MATCH (c:Corpus) WHERE c.name = {{corpus_name}}
        MERGE {merge_statement}'''
        merge_statements = []
        speaker_props = generate_cypher_property_list(self.hierarchy.speaker_properties)
        discourse_props = generate_cypher_property_list(self.hierarchy.discourse_properties)
        merge_statements.append(speaker_template % speaker_props)
        merge_statements.append(discourse_template % discourse_props)
        for at in self.hierarchy.highest_to_lowest:
            sup = self.hierarchy[at]
            if sup is None:
                sup = 'c'
            else:
                sup = '{}'.format(sup)
            try:
                token_props = generate_cypher_property_list(self.hierarchy.token_properties[at])
                if token_props:
                    token_props = ', ' + token_props
            except KeyError:
                token_props = ''
            try:
                type_props = generate_cypher_property_list(self.hierarchy.type_properties[at])
                if type_props:
                    type_props = ', ' + type_props
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
            merge_statements.append(hierarchy_template.format(super=sup, sub=sub,
                                                              sub_type=sub_type))
            for sa in subannotations:
                sa = "{0}:{0} {{label: '', begin:0, end: 0}}".format(sa)
                merge_statements.append(subannotation_template.format(super=at, sub=sa))

        statement = statement.format(merge_statement='\nMERGE '.join(merge_statements))
        self.execute_cypher(statement, corpus_name=self.corpus_name)
        self.cache_hierarchy()

    def encode_position(self, higher_annotation_type, lower_annotation_type, name, subset=None):
        """
        Encodes position of lower type in higher type

        Parameters
        ----------
        higher_annotation_type : str
            what the higher annotation is (utterance, word)
        lower_annotation_type : str
            what the lower annotation is (word, phone, syllable)
        name : str
            the column name
        subset : str
            the annotation subset

        """
        lower = getattr(self, lower_annotation_type)
        if subset is not None:
            lower = lower.filter_by_subset(subset)

        higher = getattr(getattr(lower, higher_annotation_type), lower_annotation_type)
        if subset is not None:
            higher = higher.filter_by_subset(subset)

        q = self.query_graph(lower)

        q.cache(higher.position.column_name(name))
        self.hierarchy.add_token_properties(self, lower_annotation_type, [(name, float)])

    def encode_rate(self, higher_annotation_type, lower_annotation_type, name, subset=None):
        """
        Encodes the rate of the lower type in the higher type

        Parameters
        ----------
        higher_annotation_type : str
            what the higher annotation is (utterance, word)
        lower_annotation_type : str
            what the lower annotation is (word, phone, syllable)
        name : str
            the column name
        subset : str
            the annotation subset
        """
        higher = getattr(self, higher_annotation_type)
        lower = getattr(higher, lower_annotation_type)
        if subset is not None:
            lower = lower.filter_by_subset(subset)
        q = self.query_graph(higher)

        q.cache(lower.rate.column_name(name))

        self.hierarchy.add_token_properties(self, higher_annotation_type, [(name, float)])

    def encode_count(self, higher_annotation_type, lower_annotation_type, name, subset=None):
        """
        Encodes the rate of the lower type in the higher type

        Parameters
        ----------
        higher_annotation_type : str
            what the higher annotation is (utterance, word)
        lower_annotation_type : str
            what the lower annotation is (word, phone, syllable)
        name : str
            the column name
        subset : str
            the annotation subset
        """
        higher = getattr(self, higher_annotation_type)
        lower = getattr(higher, lower_annotation_type)
        if subset is not None:
            lower = lower.filter_by_subset(subset)
        q = self.query_graph(higher)

        q.cache(lower.count.column_name(name))

        self.hierarchy.add_token_properties(self, higher_annotation_type, [(name, float)])

    def reset_property(self, annotation_type, name):
        """
        Removes property from hierarchy

        Parameters
        ----------
        annnotation_type : str
            what is being removed
        name : str
            the column name
        """
        q = self.query_graph(getattr(self, annotation_type))
        q.set_properties(**{name: None})
        self.hierarchy.remove_token_properties(self, annotation_type, [name])
