from .results import BaseQueryResults

from .func import Count
from ..base.helper import key_for_cypher, value_for_cypher


class BaseQuery(object):
    query_template = '''{match}
    {where}
    {optional_match}
    {with}
    {return}'''

    delete_template = '''DETACH DELETE {alias}'''

    aggregate_template = '''RETURN {aggregates}{order_by}'''

    distinct_template = '''RETURN {columns}{order_by}{offset}{limit}'''

    set_label_template = '''{alias} {value}'''

    remove_label_template = '''{alias}{value}'''

    set_property_template = '''{alias}.{attribute} = {value}'''

    def __init__(self, corpus, to_find):
        self.corpus = corpus
        self.to_find = to_find
        self._criterion = []
        self._columns = []
        self._hidden_columns = []
        self._order_by = []
        self._group_by = []
        self._aggregate = []
        self._preload = []
        self._cache = []

        self._delete = False

        self._set_labels = []
        self._remove_labels = []

        self._set_properties = {}

        self._limit = None
        self._offset = None
        self.call_back = None
        self.stop_check = None

    def cache(self):
        raise NotImplementedError

    def required_nodes(self):
        ns = {self.to_find}
        tf_type = type(self.to_find)
        for c in self._criterion:
            ns.update(x for x in c.nodes if type(x) is not tf_type)
        for c in self._columns + self._hidden_columns + self._aggregate + self._preload + self._cache:
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

    def offset(self, number):
        self._offset = number
        return self

    def filter(self, *args):
        """
        Apply one or more filters to a query.
        """
        from .elements import EqualClauseElement
        for a in args:
            for c in self._criterion:
                if isinstance(c, EqualClauseElement) and isinstance(a, EqualClauseElement) and \
                        c.attribute.node == a.attribute.node and c.attribute.label == a.attribute.label:
                    c.value = a.value
                    break
            else:
                self._criterion.append(a)
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
        return list(value[0].values())[0]

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
            return list(list(value)[0].values())[0]

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
        """
        Generates a Cypher statement based on the query.
        """
        kwargs = {'match': '',
                  'optional_match': '',
                  'where': '',
                  'with': '',
                  'return': ''}

        # generate initial match strings

        match_strings = set()
        withs = set()
        nodes = self.required_nodes()
        for node in nodes:
            if node.has_subquery:
                continue
            match_strings.add(node.for_match())
            withs.update(node.withs)

        kwargs['match'] = 'MATCH ' + ',\n'.join(match_strings)

        # generate main filters

        properties = []
        for c in self._criterion:
            if c.in_subquery:
                continue
            properties.append(c.for_cypher())
        if properties:
            kwargs['where'] += 'WHERE ' + '\nAND '.join(properties)

        optional_nodes = self.optional_nodes()
        optional_match_strings = []
        for node in optional_nodes:
            if node.has_subquery:
                continue
            optional_match_strings.append(node.for_match())
            withs.update(node.withs)
        if optional_match_strings:
            s = ''
            for i, o in enumerate(optional_match_strings):
                s += 'OPTIONAL MATCH ' + o + '\n'
            kwargs['optional_match'] = s

        # generate subqueries

        with_statements = ['WITH ' + ', '.join(withs)]

        for node in nodes:
            if not node.has_subquery:
                continue
            statement = node.subquery(withs, self._criterion)
            with_statements.append(statement)

            withs.update(node.withs)

        for node in optional_nodes:
            if not node.has_subquery:
                continue
            statement = node.subquery(withs, self._criterion, optional=True)
            with_statements.append(statement)

            withs.update(node.withs)
        kwargs['with'] = '\n'.join(with_statements)

        kwargs['return'] = self.generate_return()
        cypher = self.query_template.format(**kwargs)

        return cypher

    def create_subset(self, label):
        self._set_labels.append(label)
        self.corpus.execute_cypher(self.cypher(), **self.cypher_params())
        self._set_labels = []

    def remove_subset(self, label):
        self._remove_labels.append(label)
        self.corpus.execute_cypher(self.cypher(), **self.cypher_params())
        self._remove_labels = []

    def delete(self):
        """
        Remove the results of a query from the graph.  CAUTION: this is
        irreversible.
        """
        self._delete = True
        self.corpus.execute_cypher(self.cypher(), **self.cypher_params())

    def set_properties(self, **kwargs):
        self._set_properties = {k: v for k,v in kwargs.items()}
        self.corpus.execute_cypher(self.cypher(), **self.cypher_params())
        self._set_properties = {}

    def all(self):
        return BaseQueryResults(self)

    def get(self):
        r = BaseQueryResults(self)
        if len(r) > 1:
            raise Exception("Can't use get on query with more than one result.")
        return r[0]

    def cypher_params(self):
        from ..base.complex import ComplexClause
        from ..base.elements import SubsetClauseElement, NotSubsetClauseElement
        from ..base.attributes import NodeAttribute
        params = {}
        for c in self._criterion:
            if isinstance(c, ComplexClause):
                params.update(c.generate_params())
            elif isinstance(c, (SubsetClauseElement, NotSubsetClauseElement)):
                pass
            else:
                try:
                    if not isinstance(c.value, NodeAttribute):
                        params[c.cypher_value_string()[1:-1].replace('`', '')] = c.value
                except AttributeError:
                    pass
        return params

    def generate_return(self):
        """
        Generates final statement from query object, calling whichever one of the other generate statements is specified in the query obj

        Parameters
        ----------
        query : :class: `~polyglotdb.graph.GraphQuery`
            a query object

        Returns
        -------
        str
            cypher formatted string
        """
        if self._delete:
            statement = self._generate_delete_return()
        elif self._cache:
            statement = self._generate_cache_return()
        elif self._set_properties:
            statement = self._generate_set_properties_return()
        elif self._set_labels:
            statement = self._generate_set_labels_return()
        elif self._remove_labels:
            statement = self._generate_remove_labels_return()
        elif self._aggregate:
            statement = self._generate_aggregate_return()
        else:
            statement = self._generate_distinct_return()
        return statement

    def _generate_delete_return(self):
        kwargs = {}
        kwargs['alias'] = self.to_find.alias
        return_statement = self.delete_template.format(**kwargs)
        return return_statement

    def _generate_cache_return(self):
        properties = []
        for c in self._cache:
            kwargs = {'alias': c.node.cache_alias,
                      'attribute': c.output_alias,
                      'value': c.for_cypher()
                      }
            if c.label == 'position':
                kwargs['alias'] = self.to_find.alias
            set_string = self.set_property_template.format(**kwargs)
            properties.append(set_string)
        return 'SET {}'.format(', '.join(properties))

    def _generate_remove_labels_return(self):
        remove_label_strings = []
        kwargs = {}
        kwargs['alias'] = self.to_find.alias
        kwargs['value'] = ':' + ':'.join(map(key_for_cypher, self._remove_labels))
        remove_label_strings.append(self.remove_label_template.format(**kwargs))
        return_statement = ''
        if remove_label_strings:
            if return_statement:
                return_statement += '\nWITH {alias}\n'.format(alias=self.to_find.alias)
            return_statement += '\nREMOVE ' + ', '.join(remove_label_strings)
        return return_statement

    def _generate_set_properties_return(self):
        set_strings = []
        for k, v in self._set_properties.items():
            if v is None:
                v = 'NULL'
            else:
                v = value_for_cypher(v)
            s = self.set_property_template.format(alias=self.to_find.alias, attribute=k, value=v)
            set_strings.append(s)
        return 'SET ' + ', '.join(set_strings)

    def _generate_set_labels_return(self):
        set_label_strings = []
        kwargs = {}
        kwargs['alias'] = self.to_find.alias
        kwargs['value'] = ':' + ':'.join(map(key_for_cypher, self._set_labels))
        set_label_strings.append(self.set_label_template.format(**kwargs))
        return 'SET ' + ', '.join(set_label_strings)

    def _generate_aggregate_return(self):
        kwargs = {'order_by': self._generate_order_by(),
                  'limit': self._generate_limit()}
        properties = []
        for g in self._group_by:
            properties.append(g.aliased_for_output())
        if any(not x.collapsing for x in self._aggregate):
            for c in self._columns:
                properties.append(c.aliased_for_output())
        if len(self._order_by) == 0 and len(self._group_by) > 0:
            self._order_by.append((self._group_by[0], False))
        for a in self._aggregate:
            properties.append(a.aliased_for_output())
        kwargs['aggregates'] = ', '.join(properties)
        return self.aggregate_template.format(**kwargs)

    def _generate_distinct_return(self):
        kwargs = {'order_by': self._generate_order_by(),
                  'limit': self._generate_limit(),
                  'offset': self._generate_offset()}
        properties = []
        for c in self._columns + self._hidden_columns:
            properties.append(c.aliased_for_output())
        if not properties:
            properties = self.to_find.withs
            for a in self._preload:
                properties.extend(a.withs)
        kwargs['columns'] = ', '.join(properties)
        return self.distinct_template.format(**kwargs)

    def _generate_limit(self):
        if self._limit is not None:
            return '\nLIMIT {}'.format(self._limit)
        return ''

    def _generate_offset(self):
        if self._offset is not None:
            return '\nSKIP {}'.format(self._offset)
        return ''

    def _generate_order_by(self):
        properties = []
        for c in self._order_by:
            ac_set = set(self._columns)
            gb_set = set(self._group_by)
            h_c = hash(c[0])
            for col in ac_set:
                if h_c == hash(col):
                    element = col.for_cypher()
                    break
            else:
                for col in gb_set:
                    if h_c == hash(col):
                        element = col.for_cypher()
                        break
                else:
                    element = c[0].for_cypher()
                    # query.columns(c[0])
            if c[1]:
                element += ' DESC'
            properties.append(element)

        if properties:
            return '\nORDER BY ' + ', '.join(properties)
        return ''
