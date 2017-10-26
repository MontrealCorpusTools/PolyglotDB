from collections import defaultdict
import copy

from .elements import (ContainsClauseElement,
                       AlignmentClauseElement,
                       RightAlignedClauseElement, LeftAlignedClauseElement,
                       NotRightAlignedClauseElement, NotLeftAlignedClauseElement)

from .attributes import (HierarchicalAnnotation)

from .results import QueryResults
from .profiles.base import Filter, Column

from polyglotdb.exceptions import SubannotationError

from ..base import BaseQuery


def base_stop_check():
    return False


class GraphQuery(BaseQuery):
    """
    Base GraphQuery class.

    Extend this class to implement more advanced query functions.

    Parameters
    ----------
    corpus : :class:`~polyglotdb.corpus.CorpusContext`
        The corpus to query
    to_find : str
        Name of the annotation type to search for
    """
    _parameters = ['_criterion', '_columns', '_order_by', '_aggregate',
                   '_preload', '_set_labels', '_remove_labels',
                   '_set_properties', '_delete', '_limit',
                   '_cache', '_acoustic_columns']

    set_pause_template = '''SET {alias} :pause, {type_alias} :pause_type
    REMOVE {alias}:speech
    WITH {alias}
    OPTIONAL MATCH (prec)-[r1:precedes]->({alias})
        FOREACH (o IN CASE WHEN prec IS NOT NULL THEN [prec] ELSE [] END |
          CREATE (prec)-[:precedes_pause]->({alias})
        )
    DELETE r1
    WITH {alias}, prec
    OPTIONAL MATCH ({alias})-[r2:precedes]->(foll)
        FOREACH (o IN CASE WHEN foll IS NOT NULL THEN [foll] ELSE [] END |
          CREATE ({alias})-[:precedes_pause]->(foll)
        )
    DELETE r2'''

    def __init__(self, corpus, to_find, stop_check=None):
        super(GraphQuery, self).__init__(corpus, to_find)
        if stop_check is None:
            stop_check = base_stop_check
        self.stop_check = stop_check
        self._acoustic_columns = []

        self._add_subannotations = []

    def required_nodes(self):
        from .attributes.hierarchical import HierarchicalAnnotation
        tf_type = type(self.to_find)
        ns = super(GraphQuery, self).required_nodes()
        for c in self._columns + self._aggregate + self._preload + self._cache:
            ns.update(x for x in c.nodes if isinstance(x, HierarchicalAnnotation))
        for c, _ in self._order_by:
            ns.update(x for x in c.nodes if isinstance(x, HierarchicalAnnotation))
        for c in self._acoustic_columns:
            ns.update(x for x in c.nodes if type(x) is not tf_type)
        return ns

    def set_pause(self):
        """ sets pauses in graph"""
        self._set_properties['pause'] = True
        self.corpus.execute_cypher(self.cypher(), **self.cypher_params())
        self._set_properties = {}

    def _generate_set_properties_return(self):
        if 'pause' in self._set_properties:
            kwargs = {'alias': self.to_find.alias,
                      'type_alias': self.to_find.type_alias}

            return_statement = self.set_pause_template.format(**kwargs)
            return return_statement
        return super(GraphQuery, self)._generate_set_properties_return()

    def columns(self, *args):
        """
        Add one or more additional columns to the results.

        Columns should be :class:`~polyglotdb.graph.attributes.Attribute` objects.
        """
        column_set = set(self._columns) & set(self._acoustic_columns) & set(self._hidden_columns)
        for c in args:
            if c in column_set:
                continue
            if c.acoustic:
                self._acoustic_columns.append(c)
            else:
                self._columns.append(c)
                # column_set.add(c) #FIXME failing tests
        return self

    def filter_left_aligned(self, annotation_type):
        """
        Short cut function for aligning the queried annotations with
        another annotation type.

        Same as query.filter(g.word.begin == g.phone.begin).
        """
        if not isinstance(annotation_type, HierarchicalAnnotation):
            annotation_type = getattr(self.to_find, annotation_type.node_type)
        self._criterion.append(LeftAlignedClauseElement(self.to_find, annotation_type))
        return self

    def filter_right_aligned(self, annotation_type):
        """
        Short cut function for aligning the queried annotations with
        another annotation type.

        Same as query.filter(g.word.end == g.phone.end).
        """
        if not isinstance(annotation_type, HierarchicalAnnotation):
            annotation_type = getattr(self.to_find, annotation_type.node_type)
        self._criterion.append(RightAlignedClauseElement(self.to_find, annotation_type))
        return self

    def filter_not_left_aligned(self, annotation_type):
        """
        Short cut function for aligning the queried annotations with
        another annotation type.

        Same as query.filter(g.word.begin != g.phone.begin).
        """
        if not isinstance(annotation_type, HierarchicalAnnotation):
            annotation_type = getattr(self.to_find, annotation_type.node_type)
        self._criterion.append(NotLeftAlignedClauseElement(self.to_find, annotation_type))
        return self

    def filter_not_right_aligned(self, annotation_type):
        """
        Short cut function for aligning the queried annotations with
        another annotation type.

        Same as query.filter(g.word.end != g.phone.end).
        """
        if not isinstance(annotation_type, HierarchicalAnnotation):
            annotation_type = getattr(self.to_find, annotation_type.node_type)
        self._criterion.append(NotRightAlignedClauseElement(self.to_find, annotation_type))
        return self

    def preload(self, *args):
        from .attributes.path import SubPathAnnotation
        from .attributes.subannotation import SubAnnotation
        for a in args:
            if isinstance(a, SubPathAnnotation) and not isinstance(a, SubAnnotation):
                a.with_subannotations = True
            self._preload.append(a)
        return self

    def all(self):
        """
        Returns all results for the query

        Returns
        -------
        res_list : list
            a list of results from the query
        """
        if self._acoustic_columns:
            for a in self._acoustic_columns:
                discourse_found = False
                speaker_found = False
                begin_found = False
                end_found = False
                for c in self._columns + self._hidden_columns:
                    if a.node.discourse == c.node and \
                                    c.label == 'name':
                        a.discourse_alias = c.output_alias
                        discourse_found = True
                    if a.node.speaker == c.node and \
                                    c.label == 'name':
                        a.speaker_alias = c.output_alias
                        speaker_found = True
                    elif a.node == c.node and \
                                    c.label == 'begin':
                        a.begin_alias = c.output_alias
                        begin_found = True
                    elif a.node == c.node and \
                                    c.label == 'end':
                        a.end_alias = c.output_alias
                        end_found = True
                if not discourse_found:
                    self._hidden_columns.append(a.node.discourse.name.column_name(a.discourse_alias))
                if not speaker_found:
                    self._hidden_columns.append(a.node.speaker.name.column_name(a.speaker_alias))
                if not begin_found:
                    self._hidden_columns.append(a.node.begin.column_name(a.begin_alias))
                if not end_found:
                    self._hidden_columns.append(a.node.end.column_name(a.end_alias))
        return QueryResults(self)

    def create_subset(self, label):
        """
        Set properties of the returned tokens.
        """
        labels_to_add = []
        if self.to_find.node_type not in self.corpus.hierarchy.subset_tokens or \
                        label not in self.corpus.hierarchy.subset_tokens[self.to_find.node_type]:
            labels_to_add.append(label)
        super(GraphQuery, self).create_subset(label)
        if labels_to_add:
            self.corpus.hierarchy.add_token_labels(self.corpus, self.to_find.node_type, labels_to_add)

    def set_properties(self, **kwargs):
        """
        Set properties of the returned tokens.
        """
        props_to_remove = []
        props_to_add = []
        for k, v in kwargs.items():
            if v is None:
                props_to_remove.append(k)
            else:
                if not self.corpus.hierarchy.has_token_property(self.to_find.node_type, k):
                    props_to_add.append((k, type(kwargs[k])))
        super(GraphQuery, self).set_properties(**kwargs)
        if props_to_add:
            self.corpus.hierarchy.add_token_properties(self.corpus, self.to_find.node_type, props_to_add)
        if props_to_remove:
            self.corpus.hierarchy.remove_token_properties(self.corpus, self.to_find.node_type, props_to_remove)

    def remove_subset(self, label):
        """ removes all token labels"""

        super(GraphQuery, self).remove_subset(label)
        self.corpus.hierarchy.remove_token_labels(self.corpus, self.to_find.node_type, [label])

    def cache(self, *args):
        """

        """
        self._cache.extend(args)
        self.corpus.execute_cypher(self.cypher(), **self.cypher_params())

        props_to_add = []
        for k in args:
            k = k.output_label
            if not self.corpus.hierarchy.has_token_property(self.to_find.node_type, k):
                props_to_add.append((k, float))

        if props_to_add:
            self.corpus.hierarchy.add_token_properties(self.corpus, self.to_find.node_type, props_to_add)

    def to_json(self):
        data = {'to_find': self.to_find.for_json()[0],
                'corpus_name': self.corpus.corpus_name,
                'filters': [x.for_json() for x in self._criterion],
                'columns': [x.for_json() for x in self._columns]}
        return data

    def from_json(self, corpus, data):
        self.corpus = corpus
        self.to_find = getattr(corpus.hierarchy, data['to_find'])
        for f in data['filters']:
            print(f)
            self._criterion.append(Filter(*f).for_polyglot(corpus))
        for c in data['columns']:
            self._columns.append(Column(*c).for_polyglot(corpus, data['to_find']))


