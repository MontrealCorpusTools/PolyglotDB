
def generate_wheres(criterion, wheres = None):
    """
    Generates where statements

    Parameters
    ----------
    criterion : :class: `~polyglotdb.graph.GraphQuery`
        query object
    wheres : list
        Defaults to None
        list of where statements

    Returns
    -------
    str
        cypher string containing where statements

    """
    properties = []
    for c in criterion:
        if not c.is_matrix():
            continue
        properties.append(c.for_cypher())
    if wheres is not None:
        properties.extend(wheres)
    where_string = ''
    if properties:
        where_string += 'WHERE ' + '\nAND '.join(properties)
    return where_string
