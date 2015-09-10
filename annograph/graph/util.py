
from py2neo import Graph
from annograph.graph.models import Anchor, Annotation, ContainsClauseElement, InClauseElement

from annograph.helper import align_phones


class Query(object):
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
        template = '''MATCH {preceding_condition}(b)-[r]->(e){following_condition}{additional_match}
                WHERE b.corpus = '{corpus_name}'
                AND type(r) = '{annotation_type}'{additional_where}
                RETURN DISTINCT r'''
        kwargs = {'corpus_name': self.graph.corpus_name,
                    'annotation_type': self.to_find,
                    'preceding_condition': '',
                    'following_condition': '',
                    'additional_match': '',
                    'additional_where': ''}
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

        contained_by_template = '''(b)<-[:{annotation_type}*..]-(wb)-[{rel_name}:{containing_annotation_type}]->(we)<-[:{annotation_type}*..]-(e)'''
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

        contains_template = '''(b)-[{rel_name}:{contains_annotation_type}*..]->(e)'''
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


        query = template.format(**kwargs)

        return query

    def all(self):
        for x in self.graph.graph.cypher.execute(self.cypher()):
            yield x.r


class GraphContext(object):
    def __init__(self, user, password, corpus_name, host = 'localhost', port = 7474):
        self.graph = Graph("http://{}:{}@{}:{}/db/data/".format(user, password, host, port))
        self.corpus_name = corpus_name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        if exc_type is None:
            return True

    def reset_graph(self):
        self.graph.delete_all()

    def remove_discourse(self, name):
        pass

    def query(self, annotation_type):
        return Query(self, annotation_type)

    def find(self, word = None):

        query = '''MATCH (n{corpus:'%s'})-[r:%s{label:'%s'}]->()
                RETURN r''' % (self.corpus_name, 'word', word)
        t = self.graph.cypher.execute(query)
        for r in t:
            print(dir(r.r))
            print(r.r)

    def add_discourse(self, data):
        nodes = []
        begin_node = Anchor(time = 0, corpus = self.corpus_name, discourse = data.name)
        base_ind_to_node = {}
        base_levels = data.base_levels
        nodes.append(begin_node)
        for b in base_levels:
            base_ind_to_node[b] = {0: begin_node}
        for i, level in enumerate(data.process_order):
            for d in data[level]:

                if i == 0: #Anchor level, should have all base levels in it
                    begin_node = nodes[-1]

                    to_align = []
                    endpoints = []
                    for b in base_levels:
                        begin, end = d[b]
                        endpoints.append(end)
                        base = data[b][begin:end]
                        to_align.append(base)

                    if len(to_align) > 1:
                        aligned = list(align_phones(*to_align))
                    else:
                        aligned = to_align
                    first_aligned = aligned.pop(0)
                    for j, first in enumerate(first_aligned):
                        time = None
                        if first != '-':
                            time = first.end
                        else:
                            for second in aligned:
                                s = second[j]
                                if s != '-':
                                    time = s.end
                        node = Anchor(time = time, corpus = self.corpus_name, discourse = data.name)
                        nodes.append(node)
                        first_begin_node = -2
                        second_begin_nodes = [-2 for k in aligned]
                        if first != '-':
                            for k in range(j-1, -1, -1):
                                if first_aligned[k] != '-':
                                    break
                                first_begin_node -= 1
                            annotation = Annotation(nodes[first_begin_node],
                                                node, base_levels[0], first.label)
                            self.graph.create(annotation)
                        for k, second in enumerate(aligned):
                            s = second[j]
                            if s != '-':
                                for m in range(j-1, -1, -1):
                                    if second[m] != '-':
                                        break
                                    second_begin_nodes[k] -= 1
                                annotation = Annotation(nodes[second_begin_nodes[k]],
                                                    node, base_levels[k+1], s.label)
                                self.graph.create(annotation)
                    for ind, b in enumerate(base_levels):
                        base_ind_to_node[b][endpoints[ind]] = nodes[-1]
                    end_node = nodes[-1]
                else:
                    for b in base_levels:
                        if b in d.references:

                            begin, end = d[b]
                            if begin not in base_ind_to_node[b]:
                                n = nodes[0]
                                for ind in range(begin+1):
                                    for e in n.match_outgoing(b):
                                        n = e.end_node
                                base_ind_to_node[b][begin] = n
                            begin_node = base_ind_to_node[b][begin]
                            if end not in base_ind_to_node[b]:
                                n = nodes[0]
                                for ind in range(end):
                                    for e in n.match_outgoing(b):
                                        n = e.end_node
                                base_ind_to_node[b][end] = n
                            end_node = base_ind_to_node[b][end]
                annotation = Annotation(begin_node, end_node, level, d.label)
                self.graph.create(annotation)