class SplitQuery(GraphQuery):
    splitter = ''

    def base_query(self, filters=None):
        """ sets up base query

        Returns
        -------
        q : :class: `~polyglotdb.graph.GraphQuery`
            the base query
        """
        q = GraphQuery(self.corpus, self.to_find)
        for p in q._parameters:
            if p == '_criterion' and filters is not None:
                setattr(q, p, filters)
            elif isinstance(getattr(self, p), list):
                for x in getattr(self, p):
                    getattr(q, p).append(x)
            else:
                setattr(q, p, copy.deepcopy(getattr(self, p)))
        return q

    def split_queries(self):
        """ splits a query into multiple queries """
        from .elements import BaseNotEqualClauseElement, BaseNotInClauseElement
        attribute_name = self.splitter[:-1]  # remove 's', fixme maybe?
        splitter_annotation = getattr(self.to_find, attribute_name)
        splitter_attribute = getattr(splitter_annotation, 'name')
        splitter_names = sorted(getattr(self.corpus, self.splitter))
        if self.call_back is not None:
            self.call_back(0, len(splitter_names))
        selection = []
        include = True
        reg_filters = []
        for c in self._criterion:
            try:
                if c.attribute.node == splitter_annotation and \
                                c.attribute.label == 'name':
                    if isinstance(c.value, (list, tuple, set)):
                        selection.extend(c.value)
                    else:
                        selection.append(c.value)
                    if isinstance(c, (BaseNotEqualClauseElement, BaseNotInClauseElement)):
                        include = False
                else:
                    reg_filters.append(c)
            except AttributeError:
                reg_filters.append(c)

        for i, x in enumerate(splitter_names):
            if selection:
                if include and x not in selection:
                    continue
                if not include and x in selection:
                    continue
            if self.call_back is not None:
                self.call_back(i)
                self.call_back('Querying {} {} of {} ({})...'.format(attribute_name, i, len(splitter_names), x))

            base = self.base_query(reg_filters)
            al = base.required_nodes()
            al.update(base.optional_nodes())
            base = base.filter(splitter_attribute == x)
            yield base

    def set_pause(self):
        """ sets a pause in queries """
        for q in self.split_queries():
            if self.stop_check():
                return
            q.set_pause()

    def all(self):
        """ returns all results from a query """
        results = None
        for q in self.split_queries():
            if self.stop_check():
                return
            if results is None:
                r = q.all()
                results = r
            else:
                results.add_results(q)
        return results

    def to_csv(self, path):
        for i, q in enumerate(self.split_queries()):
            if i == 0:
                mode = 'w'
            else:
                mode = 'a'
            r = q.all()

            r.to_csv(path, mode=mode)

    def delete(self):
        """ deletes the query """
        for q in self.split_queries():
            if self.stop_check():
                return
            q.delete()

    def cache(self, *args):
        for q in self.split_queries():
            if self.stop_check():
                return
            q.cache(*args)

    def set_label(self, *args):
        """ sets the query type"""
        for q in self.split_queries():
            if self.stop_check():
                return
            q.set_label(*args)

    def set_properties(self, **kwargs):
        """ sets the query token """
        for q in self.split_queries():
            if self.stop_check():
                return
            q.set_properties(**kwargs)


class SpeakerGraphQuery(SplitQuery):
    splitter = 'speakers'


class DiscourseGraphQuery(SplitQuery):
    splitter = 'discourses'
