
from .elements import (ContainsClauseElement,
                    RightAlignedClauseElement, LeftAlignedClauseElement)

from .func import Count

from .cypher import query_to_cypher

from polyglotdb.io.csv import save_results

class GraphQuery(object):
    def __init__(self, graph, to_find, is_timed):
        self.is_timed = is_timed
        self.graph = graph
        self.to_find = to_find
        self._criterion = []
        self._contained_by_annotations = set()
        self._contains_annotations = set()
        self._columns = [self.to_find.id.column_name('id'),
                        self.to_find.label.column_name('label')]
        self._additional_columns = []
        self._order_by = []
        self._group_by = []
        self._aggregate = []

    def filter(self, *args):
        self._criterion.extend(args)
        return self

    def filter_contains(self, *args):
        args = [ContainsClauseElement(x.attribute, x.value) for x in args]
        self._criterion.extend(args)
        annotation_set = set(x.attribute.annotation for x in args)
        self._contains_annotations.update(annotation_set)
        return self

    def filter_contained_by(self, *args):
        self._criterion.extend(args)
        annotation_set = set(x.attribute.annotation for x in args)
        self._contained_by_annotations.update(annotation_set)
        return self

    def columns(self, *args):
        column_set = set(self._additional_columns)
        column_set.update(self._columns)
        args = [x for x in args if x not in column_set]
        self._additional_columns.extend(args)
        return self

    def filter_left_aligned(self, annotation_type):
        self._criterion.append(LeftAlignedClauseElement(self.to_find, annotation_type))
        return self

    def filter_right_aligned(self, annotation_type):
        self._criterion.append(RightAlignedClauseElement(self.to_find, annotation_type))
        return self

    def cypher(self):
        return query_to_cypher(self)

    def group_by(self, field):
        self._group_by.append(field)
        return self

    def order_by(self, field, descending = False):
        self._order_by.append((field, descending))
        return self

    def times(self, begin_name = None, end_name = None):
        if begin_name is not None:
            self._additional_columns.append(self.to_find.begin.column_name('begin'))
        else:
            self._additional_columns.append(self.to_find.begin)
        if end_name is not None:
            self._additional_columns.append(self.to_find.end.column_name('end'))
        else:
            self._additional_columns.append(self.to_find.end)
        return self

    def duration(self):
        self._additional_columns.append(self.to_find.duration.column_name('duration'))
        return self

    def all(self):
        return self.graph.graph.cypher.execute(self.cypher())

    def to_csv(self, path):
        save_results(self.graph.graph.cypher.execute(self.cypher()), path)

    def count(self):
        self._aggregate = [Count()]
        cypher = self.cypher()
        value = self.graph.graph.cypher.execute(cypher)
        return value.one

    def aggregate(self, *args):
        self._aggregate = args
        cypher = self.cypher()
        value = self.graph.graph.cypher.execute(cypher)
        if self._group_by:
            return value
        else:
            return value.one
