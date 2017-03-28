from collections import defaultdict
import copy

from .elements import (ContainsClauseElement,
                       AlignmentClauseElement,
                       RightAlignedClauseElement, LeftAlignedClauseElement,
                       NotRightAlignedClauseElement, NotLeftAlignedClauseElement)

from .attributes import (HierarchicalAnnotation, SubPathAnnotation,
                         SubAnnotation as QuerySubAnnotation,
                         SpeakerAnnotation, DiscourseAnnotation)

from .results import QueryResults

from .func import Count

from .cypher import query_to_cypher, query_to_params

from polyglotdb.io import save_results

from polyglotdb.exceptions import SubannotationError


class GraphQuery(object):
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
                   '_preload', '_set_type_labels', '_set_token_labels',
                   '_remove_type_labels', '_remove_token_labels',
                   '_set_type', '_set_token', '_delete', '_limit',
                   '_cache', '_acoustic_columns']

    def __init__(self, corpus, to_find):
        self.corpus = corpus
        self.to_find = to_find
        self._criterion = []
        self._columns = []
        self._hidden_columns = []
        self._acoustic_columns = []
        self._order_by = []
        self._group_by = []
        self._aggregate = []
        self._preload = []

        self._set_type_labels = []
        self._set_token_labels = []
        self._remove_type_labels = []
        self._remove_token_labels = []

        self._set_type = {}
        self._set_token = {}
        self._delete = False

        self._limit = None

        self._add_subannotations = []
        self._cache = []
        self.call_back = None
        self.stop_check = None

    def set_pause(self):
        """ sets pauses in graph"""
        self._set_token['pause'] = True
        self.corpus.execute_cypher(self.cypher(), **self.cypher_params())
        self._set_token = {}

    def clear_columns(self):
        """
        Remove any columns specified.  The default columns for any query
        are the id of the token and the label of the type.
        """
        self._columns = []
        return self

    @property
    def annotation_set(self):
        """ Returns annotation set """
        annotation_set = set()
        for c in self._criterion:
            annotation_set.update(c.annotations)
        return annotation_set

    def filter(self, *args):
        """
        Apply one or more filters to a query.
        """
        self._criterion.extend(args)
        return self

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
            annotation_type = getattr(self.to_find, annotation_type.type)
        self._criterion.append(LeftAlignedClauseElement(self.to_find, annotation_type))
        return self

    def filter_right_aligned(self, annotation_type):
        """
        Short cut function for aligning the queried annotations with
        another annotation type.

        Same as query.filter(g.word.end == g.phone.end).
        """
        if not isinstance(annotation_type, HierarchicalAnnotation):
            annotation_type = getattr(self.to_find, annotation_type.type)
        self._criterion.append(RightAlignedClauseElement(self.to_find, annotation_type))
        return self

    def filter_not_left_aligned(self, annotation_type):
        """
        Short cut function for aligning the queried annotations with
        another annotation type.

        Same as query.filter(g.word.begin != g.phone.begin).
        """
        if not isinstance(annotation_type, HierarchicalAnnotation):
            annotation_type = getattr(self.to_find, annotation_type.type)
        self._criterion.append(NotLeftAlignedClauseElement(self.to_find, annotation_type))
        return self

    def filter_not_right_aligned(self, annotation_type):
        """
        Short cut function for aligning the queried annotations with
        another annotation type.

        Same as query.filter(g.word.end != g.phone.end).
        """
        if not isinstance(annotation_type, HierarchicalAnnotation):
            annotation_type = getattr(self.to_find, annotation_type.type)
        self._criterion.append(NotRightAlignedClauseElement(self.to_find, annotation_type))
        return self

    def cypher(self):
        """
        Generates a Cypher statement based on the query.
        """
        return query_to_cypher(self)

    def cypher_params(self):
        """
        Generates Cypher statement parameters based on the query.
        """
        return query_to_params(self)

    def group_by(self, *args):
        """
        Specify one or more fields for how aggregates should be grouped.
        """
        self._group_by.extend(args)
        return self

    def order_by(self, field, descending=False):
        """
        Specify how the results of the query should be ordered.

        Parameters
        ----------
        field : Attribute
            Determines what the ordering should be based on
        descending : bool, defaults to False
            Whether the order should be descending
        """
        self._order_by.append((field, descending))
        return self

    def discourses(self, output_name=None):
        """
        Add a column to the output for the name of the discourse that
        the annotations are in.

        Parameters
        ----------
        output_name : str, optional
            Name of the output column, defaults to "discourse"
        """
        if output_name is None:
            output_name = 'discourse'
        self = self.columns(self.to_find.discourse.name.column_name(output_name))
        return self

    def filter_contains(self, *args):
        """
        Deprecated, use ``filter`` instead.
        """
        return self.filter(*args)

    def filter_contained_by(self, *args):
        """
        Deprecated, use ``filter`` instead.
        """
        return self.filter(*args)

    def annotation_levels(self):
        """
        Returns a dictionary with annotation types as keys and positional
        annotation types as values.

        Used for constructing Cypher statements.
        """
        annotation_levels = defaultdict(set)
        annotation_levels[self.to_find].add(self.to_find)

        # Fix up bug for paths containing multiple routes (i.e. phone.utterance and phone.word)
        hierarchical_depths = set()
        annotations = [a for c in self._criterion for a in c.annotations]
        annotations += [a.base_annotation for a in self._columns]
        annotations += [a.base_annotation for a in self._hidden_columns]
        annotations += [a.base_annotation for a in self._cache]
        annotations += [a.base_annotation for a in self._group_by]
        annotations += [a[0].base_annotation for a in self._order_by]
        annotations += [a for a in self._preload]

        for a in annotations:
            if isinstance(a, (SpeakerAnnotation, DiscourseAnnotation)):
                continue
            if not isinstance(a, HierarchicalAnnotation):
                continue
            hierarchical_depths.add(a.depth)
        # Fix up hierarchical annotations
        if any(x > 1 for x in hierarchical_depths):
            def create_new_hierarchical(base):
                cur = base.hierarchy[self.to_find.type]
                a = getattr(self.to_find, cur)
                while a.type != base.type:
                    cur = base.hierarchy[cur]
                    if cur is None:
                        break
                    a = getattr(a, cur)
                a.pos = base.pos
                return a

            for c in self._criterion:
                try:
                    k = c.attribute.base_annotation
                    if isinstance(k, HierarchicalAnnotation) and \
                            not isinstance(k, (SpeakerAnnotation, DiscourseAnnotation)):
                        c.attribute.base_annotation = create_new_hierarchical(k)
                    try:
                        k = c.value.base_annotation
                        if isinstance(k, HierarchicalAnnotation) and \
                                not isinstance(k, (SpeakerAnnotation, DiscourseAnnotation)):
                            c.attribute.base_annotation = create_new_hierarchical(k)
                    except AttributeError:
                        pass
                except AttributeError:
                    k = c.first
                    if isinstance(k, HierarchicalAnnotation) and \
                            not isinstance(k, (SpeakerAnnotation, DiscourseAnnotation)):
                        c.first = create_new_hierarchical(k)
                    k = c.second
                    if isinstance(k, HierarchicalAnnotation) and \
                            not isinstance(k, (SpeakerAnnotation, DiscourseAnnotation)):
                        c.second = create_new_hierarchical(k)

            for a in self._columns + self._hidden_columns + self._cache + self._group_by:
                k = a.base_annotation
                if isinstance(k, HierarchicalAnnotation) and \
                        not isinstance(k, (SpeakerAnnotation, DiscourseAnnotation)):
                    a.base_annotation = create_new_hierarchical(k)

            for i, k in enumerate(self._preload):
                if isinstance(k, HierarchicalAnnotation) and \
                        not isinstance(k, (SpeakerAnnotation, DiscourseAnnotation)):
                    self._preload[i] = create_new_hierarchical(k)

            for i, a in enumerate(self._order_by):
                k = a[0].base_annotation
                if isinstance(k, HierarchicalAnnotation) and \
                        not isinstance(k, (SpeakerAnnotation, DiscourseAnnotation)):
                    self._order_by[i] = (getattr(create_new_hierarchical(k), a[0].label), a[1])

        for c in self._criterion:
            for a in c.annotations:
                if isinstance(a, DiscourseAnnotation):
                    key = getattr(self.to_find, 'discourse')
                    annotation_levels[key].add(a)
                elif isinstance(a, SpeakerAnnotation):
                    key = getattr(self.to_find, 'speaker')
                    annotation_levels[key].add(a)
                elif isinstance(a, HierarchicalAnnotation):
                    key = getattr(a.contained_annotation, a.type)
                    annotation_levels[key].add(a)
                    contained = key.contained_annotation
                    while True:
                        if not isinstance(contained, HierarchicalAnnotation):
                            break
                        if contained not in annotation_levels:
                            annotation_levels[contained] = set()
                        contained = contained.contained_annotation
                else:
                    key = getattr(self.corpus, a.type)
                    key = key.subset_type(*a.subset_type_labels)
                    key = key.subset_token(*a.subset_token_labels)
                    annotation_levels[key].add(a)
        if self._columns:
            for a in self._columns + self._hidden_columns:
                t = a.base_annotation
                if isinstance(t, DiscourseAnnotation):
                    key = getattr(self.to_find, 'discourse')
                    annotation_levels[key].add(t)
                elif isinstance(t, SpeakerAnnotation):
                    key = getattr(self.to_find, 'speaker')
                    annotation_levels[key].add(t)
                elif isinstance(t, HierarchicalAnnotation):
                    key = getattr(t.contained_annotation, t.type)
                    annotation_levels[key].add(t)
                    hierarchical_depths.add(t.depth)
                    contained = key.contained_annotation
                    while True:
                        if not isinstance(contained, HierarchicalAnnotation):
                            break
                        if contained not in annotation_levels:
                            annotation_levels[contained] = set()
                        contained = contained.contained_annotation
                else:
                    key = getattr(self.corpus, t.type)
                    key = key.subset_type(*t.subset_type_labels)
                    key = key.subset_token(*t.subset_token_labels)
                    annotation_levels[key].add(t)
        elif self._cache:
            for a in self._cache:
                t = a.base_annotation
                if isinstance(t, DiscourseAnnotation):
                    key = getattr(self.to_find, 'discourse')
                    annotation_levels[key].add(t)
                elif isinstance(t, SpeakerAnnotation):
                    key = getattr(self.to_find, 'speaker')
                    annotation_levels[key].add(t)
                elif isinstance(t, HierarchicalAnnotation):
                    key = getattr(t.contained_annotation, t.type)
                    annotation_levels[key].add(t)
                    contained = key.contained_annotation
                    while True:
                        if not isinstance(contained, HierarchicalAnnotation):
                            break
                        if contained not in annotation_levels:
                            annotation_levels[contained] = set()
                        contained = contained.contained_annotation
                else:
                    key = getattr(self.corpus, t.type)
                    key = key.subset_type(*t.subset_type_labels)
                    key = key.subset_token(*t.subset_token_labels)
                    annotation_levels[key].add(t)
        elif self._aggregate:
            for a in self._group_by:
                t = a.base_annotation
                if isinstance(t, DiscourseAnnotation):
                    key = getattr(self.to_find, 'discourse')
                    annotation_levels[key].add(t)
                elif isinstance(t, SpeakerAnnotation):
                    key = getattr(self.to_find, 'speaker')
                    annotation_levels[key].add(t)
                elif isinstance(t, HierarchicalAnnotation):
                    key = getattr(t.contained_annotation, t.type)
                    annotation_levels[key].add(t)
                    contained = key.contained_annotation
                    while True:
                        if not isinstance(contained, HierarchicalAnnotation):
                            break
                        if contained not in annotation_levels:
                            annotation_levels[contained] = set()
                        contained = contained.contained_annotation
                else:
                    key = getattr(self.corpus, t.type)
                    key = key.subset_type(*t.subset_type_labels)
                    key = key.subset_token(*t.subset_token_labels)
                    annotation_levels[key].add(t)
        else:
            for a in self._preload:
                if isinstance(a, DiscourseAnnotation):
                    key = getattr(self.to_find, 'discourse')
                    annotation_levels[key].add(a)
                elif isinstance(a, SpeakerAnnotation):
                    key = getattr(self.to_find, 'speaker')
                    annotation_levels[key].add(a)
                elif isinstance(a, HierarchicalAnnotation):
                    key = getattr(a.contained_annotation, a.type)
                    annotation_levels[key].add(a)
                    contained = key.contained_annotation
                    while True:
                        if not isinstance(contained, HierarchicalAnnotation):
                            break
                        if contained not in annotation_levels:
                            annotation_levels[contained] = set()
                        contained = contained.contained_annotation
                elif isinstance(a, QuerySubAnnotation):
                    a = a.annotation
                    if isinstance(a, SubPathAnnotation):
                        continue
                    key = getattr(self.corpus, a.type)
                    annotation_levels[key].add(a)

                elif isinstance(a, SubPathAnnotation):
                    a = a.annotation
                    key = getattr(self.corpus, a.type)
                    key = key.subset_type(*a.subset_type_labels)
                    key = key.subset_token(*a.subset_token_labels)
                    annotation_levels[key].add(a)
                else:
                    key = getattr(self.corpus, a.type)
                    key = key.subset_type(*a.subset_type_labels)
                    key = key.subset_token(*a.subset_token_labels)
                    annotation_levels[key].add(a)
        return annotation_levels

    def times(self, begin_name=None, end_name=None):
        """
        Add columns for the beginnings and ends of the searched for annotations to
        the output.

        Parameters
        ----------
        begin_name : str, optional
            Specify the name of the column for beginnings, defaults to
            "begin"
        end_name : str, optional
            Specify the name of the column for ends, defaults to
            "end"
        """
        if begin_name is None:
            begin_name = 'begin'
        if end_name is None:
            end_name = 'end'
        self = self.columns(self.to_find.begin.column_name(begin_name))
        self = self.columns(self.to_find.end.column_name(end_name))
        return self

    def duration(self):
        """
        Add a column for the durations of the annotations to the output
        named "duration".
        """
        self.columns(self.to_find.duration.column_name('duration'))
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
                    if a.annotation.discourse == c.base_annotation and \
                                    c.label == 'name':
                        a.discourse_alias = c.output_label
                        discourse_found = True
                    if a.annotation.speaker == c.base_annotation and \
                                    c.label == 'name':
                        a.speaker_alias = c.output_label
                        speaker_found = True
                    elif a.annotation == c.base_annotation and \
                                    c.label == 'begin':
                        a.begin_alias = c.output_label
                        begin_found = True
                    elif a.annotation == c.base_annotation and \
                                    c.label == 'end':
                        a.end_alias = c.output_label
                        end_found = True
                if not discourse_found:
                    self._hidden_columns.append(a.annotation.discourse.name.column_name(a.discourse_alias))
                if not speaker_found:
                    self._hidden_columns.append(a.annotation.speaker.name.column_name(a.speaker_alias))
                if not begin_found:
                    self._hidden_columns.append(a.annotation.begin.column_name(a.begin_alias))
                if not end_found:
                    self._hidden_columns.append(a.annotation.end.column_name(a.end_alias))

        return QueryResults(self)

    def to_csv(self, path):
        """
        Same as ``all``, but the results of the query are output to the
        specified path as a CSV file.
        """
        results = self.all()
        if self.stop_check is not None and self.stop_check():
            return
        results.to_csv(path)

    def count(self):
        """
        Returns the number of rows in the query.
        """
        self._aggregate = [Count()]
        cypher = self.cypher()
        value = self.corpus.execute_cypher(cypher, **self.cypher_params())
        self._aggregate = []
        return value.evaluate()

    def aggregate(self, *args):
        """
        Aggregate the results of the query by a grouping factor or overall.
        Not specifying a ``group_by`` in the query will result in a single
        result for the aggregate from the whole query.
        """
        self._aggregate = args
        cypher = self.cypher()
        value = self.corpus.execute_cypher(cypher, **self.cypher_params())
        if self._group_by or any(not x.collapsing for x in self._aggregate):
            return list(value)
        elif len(self._aggregate) > 1:
            return list(value)[0]
        else:
            return value.evaluate()

    def set_type(self, *args, **kwargs):
        """
        Set properties of the returned types.
        """
        for k, v in kwargs.items():
            self._set_type[k] = v
        self._set_type_labels.extend(args)

        props_to_add = []
        for k in kwargs.keys():
            if not self.corpus.hierarchy.has_type_property(self.to_find.type, k):
                props_to_add.append((k, type(kwargs[k])))
        labels_to_add = []
        for l in args:
            if self.to_find.type not in self.corpus.hierarchy.subset_types or \
                            l not in self.corpus.hierarchy.subset_types:
                labels_to_add.append(l)

        self.corpus.execute_cypher(self.cypher(), **self.cypher_params())

        if labels_to_add:
            self.corpus.hierarchy.add_type_labels(self.corpus, self.to_find.type, labels_to_add)
        if props_to_add:
            self.corpus.hierarchy.add_type_properties(self.corpus, self.to_find.type, props_to_add)
        self._set_type = {}
        self._set_type_labels = []

    def set_token(self, *args, **kwargs):
        """
        Set properties of the returned tokens.
        """
        for k, v in kwargs.items():
            self._set_token[k] = v
        self._set_token_labels.extend(args)

        props_to_add = []
        for k in kwargs.keys():
            if not self.corpus.hierarchy.has_token_property(self.to_find.type, k):
                props_to_add.append((k, type(kwargs[k])))

        labels_to_add = []
        for l in args:
            if self.to_find.type not in self.corpus.hierarchy.subset_tokens or \
                            l not in self.corpus.hierarchy.subset_tokens:
                labels_to_add.append(l)
        self.corpus.execute_cypher(self.cypher(), **self.cypher_params())
        if labels_to_add:
            self.corpus.hierarchy.add_token_labels(self.corpus, self.to_find.type, labels_to_add)
        if props_to_add:
            self.corpus.hierarchy.add_token_properties(self.corpus, self.to_find.type, props_to_add)
        self._set_token = {}
        self._set_token_labels = []

    def remove_type_labels(self, *args):
        """ removes all type labels"""
        self._remove_type_labels.extend(args)
        self.corpus.execute_cypher(self.cypher(), **self.cypher_params())

        self.corpus.hierarchy.remove_type_labels(self.corpus, self.to_find.type, args)
        self._remove_type_labels = []

    def remove_token_labels(self, *args):
        """ removes all token labels"""
        self._remove_token_labels.extend(args)
        self.corpus.execute_cypher(self.cypher(), **self.cypher_params())

        self.corpus.hierarchy.remove_token_labels(self.corpus, self.to_find.type, args)
        self._remove_token_labels = []

    def delete(self):
        """
        Remove the results of a query from the graph.  CAUTION: this is
        irreversible.
        """
        self._delete = True
        self.corpus.execute_cypher(self.cypher(), **self.cypher_params())

    def preload(self, *args):
        self._preload.extend(args)
        return self

    def limit(self, limit):
        """ sets object limit to parameter limit """
        self._limit = limit
        return self

    def cache(self, *args):
        """

        """
        self._cache.extend(args)
        self.corpus.execute_cypher(self.cypher(), **self.cypher_params())

        props_to_add = []
        for k in args:
            k = k.output_label
            if not self.corpus.hierarchy.has_token_property(self.to_find.type, k):
                props_to_add.append((k, float))

        if props_to_add:
            self.corpus.hierarchy.add_token_properties(self.corpus, self.to_find.type, props_to_add)


