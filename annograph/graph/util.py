import os
import shutil
import csv
from uuid import uuid1
from py2neo import Graph
from annograph.graph.models import Anchor, Annotation, ContainsClauseElement, InClauseElement

from annograph.helper import align_phones

def duration_cypher():
    return 'e.time - b.time AS duration'

class AggregateFunction(object):
    function = ''
    def __init__(self, key):
        self.key = key

    def for_cypher(self):
        if self.key == 'duration':
            element = 'e.time - b.time'
        elif self.key == 'begin':
            element = 'b.time'
        elif self.key == 'end':
            element = 'e.time'
        else:
            element = self.key
        if self.key != '*':
            template = '{function}({property}) AS {readable_function}_{name}'
        else:
            template = '{function}({property}) AS {readable_function}_all'
        return template.format(function = self.function,
                                readable_function = self.__class__.__name__.lower(),
                                property = element,
                                name = self.key)

class Average(AggregateFunction):
    function = 'avg'

class Count(AggregateFunction):
    function = 'count'

class Sum(AggregateFunction):
    function = 'sum'

class Stdev(AggregateFunction):
    function = 'stdev'

class Max(AggregateFunction):
    function = 'max'

class Min(AggregateFunction):
    function = 'min'

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

def data_to_graph_csvs(data, directory):
    node_path = os.path.join(directory,'{}_nodes.csv'.format(data.name))
    rel_paths = {x:os.path.join(directory,'{}_{}.csv'.format(data.name,x)) for x in data.types}
    rfs = {k: open(v, 'w') for k,v in rel_paths.items()}
    rel_writers = {k:csv.DictWriter(v, ['from_id', 'to_id','label', 'id'], delimiter = ',')
                        for k,v in rfs.items()}
    for x in rel_writers.values():
        x.writeheader()
    with open(node_path,'w') as nf:
        node_writer = csv.DictWriter(nf, ['id','label','time','corpus','discourse'], delimiter = ',')

        node_writer.writeheader()
        nodes = []
        node_ind = 0
        begin_node = dict(id = node_ind, label = uuid1(), time = 0, corpus = data.corpus_name, discourse = data.name)
        node_writer.writerow(begin_node)
        base_ind_to_node = {}
        base_levels = data.base_levels
        nodes.append(begin_node)
        for b in base_levels:
            base_ind_to_node[b] = {0: begin_node}
        for i, level in enumerate(data.process_order):
            annotations = []
            for d in data[level]:

                if i == 0: #Anchor level, should have all base levels in it
                    begin_node = nodes[-1]

                    to_align = []
                    endpoints = []
                    if len(base_levels) != 1:
                        print(data.name)
                        print(base_levels)
                        raise(ValueError)
                    b = base_levels[0]
                    begin, end = d[b]
                    base_sequence = data[b][begin:end]

                    if len(base_sequence) == 0:
                        print(d)
                        print(to_align)
                        print(begin_node)
                        raise(ValueError)
                    for j, first in enumerate(base_sequence):
                        time = None
                        time = first.end
                        node_ind += 1
                        node = dict(id = node_ind, label = uuid1(),
                                        time = time, corpus = data.corpus_name,
                                        discourse = data.name)
                        node_writer.writerow(node)
                        nodes.append(node)
                        first_begin_node = -2
                        rel_writers[base_levels[0]].writerow(dict(from_id=nodes[first_begin_node]['id'],
                                            to_id=node['id'], label=first.label, id = uuid1()))
                    end_node = nodes[-1]
                else:
                    for b in base_levels:
                        if b in d.references:

                            begin, end = d[b]
                            begin_node = nodes[begin]
                            end_node = nodes[end]
                rel_writers[level].writerow(dict(from_id=begin_node['id'],
                                to_id=end_node['id'], label=d.label, id = uuid1()))
    for x in rfs.values():
        x.close()



