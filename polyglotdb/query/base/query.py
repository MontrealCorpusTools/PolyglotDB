from .results import BaseQueryResults
from .func import Count


class BaseQuery(object):
    def __init__(self, corpus, to_find):
        self.corpus = corpus
        self.to_find = to_find
        self._criterion = []
        self._columns = []
        self._order_by = []
        self._group_by = []
        self._aggregate = []
        self._preload = []
        self._cache = []

        self._set_labels = []
        self._remove_labels = []

        self._set_properties = {}

        self._limit = None
        self.call_back = None
        self.stop_check = None

    def cache(self):
        raise NotImplementedError

    def required_nodes(self):
        ns = {self.to_find}
        tf_type = type(self.to_find)
        for c in self._criterion:
            ns.update(x for x in c.nodes if type(x) is not tf_type)
        for c in self._columns + self._aggregate + self._preload + self._cache:
            ns.update(x for x in c.nodes if type(x) is not tf_type and x.non_optional)
        for c, _ in self._order_by:
            ns.update(x for x in c.nodes if type(x) is not tf_type and x.non_optional)
        return ns

    def optional_nodes(self):
        required_nodes = self.required_nodes()
        ns = set()
        tf_type = type(self.to_find)
        for c in self._columns + self._aggregate + self._preload + self._cache:
            ns.update(x for x in c.nodes if type(x) is not tf_type and x not in required_nodes)
        for c, _ in self._order_by:
            ns.update(x for x in c.nodes if type(x) is not tf_type and x not in required_nodes)
        return sorted(ns)

    def clear_columns(self):
        """
        Remove any columns specified.  The default columns for any query
        are the id of the token and the label of the type.
        """
        self._columns = []
        return self

    def filter(self, *args):
        """
        Apply one or more filters to a query.
        """
        self._criterion.extend(args)
        return self

    def columns(self, *args):
        """
        Add one or more additional columns to the results.

        Columns should be :class:`~polyglotdb.query.base.Attribute` objects.
        """
        column_set = set(self._columns)
        for c in args:
            if c in column_set:
                continue
            else:
                self._columns.append(c)
                # column_set.add(c) # FIXME failing tests
        return self

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
        self._aggregate.extend(args)
        cypher = self.cypher()
        value = self.corpus.execute_cypher(cypher, **self.cypher_params())
        if self._group_by or any(not x.collapsing for x in self._aggregate):
            return list(value)
        elif len(self._aggregate) > 1:
            return list(value)[0]
        else:
            return value.evaluate()

    def preload(self, *args):
        self._preload.extend(args)
        return self

    def limit(self, limit):
        """ sets object limit to parameter limit """
        self._limit = limit
        return self

    def to_json(self):
        data = {'corpus_name': self.corpus.corpus_name,
                'filters': [x.for_json() for x in self._criterion],
                'columns': [x.for_json() for x in self._columns]}
        return data

    def cypher(self):
        pass

    def all(self):
        return BaseQueryResults(self)

    def get(self):
        print(self.cypher())
        r = BaseQueryResults(self)
        if len(r) > 1:
            raise Exception("Can't use get on query with more than one result.")
        return r[0]

    def cypher_params(self):
        from ..base.complex import ComplexClause
        from ..base.attributes import NodeAttribute
        params = {}
        for c in self._criterion:
            if isinstance(c, ComplexClause):
                params.update(c.generate_params())
            else:
                try:
                    if not isinstance(c.value, NodeAttribute):
                        params[c.cypher_value_string()[1:-1].replace('`', '')] = c.value
                except AttributeError:
                    pass
        return params
