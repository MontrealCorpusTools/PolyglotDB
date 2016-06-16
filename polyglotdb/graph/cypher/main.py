
from collections import defaultdict

from ..helper import key_for_cypher, value_for_cypher

from ..attributes import AnnotationAttribute, PathAnnotation, Attribute, PathAttribute

from ..elements import ComplexClause

from .matches import generate_match

from .withs import generate_withs

from .wheres import generate_wheres

from .returns import generate_return

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
    query : :class: `~polyglotdb.graph.GraphQuery`
        the query to transform

    Returns
    -------
    cypher : str
        the cypher-formatted string
    """
    kwargs = {'match': '',
            'optional_match':'',
            'where': '',
            'with': '',
            'return':''}
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

    for k,v in annotation_levels.items():
        if k.has_subquery:
            continue
        statements,optional_statements, withs, wheres, optional_wheres = generate_match(query, k,v, filter_annotations)
        all_withs.update(withs)
        match_strings.extend(statements)
        optional_match_strings.extend(optional_statements)
        optional_where_strings.extend(optional_wheres)
        where_strings.extend(wheres)

    kwargs['match'] = 'MATCH ' + ',\n'.join(match_strings)

    if optional_match_strings:
        kwargs['optional_match'] = 'OPTIONAL MATCH ' + ',\n'.join(optional_match_strings)
        if optional_where_strings:
            kwargs['optional_match'] += '\nWHERE ' + ',\n'.join(optional_where_strings)

    kwargs['where'] = generate_wheres(query._criterion, wheres)

    kwargs['with'] = generate_withs(query, all_withs)

    kwargs['return'] = generate_return(query)
    cypher = template.format(**kwargs)
    return cypher

def query_to_params(query):
    """
    translates a query object into a dict of parameters

    Parameters
    ----------
    query : :class: `~polyglotdb.graph.GraphQuery`
        the query to transform

    Returns
    -------
    params : dict
        the parameter dictionary
    """
    params = {}
    for c in query._criterion:
        if isinstance(c, ComplexClause):
            params.update(c.generate_params())
        else:
            try:
                if not isinstance(c.value, Attribute):
                    params[c.cypher_value_string()[1:-1].replace('`','')] = c.value
            except AttributeError:
                pass
    return params