class CorpusContext(object):
    def __init__(self, user, password, corpus_name, host = 'localhost', port = 7474):
        self.graph = Graph("http://{}:{}@{}:{}/db/data/".format(user, password, host, port))
        self.corpus_name = corpus_name
        self.base_dir = os.path.join(os.path.expanduser('~/Documents/SCT'), self.corpus_name)

        self.log_dir = os.path.join(self.base_dir, 'logs')
        os.makedirs(self.log_dir, exist_ok = True)

        self.temp_dir = os.path.join(self.base_dir, 'temp')
        os.makedirs(self.temp_dir, exist_ok = True)

        self.data_dir = os.path.join(self.base_dir, 'data')
        os.makedirs(self.data_dir, exist_ok = True)


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        if exc_type is None:
            shutil.rmtree(self.temp_dir)
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

    def import_csvs(self, name, annotation_types):
        node_path = 'file:{}'.format(os.path.join(self.temp_dir, '{}_nodes.csv'.format(name)).replace('\\','/'))

        node_import_statement = '''LOAD CSV WITH HEADERS FROM "%s" AS csvLine
CREATE (n:Anchor { id: toInt(csvLine.id),
time: toFloat(csvLine.time), label: csvLine.label, corpus: csvLine.corpus,
discourse: csvLine.discourse })'''
        self.graph.cypher.execute(node_import_statement % node_path)
        self.graph.cypher.execute('CREATE INDEX ON :Anchor(corpus)')
        self.graph.cypher.execute('CREATE INDEX ON :Anchor(discourse)')
        self.graph.cypher.execute('CREATE CONSTRAINT ON (node:Anchor) ASSERT node.id IS UNIQUE')
        self.graph.cypher.execute('CREATE CONSTRAINT ON (node:Anchor) ASSERT node.label IS UNIQUE')

        for at in annotation_types:
            rel_path = 'file:{}'.format(os.path.join(self.temp_dir, '{}_{}.csv'.format(name, at)).replace('\\','/'))
            rel_import_statement = '''USING PERIODIC COMMIT 1000
    LOAD CSV WITH HEADERS FROM "%s" AS csvLine
    MATCH (begin_node:Anchor { id: toInt(csvLine.from_id)}),(end_node:Anchor { id: toInt(csvLine.to_id)})
    CREATE (begin_node)-[:%s { label: csvLine.label, id: csvLine.id }]->(end_node)'''
            self.graph.cypher.execute(rel_import_statement % (rel_path,at))
            self.graph.cypher.execute('CREATE INDEX ON :%s(label)' % at)
        self.graph.cypher.execute('DROP CONSTRAINT ON (node:Anchor) ASSERT node.id IS UNIQUE')
        self.graph.cypher.execute('''MATCH (n)
                                    WHERE n:Anchor
                                    REMOVE n.id''')

    def add_discourse(self, data):
        data.corpus_name = self.corpus_name
        data_to_graph_csvs(data, self.temp_dir)
        self.import_csvs(data.name, data.types)
        #nodes = []
        #begin_node = Anchor(time = 0, corpus = self.corpus_name, discourse = data.name)
        #base_ind_to_node = {}
        #base_levels = data.base_levels
        #nodes.append(begin_node)
        #for b in base_levels:
            #base_ind_to_node[b] = {0: begin_node}
        #for i, level in enumerate(data.process_order):
            #annotations = []
            #for d in data[level]:

                #if i == 0: #Anchor level, should have all base levels in it
                    #begin_node = nodes[-1]

                    #to_align = []
                    #endpoints = []
                    #for b in base_levels:
                        #begin, end = d[b]
                        #endpoints.append(end)
                        #base = data[b][begin:end]
                        #to_align.append(base)

                    #if len(to_align) > 1:
                        #if any(len(x) == 0 for x in to_align):
                            #print(d)
                            #print(to_align)
                            #print(begin_node)
                            #raise(ValueError)
                        #aligned = list(align_phones(*to_align))
                    #else:
                        #aligned = to_align
                    #first_aligned = aligned.pop(0)
                    ##base_annotations = []
                    #for j, first in enumerate(first_aligned):
                        #time = None
                        #if first != '-':
                            #time = first.end
                        #else:
                            #for second in aligned:
                                #s = second[j]
                                #if s != '-':
                                    #time = s.end
                        #node = Anchor(time = time, corpus = self.corpus_name, discourse = data.name)
                        #nodes.append(node)
                        #first_begin_node = -2
                        #second_begin_nodes = [-2 for k in aligned]
                        #if first != '-':
                            #for k in range(j-1, -1, -1):
                                #if first_aligned[k] != '-':
                                    #break
                                #first_begin_node -= 1
                            #annotations.append(Annotation(nodes[first_begin_node],
                                                #node, base_levels[0], first.label))
                        #for k, second in enumerate(aligned):
                            #s = second[j]
                            #if s != '-':
                                #for m in range(j-1, -1, -1):
                                    #if second[m] != '-':
                                        #break
                                    #second_begin_nodes[k] -= 1
                                #annotations.append(Annotation(nodes[second_begin_nodes[k]],
                                                    #node, base_levels[k+1], s.label))
                    ##self.graph.create(*base_annotations)
                    #for ind, b in enumerate(base_levels):
                        #base_ind_to_node[b][endpoints[ind]] = nodes[-1]
                    #end_node = nodes[-1]
                #else:
                    #for b in base_levels:
                        #if b in d.references:

                            #begin, end = d[b]
                            #if begin not in base_ind_to_node[b]:
                                #n = nodes[0]
                                #for ind in range(begin+1):
                                    #for e in n.match_outgoing(b):
                                        #n = e.end_node
                                #base_ind_to_node[b][begin] = n
                            #begin_node = base_ind_to_node[b][begin]
                            #if end not in base_ind_to_node[b]:
                                #n = nodes[0]
                                #for ind in range(end):
                                    #for e in n.match_outgoing(b):
                                        #n = e.end_node
                                #base_ind_to_node[b][end] = n
                            #end_node = base_ind_to_node[b][end]
                #annotations.append(Annotation(begin_node, end_node, level, d.label))
                #if len(annotations) > 1000:
                    #self.graph.create(*annotations)
                    #annotations = []
            #print(len(annotations))
            #if len(annotations) > 0:
                #self.graph.create(*annotations)


