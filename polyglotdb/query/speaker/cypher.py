from ..base.complex import ComplexClause
from ..base.helper import key_for_cypher, value_for_cypher

from .attributes import SpeakerAttribute

template = '''{match}
{where}
{with}
{return}'''

aggregate_template = '''RETURN {aggregates}{order_by}'''

distinct_template = '''RETURN {columns}{order_by}{limit}'''

set_label_template = '''{alias} {value}'''

remove_label_template = '''{alias}{value}'''

set_property_template = '''{alias}.{attribute} = {value}'''

remove_property_template = '''{alias}.{attribute}'''





def generate_order_by(query):
    """
    Generates cypher string to order columns, groups, and elements of query

    Parameters
    ----------
    query : :class: `~polyglotdb.graph.GraphQuery`
        a query object

    Returns
    -------
    str
        a cypher string containing columns, groups, and elements of query"""
    properties = []
    for c in query._order_by:
        ac_set = set(query._columns)
        gb_set = set(query._group_by)
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


def generate_aggregate(query):
    """
    aggregates properties of a query into one string

    Parameters
    ----------
    query : :class: `~polyglotdb.graph.GraphQuery`
        a query object

    Returns
    -------
    str
        aggregated properties of query
     """
    properties = []
    for g in query._group_by:
        properties.append(g.aliased_for_output())
    if any(not x.collapsing for x in query._aggregate):
        for c in query._columns:
            properties.append(c.aliased_for_output())
    if len(query._order_by) == 0 and len(query._group_by) > 0:
        query._order_by.append((query._group_by[0], False))
    for a in query._aggregate:
        properties.append(a.aliased_for_output())
    return ', '.join(properties)


def generate_distinct(query):
    """
    Generates string of either columns or aliases

    Parameters
    ----------
    query : :class: `~polyglotdb.graph.GraphQuery`
        a query object

    Returns
    -------
    str
        string of columns or aliases
    """

    properties = []
    for c in query._columns:
        properties.append(c.aliased_for_output())
    if properties:
        return ', '.join(properties)
    else:
        properties = [query.to_find.alias]
        for a in query._preload:
            properties.extend(a.withs)
        return ', '.join(properties)


def generate_return(query):
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
    kwargs = {'order_by': '', 'columns': ''}
    return_statement = ''
    set_strings = []
    set_label_strings = []
    remove_label_strings = []
    for k, v in query._set_properties.items():
        if v is None:
            v = 'NULL'
        else:
            v = value_for_cypher(v)
        set_strings.append(set_property_template.format(alias=query.to_find.alias, attribute=k, value=v))
    if query._set_labels:
        kwargs = {}
        kwargs['alias'] = query.to_find.alias
        kwargs['value'] = ':' + ':'.join(map(key_for_cypher, query._set_labels))
        set_label_strings.append(set_label_template.format(**kwargs))
    if set_label_strings or set_strings:
        return_statement = 'SET ' + ', '.join(set_label_strings + set_strings)
    if query._remove_labels:
        kwargs = {}
        kwargs['alias'] = query.to_find.alias
        kwargs['value'] = ':' + ':'.join(map(key_for_cypher, query._remove_labels))
        remove_label_strings.append(remove_label_template.format(**kwargs))
    if remove_label_strings:
        if return_statement:
            return_statement += '\nWITH {alias}\n'.format(alias=query.to_find.alias)
        return_statement += '\nREMOVE ' + ', '.join(remove_label_strings)
    if return_statement:
        return return_statement

    if query._aggregate:
        template = aggregate_template
        kwargs['aggregates'] = generate_aggregate(query)
    else:
        template = distinct_template
        kwargs['columns'] = generate_distinct(query)
        if query._limit is not None:
            kwargs['limit'] = '\nLIMIT {}'.format(query._limit)
        else:
            kwargs['limit'] = ''

    kwargs['order_by'] = generate_order_by(query)

    return template.format(**kwargs)


def query_to_cypher(query):
    """
    translates a query object into a cypher formatted string

    Parameters
    ----------
    query : :class: `~polyglotdb.graph.GraphQuery`
        the query to transform

    Returns
    -------
    cypher : str
        the cypher-formatted string
    """
    kwargs = {'match': '',
              'optional_match': '',
              'where': '',
              'with': '',
              'return': ''}

    # generate initial match strings

    match_strings = set()
    withs = set()
    nodes = query.required_nodes()
    nodes.update(query.optional_nodes())
    print(nodes)
    for node in nodes:
        if node.has_subquery:
            continue
        match_strings.add(node.for_match())
        withs.update(node.withs)

    kwargs['match'] = 'MATCH ' + ',\n'.join(match_strings)

    # generate main filters

    properties = []
    for c in query._criterion:
        properties.append(c.for_cypher())
    if properties:
        kwargs['where'] += 'WHERE ' + '\nAND '.join(properties)

    # generate subqueries

    with_statements = [withs_to_string(withs)]

    for node in nodes:
        if not node.has_subquery:
            continue
        statement = node.subquery(withs, query._criterion)
        with_statements.append(statement)

        withs.update(node.withs)
    kwargs['with'] = '\n'.join(with_statements)

    kwargs['return'] = generate_return(query)
    cypher = template.format(**kwargs)
    return cypher


def withs_to_string(withs):
    """Translates with lists into 'with' statements"""
    return 'WITH ' + ', '.join(withs)