class SplitQuery(GraphQuery):
    splitter = ''

    def base_query(self):
        """ sets up base query

        Returns
        -------
        q : :class: `~polyglotdb.graph.GraphQuery`
            the base query
        """
        q = GraphQuery(self.corpus, self.to_find)
        for p in q._parameters:
            if isinstance(getattr(self, p), list):
                for x in getattr(self, p):
                    getattr(q, p).append(x)
            else:
                setattr(q, p, copy.deepcopy(getattr(self, p)))
        return q

    def split_queries(self):
        """ splits a query into multiple queries """
        attribute_name = self.splitter[:-1]  # remove 's', fixme maybe?
        splitter_annotation = getattr(self.to_find, attribute_name)
        splitter_attribute = getattr(splitter_annotation, 'name')
        splitter_names = sorted(getattr(self.corpus, self.splitter))
        if self.call_back is not None:
            self.call_back(0, len(splitter_names))
        for i, x in enumerate(splitter_names):
            if self.call_back is not None:
                self.call_back(i)
                self.call_back('Querying {} {} of {} ({})...'.format(attribute_name, i, len(splitter_names), x))
            base = self.base_query()
            al = base.annotation_levels()
            add_filter = True
            if splitter_annotation in al:
                skip = False
                for c in base._criterion:
                    try:
                        if c.attribute.annotation == splitter_annotation and \
                                        c.attribute.label == 'name':
                            add_filter = False
                            if c.value != x:
                                skip = True
                                break
                    except AttributeError:
                        pass
                if skip:
                    continue
            if add_filter:
                base = base.filter(splitter_attribute == x)
            yield base

    def set_pause(self):
        """ sets a pause in queries """
        for q in self.split_queries():
            if self.stop_check is not None and self.stop_check():
                return
            q.set_pause()

    def all(self):
        """ returns all results from a query """
        results = None
        for q in self.split_queries():
            if self.stop_check is not None and self.stop_check():
                return
            if results is None:
                r = q.all()
                results = r
            else:
                results.add_results(q)
        return results

    def delete(self):
        """ deletes the query """
        for q in self.split_queries():
            if self.stop_check is not None and self.stop_check():
                return
            q.delete()

    def cache(self, *args):
        for q in self.split_queries():
            if self.stop_check is not None and self.stop_check():
                return
            q.cache(*args)

    def set_type(self, *args, **kwargs):
        """ sets the query type"""
        for q in self.split_queries():
            if self.stop_check is not None and self.stop_check():
                return
            q.set_type(*args, **kwargs)

    def set_token(self, *args, **kwargs):
        """ sets the query token """
        for q in self.split_queries():
            if self.stop_check is not None and self.stop_check():
                return
            q.set_token(*args, **kwargs)


class SpeakerGraphQuery(SplitQuery):
    splitter = 'speakers'


class DiscourseGraphQuery(SplitQuery):
    splitter = 'discourses'
