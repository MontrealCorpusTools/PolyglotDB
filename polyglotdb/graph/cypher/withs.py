
from ..attributes import SubAnnotation

def generate_withs(query, all_withs):
    """
    Generates with statements
    
    Parameters
    ----------
    query : :class: `~polyglotdb.graph.GraphQuery`
        query object
    all_withs : list
        Defaults to None
        list of with statements

    Returns
    -------
    str
        cypher string containing with statements
    
    """
    statements = [withs_to_string(all_withs)]
    for c in query._criterion:
        for a in c.attributes:
            if a.with_alias not in all_withs:
                statement = a.annotation.subquery(all_withs, query._criterion)
                statements.append(statement)

                all_withs.update(a.with_aliases)
    if query._columns:
        for a in query._columns:
            if a.with_alias not in all_withs:
                statement = a.annotation.subquery(all_withs, query._criterion)
                statements.append(statement)

                all_withs.update(a.with_aliases)
    elif query._cache:
        for a in query._cache:
            if a.with_alias not in all_withs:
                statement = a.annotation.subquery(all_withs, query._criterion)
                statements.append(statement)

                all_withs.update(a.with_aliases)
    elif query._aggregate:
        for a in query._group_by:
            if a.with_alias not in all_withs:
                statement = a.annotation.subquery(all_withs, query._criterion)
                statements.append(statement)

                all_withs.update(a.with_aliases)
        for agg in query._aggregate:
            if agg.collapsing:
                continue
            a = agg.attribute
            if a.with_alias not in all_withs:
                statement = a.annotation.subquery(all_withs, query._criterion)
                statements.append(statement)

                all_withs.update(a.with_aliases)
    elif query._preload:
        for a in query._preload:
            if a.with_alias not in all_withs:
                a.with_subannotations = True
                statement = a.subquery(all_withs, query._criterion)
                statements.append(statement)

                all_withs.update(a.withs)
    return '\n'.join(statements)

def withs_to_string(withs):
    """Translates with lists into 'with' statements"""
    return 'WITH ' + ', '.join(withs)
