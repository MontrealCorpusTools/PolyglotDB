
from ..helper import type_attributes, key_for_cypher, value_for_cypher

from ..attributes import SubPathAnnotation, SubAnnotation

aggregate_template = '''RETURN {aggregates}{order_by}'''

distinct_template = '''RETURN {columns}{order_by}{limit}'''

set_pause_template = '''SET {alias} :pause, {type_alias} :pause_type
REMOVE {alias}:speech
WITH {alias}
OPTIONAL MATCH (prec)-[r1:precedes]->({alias})
MERGE (prec)-[:precedes_pause]->({alias})
DELETE r1
WITH {alias}, prec
OPTIONAL MATCH ({alias})-[r2:precedes]->(foll)
MERGE ({alias})-[:precedes_pause]->(foll)
DELETE r2'''

change_label_template = '''SET {alias} {value}
REMOVE {alias}{alt_value}'''

set_label_template = '''{alias} {value}'''

remove_label_template = '''{alias}{value}'''

set_property_template = '''{alias}.{attribute} = {value}'''

remove_property_template = '''{alias}.{attribute}'''

delete_template = '''DETACH DELETE {alias}'''

def generate_order_by(query):
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
                #query.columns(c[0])
        if c[1]:
            element += ' DESC'
        properties.append(element)

    if properties:
        return '\nORDER BY ' + ', '.join(properties)
    return ''

def generate_delete(query):
    kwargs = {}
    kwargs['alias'] = query.to_find.alias
    return_statement = delete_template.format(**kwargs)
    return return_statement

def generate_aggregate(query):
    properties = []
    for g in query._group_by:
        properties.append(g.aliased_for_output())
    if any(not x.collapsing for x in query._aggregate):
        for c in query._columns:
            properties.append(c.aliased_for_output())
    if len(query._order_by) == 0 and len(query._group_by) > 0:
        query._order_by.append((query._group_by[0], False))
    for a in query._aggregate:
        properties.append(a.for_cypher())
    return ', '.join(properties)

def generate_distinct(query):

    properties = []
    for c in query._columns:
        properties.append(c.aliased_for_output())
    if properties:
        return ', '.join(properties)
    else:
        properties = [query.to_find.alias, query.to_find.type_alias]
        for a in query._preload:
            properties.extend(a.withs)
            if isinstance(a, SubAnnotation):
                pass
        return ', '.join(properties)

def generate_cache(query):
    properties = []
    for c in query._cache:
        kwargs = {'alias': c.base_annotation.alias,
                'attribute': c.output_alias,
                'value': c.for_cypher()
                }
        set_string = set_property_template.format(**kwargs)
        properties.append(set_string)
    if properties:
        return 'SET {}'.format(', '.join(properties))
    else:
        return ''

def generate_return(query):
    kwargs = {'order_by': '', 'columns':''}
    return_statement = ''
    if query._delete:
        return generate_delete(query)
    if query._cache:
        return generate_cache(query)
    set_strings = []
    set_label_strings = []
    remove_label_strings = []
    for k,v in query._set_token.items():
        if v is None:
            v = 'NULL'
        else:
            v = value_for_cypher(v)
        set_strings.append(set_property_template.format(alias = query.to_find.alias, attribute = k, value = v))
    for k,v in query._set_type.items():
        if v is None:
            v = 'NULL'
        else:
            v = value_for_cypher(v)
        set_strings.append(set_property_template.format(alias = query.to_find.type_alias, attribute = k, value = v))
    if query._set_token_labels:
        kwargs = {}
        kwargs['alias'] = query.to_find.alias
        kwargs['value'] = ':' + ':'.join(map(key_for_cypher, query._set_token_labels))
        set_label_strings.append(set_label_template.format(**kwargs))
    if query._set_type_labels:
        kwargs = {}
        kwargs['alias'] = query.to_find.type_alias
        kwargs['value'] = ':' + ':'.join(map(key_for_cypher, query._set_type_labels))
        set_label_strings.append(set_label_template.format(**kwargs))
    if set_label_strings or set_strings:
        return_statement = 'SET ' + ', '.join(set_label_strings + set_strings)
    if query._remove_type_labels:
        kwargs = {}
        kwargs['alias'] = query.to_find.type_alias
        kwargs['value'] = ':' + ':'.join(map(key_for_cypher, query._remove_type_labels))
        remove_label_strings.append(remove_label_template.format(**kwargs))
    if query._remove_token_labels:
        kwargs = {}
        kwargs['alias'] = query.to_find.type_alias
        kwargs['value'] = ':' + ':'.join(map(key_for_cypher, query._remove_token_labels))
        remove_label_strings.append(remove_label_template.format(**kwargs))
    if remove_label_strings:
        if return_statement:
            return_statement += '\nWITH {alias}, {type_alias}\n'.format(alias = query.to_find.alias, type_alias = query.to_find.type_alias)
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
