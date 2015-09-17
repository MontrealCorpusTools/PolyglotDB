
from .elements import ContainsClauseElement

from .func import Count

class GraphQuery(object):
    def __init__(self, graph, to_find):
        self.graph = graph
        self.to_find = to_find
        self._criterion = []
        self._prec_criterion = []
        self._foll_criterion = []
        self._contained_by_criterion = []
        self._contains_criterion = []
        self._left_aligned_criterion = []
        self._right_aligned_criterion = []
        self._additional_columns = []
        self._order_by = []
        self._group_by = []
        self._aggregate = []

    def filter(self, *args):
        self._criterion.extend(args)
        return self

    def filter_contains(self, annotation_type, *args):
        args = [ContainsClauseElement(x.key, x.value, x.pos) for x in args]
        self._contains_criterion.append((annotation_type, args))
        return self

    def filter_contained_by(self, annotation_type, *args):
        self._contained_by_criterion.append((annotation_type, args))
        return self

    def filter_left_aligned(self, annotation_type):
        self._left_aligned_criterion.append(annotation_type)
        return self

    def filter_right_aligned(self, annotation_type):
        self._right_aligned_criterion.append(annotation_type)
        return self

    def cypher(self):
        kwargs = {'corpus_name': self.graph.corpus_name,
                    'annotation_type': self.to_find,
                    'preceding_condition': '',
                    'following_condition': '',
                    'additional_match': '',
                    'additional_where': '',
                    'additional_columns': '',
                    'order_by': ''}
        if self._aggregate:
            template = '''MATCH {preceding_condition}(b)-[r]->(e){following_condition}{additional_match}
                    WHERE b.corpus = '{corpus_name}'
                    AND type(r) = '{annotation_type}'{additional_where}
                    RETURN {aggregates}{additional_columns}{order_by}'''
            properties = []
            for g in self._group_by:
                properties.append(g.aliased_for_cypher())
            for a in self._aggregate:
                properties.append(a.for_cypher())
            kwargs['aggregates'] = ', '.join(properties)

        else:
            template = '''MATCH {preceding_condition}(b)-[r]->(e){following_condition}{additional_match}
                    WHERE b.corpus = '{corpus_name}'
                    AND type(r) = '{annotation_type}'{additional_where}
                    RETURN DISTINCT r{additional_columns}{order_by}'''
        left_align_template = '''()<-[:{align_type}]-(b)'''
        right_align_template = '''()-[:{align_type}]->(e)'''
        for la in self._left_aligned_criterion:
            match_string = left_align_template.format(align_type = la)
            kwargs['additional_match'] += ',\n' + match_string
        for ra in self._right_aligned_criterion:
            match_string = right_align_template.format(align_type = ra)
            kwargs['additional_match'] += ',\n' + match_string

        properties = []
        r_count = 0
        prev_r = 0
        foll_r = 0
        for c in self._criterion:
            if c.pos == 0:
                properties.append(c.for_cypher('r'))
            elif c.pos < 0:
                if prev_r > c.pos:
                    prev_r = c.pos
                properties.append(c.for_cypher('prevr{}'.format(abs(c.pos))))
            elif c.pos > 0:
                if foll_r < c.pos:
                    foll_r = c.pos
                properties.append(c.for_cypher('follr{}'.format(c.pos)))
        prec_template = '''()-[{name}]->'''
        foll_template = '''-[{name}]->()'''
        for i in range(prev_r, 0):
            kwargs['preceding_condition'] += prec_template.format(name = 'prevr{}'.format(abs(i)))
        for i in range(1,foll_r+1):
            kwargs['following_condition'] += foll_template.format(name = 'follr{}'.format(i))
        if properties:
            kwargs['additional_where'] += '\nAND ' + '\nAND '.join(properties)

        contained_by_template = '''(b)<-[:{annotation_type}*0..]-(wb)-[{rel_name}:{containing_annotation_type}]->(we)<-[:{annotation_type}*0..]-(e)'''
        for c in self._contained_by_criterion:
            r_count += 1
            name = 'r{}'.format(r_count)
            match_string = contained_by_template.format(annotation_type = self.to_find,
                                                rel_name = name,
                                                containing_annotation_type = c[0])
            kwargs['additional_match'] += ',\n' + match_string
            properties = []
            for cc in c[1]:
                properties.append(cc.for_cypher(name))
            kwargs['additional_where'] += '\nAND ' + '\nAND '.join(properties)

        contains_template = '''(b)-[{rel_name}:{contains_annotation_type}*0..]->(e)'''
        for c in self._contains_criterion:
            r_count += 1
            name = 'r{}'.format(r_count)
            match_string = contains_template.format(contains_annotation_type = c[0],
                                                rel_name = name)
            kwargs['additional_match'] += ',\n' + match_string
            properties = []
            for cc in c[1]:
                properties.append(cc.for_cypher(name))
            kwargs['additional_where'] += '\nAND ' + '\nAND '.join(properties)

        properties = []
        for c in self._order_by:
            element = c[0].name
            if element not in self._additional_columns:
                self._additional_columns.append(element)
            if c[1]:
                element += ' DESC'
            properties.append(element)

        if properties:
            kwargs['order_by'] += '\nORDER BY ' + ', '.join(properties)

        properties = []
        for c in self._additional_columns:
            if c == 'duration':
                properties.append('e.time - b.time AS duration')
            elif c == 'begin':
                properties.append('b.time AS begin')
            elif c == 'end':
                properties.append('e.time AS end')
            #elif c == 'count':
            #   properties.append('r, count(label)
        if properties:
            kwargs['additional_columns'] += ', ' + ', '.join(properties)
        query = template.format(**kwargs)

        return query

    def group_by(self, field):
        self._group_by.append(field)
        return self

    def order_by(self, field, descending = False):
        self._order_by.append((field, descending))
        return self

    def times(self):
        self._additional_columns.append('begin')
        self._additional_columns.append('end')
        return self

    def duration(self):
        self._additional_columns.append('duration')
        return self

    def all(self):
        return self.graph.graph.cypher.execute(self.cypher())

    def count(self):
        self._aggregate = [Count('*')]
        cypher = self.cypher()
        value = self.graph.graph.cypher.execute(cypher)
        return value.one

    def aggregate(self, *args):
        self._aggregate = args
        cypher = self.cypher()
        value = self.graph.graph.cypher.execute(cypher)
        return value
