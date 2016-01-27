
def generate_wheres(criterion, wheres = None):
    properties = []
    for c in criterion:
        properties.append(c.for_cypher())
    if wheres is not None:
        properties.extend(wheres)
    where_string = ''
    if properties:
        where_string += 'WHERE ' + '\nAND '.join(properties)
    return where_string
