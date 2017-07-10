from ...base.complex import ComplexClause
from ...base.helper import key_for_cypher, value_for_cypher

from .matches import generate_match

from .withs import generate_withs

from .wheres import generate_wheres

from .returns import generate_return

from ..attributes.base import AnnotationAttribute

template = '''{match}
{where}
{optional_match}
{with}
{return}'''


def query_to_cypher(query):
    """
    translates a query object into a cypher formatted string

    Parameters
    ----------
    query : :class: `~polyglotdb.query.annotations.GraphQuery`
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
    annotation_levels = query.annotation_levels()

    match_strings = []
    optional_match_strings = []
    optional_where_strings = []
    where_strings = []

    all_withs = set()

    filter_annotations = set()
    for c in query._criterion:
        for a in c.annotations:
            filter_annotations.add(a)

    for k, v in annotation_levels.items():
        if k.has_subquery:
            continue
        statements, optional_statements, withs, wheres, optional_wheres = generate_match(query, k, v,
                                                                                         filter_annotations)
        all_withs.update(withs)
        match_strings.extend(statements)
        optional_match_strings.extend(optional_statements)
        optional_where_strings.extend(optional_wheres)
        where_strings.extend(wheres)

    kwargs['match'] = 'MATCH ' + ',\n'.join(match_strings)

    if optional_match_strings:
        s = ''
        for i, o in enumerate(optional_match_strings):
            s += 'OPTIONAL MATCH ' + o + '\n'
            w = optional_where_strings[i]
            if w:
                s += 'WHERE ' + w + '\n'
        kwargs['optional_match'] = s

    kwargs['where'] = generate_wheres(query._criterion, wheres)

    kwargs['with'] = generate_withs(query, all_withs)

    kwargs['return'] = generate_return(query)
    cypher = template.format(**kwargs)
    return cypher
template = '''{match}
{where}
{optional_match}
{with}
{return}'''

aggregate_template = '''RETURN {aggregates}{order_by}'''

distinct_template = '''RETURN {columns}{order_by}{limit}'''

set_label_template = '''{alias} {value}'''

remove_label_template = '''{alias}{value}'''

set_property_template = '''{alias}.{attribute} = {value}'''

remove_property_template = '''{alias}.{attribute}'''

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
    for c in query._columns + query._hidden_columns:
        properties.append(c.aliased_for_output())
    if properties:
        return ', '.join(properties)
    else:
        properties = query.to_find.withs
        for a in query._preload:
            properties.extend(a.withs)
        return ', '.join(properties)


def generate_cache(query):
    """
    Generates cache from query object

    Parameters
    ----------
    query : :class: `~polyglotdb.graph.GraphQuery`
        a query object

    Returns
    -------
    str
        cypher string to generate cache
    """
    properties = []
    for c in query._cache:
        kwargs = {'alias': c.node.cache_alias,
                  'attribute': c.output_alias,
                  'value': c.for_cypher()
                  }
        if c.label == 'position':
            kwargs['alias'] = query.to_find.alias
        set_string = set_property_template.format(**kwargs)
        properties.append(set_string)
    if properties:
        return 'SET {}'.format(', '.join(properties))
    else:
        return ''

delete_template = '''DETACH DELETE {alias}'''

def generate_delete(query):
    """
    Generates a statement to delete a query

    Parameters
    ----------
    query : :class: `~polyglotdb.graph.GraphQuery`
        a query object

    Returns
    -------
    return_statement : str
        the cypher formatted delete statement
    """
    kwargs = {}
    kwargs['alias'] = query.to_find.alias
    return_statement = delete_template.format(**kwargs)
    return return_statement

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
    if query._delete:
        return generate_delete(query)
    if query._cache:
        return generate_cache(query)
    set_strings = []
    set_label_strings = []
    remove_label_strings = []
    if 'pause' in query._set_properties:
        kwargs = {}
        kwargs['alias'] = query.to_find.alias
        kwargs['type_alias'] = query.to_find.type_alias

        return_statement = set_pause_template.format(**kwargs)
        return return_statement
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
    for node in nodes:
        if node.has_subquery:
            continue
        match_strings.add(node.for_match())
        withs.update(node.withs)

    kwargs['match'] = 'MATCH ' + ',\n'.join(match_strings)

    # generate main filters

    properties = []
    for c in query._criterion:
        if c.in_subquery:
            continue
        properties.append(c.for_cypher())
    if properties:
        kwargs['where'] += 'WHERE ' + '\nAND '.join(properties)

    optional_nodes = query.optional_nodes()
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

    with_statements = [withs_to_string(withs)]

    for node in nodes:
        if not node.has_subquery:
            continue
        statement = node.subquery(withs, query._criterion)
        with_statements.append(statement)

        withs.update(node.withs)

    #optional_nodes = list(optional_nodes)
    #sorted_optional_nodes = []
    #for node in optional_nodes:
    #    if any(x.non_optional for x in node.nodes):

    for node in optional_nodes:
        if not node.has_subquery:
            continue
        statement = node.subquery(withs, query._criterion, optional=True)
        with_statements.append(statement)

        withs.update(node.withs)
    kwargs['with'] = '\n'.join(with_statements)

    kwargs['return'] = generate_return(query)
    cypher = template.format(**kwargs)
    return cypher


def withs_to_string(withs):
    """Translates with lists into 'with' statements"""
    return 'WITH ' + ', '.join(withs)