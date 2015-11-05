
from collections import defaultdict

from .elements import (ContainsClauseElement,
                    AlignmentClauseElement,
                    RightAlignedClauseElement, LeftAlignedClauseElement,
                    NotRightAlignedClauseElement, NotLeftAlignedClauseElement)

from .func import Count

from .helper import anchor_attributes, type_attributes

from .cypher import query_to_cypher, query_to_params

from polyglotdb.io.csv import save_results


class GraphQuery(object):
    def __init__(self, corpus, to_find, is_timed):
        self.is_timed = is_timed
        self.corpus = corpus
        self.to_find = to_find
        self._criterion = []
        self._columns = [self.to_find.id.column_name('id'),
                        self.to_find.label.column_name('label')]
        self._additional_columns = []
        self._order_by = []
        self._group_by = []
        self._aggregate = []

    def clear_columns(self):
        self._columns = []
        return self

    @property
    def annotation_set(self):
        annotation_set = set()
        for c in self._criterion:
            annotation_set.update(c.annotations)
        return annotation_set

    def filter(self, *args):
        self._criterion.extend([x for x in args if x is not None])
        other_to_finds = [x for x in self.annotation_set if x.type != self.to_find.type]
        for o in other_to_finds:
            if o.pos == 0:
                if o.type in [x.type for x in self._contained_by_annotations]:
                    continue
                if o.type in [x.type for x in self._contains_annotations]:
                    continue
                self._contained_by_annotations.add(o) # FIXME
        return self

    def filter_contains(self, *args):
        self._criterion.extend(args)
        return self

    def filter_contained_by(self, *args):
        self._criterion.extend(args)
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

    def filter_not_left_aligned(self, annotation_type):
        self._criterion.append(NotLeftAlignedClauseElement(self.to_find, annotation_type))
        return self

    def filter_not_right_aligned(self, annotation_type):
        self._criterion.append(NotRightAlignedClauseElement(self.to_find, annotation_type))
        return self

    def cypher(self):
        return query_to_cypher(self)

    def cypher_params(self):
        return query_to_params(self)

    def group_by(self, *args):
        self._group_by.extend(args)
        return self

    def order_by(self, field, descending = False):
        self._order_by.append((field, descending))
        return self

    def discourses(self, output_name = None):
        if output_name is None:
            output_name = 'discourse'
        self = self.columns(self.to_find.discourse.column_name(output_name))
        return self

    def annotation_levels(self):
        annotation_levels = defaultdict(set)
        for c in self._criterion:
            for a in c.attributes:
                t = a.annotation
                annotation_levels[t.type].add(t)
        for a in self._columns + self._group_by + self._additional_columns:
            t = a.annotation
            annotation_levels[t.type].add(t)

        return annotation_levels

    def times(self, begin_name = None, end_name = None):
        if begin_name is None:
            begin_name = 'begin'
        if end_name is None:
            end_name = 'end'
        self = self.columns(self.to_find.begin.column_name(begin_name))
        self = self.columns(self.to_find.end.column_name(end_name))
        return self

    def duration(self):
        self._additional_columns.append(self.to_find.duration.column_name('duration'))
        return self

    def all(self):
        return self.corpus.graph.cypher.execute(self.cypher(), **self.cypher_params())

    def to_csv(self, path):
        save_results(self.corpus.graph.cypher.execute(self.cypher(), **self.cypher_params()), path)

    def count(self):
        self._aggregate = [Count()]
        cypher = self.cypher()
        value = self.corpus.graph.cypher.execute(cypher, **self.cypher_params())
        return value.one

    def aggregate(self, *args):
        self._aggregate = args
        cypher = self.cypher()
        value = self.corpus.graph.cypher.execute(cypher, **self.cypher_params())
        if self._group_by:
            return value
        else:
            return value.one
