
from ..helper import type_attributes, key_for_cypher, value_for_cypher

aggregate_template = '''RETURN {aggregates}{additional_columns}{order_by}'''

distinct_template = '''RETURN {columns}{additional_columns}{order_by}'''

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

create_subannotation_template = '''CREATE (:{type}:{corpus_name}:speech {{{properties}}})-[:annotates]->({node_alias})'''
property_template = '''{key}: {value}'''

def generate_create_subannotation(query):
    from uuid import uuid1
    id_query = True
    for c in self._criterion:
        if c.attribute.label == 'id':
            break
    else:
        id_query = False
    properties = []
    for sa in query._add_subannotations:
        kwargs = {'corpus_name': query.corpus.corpus_name,
                    'type': sa[0],
                    'node_alias':query.to_find.alias}
        if id_query:
            props = []
            props.append(property_template.format(key = 'id', value = value_for_cypher(uuid1())))
            props.append(property_template.format(key = 'begin', value = value_for_cypher(sa[1])))
            props.append(property_template.format(key = 'end', value = value_for_cypher(sa[2])))
            if sa[-1] is not None:
                props.append(property_template.format(key = 'label', value = value_for_cypher(sa[-1])))
            kwargs['properties'] = ', '.join(props)
        else:

            pass # need to figure out how to get ids for these
        string = create_subannotation_template.format(**kwargs)

def generate_order_by(query):
    properties = []
    for c in query._order_by:
        ac_set = set(query._additional_columns)
        gb_set = set(query._group_by)
        h_c = hash(c[0])
        for col in ac_set:
            if h_c == hash(col):
                element = col.output_alias
                break
        else:
            for col in gb_set:
                if h_c == hash(col):
                    element = col.output_alias
                    break
            else:
                query._additional_columns.append(c[0])
                element = c[0].output_alias
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


def generate_return(query):
    kwargs = {'order_by': '', 'additional_columns':'', 'columns':''}
    return_statement = ''
    if query._delete:
        return generate_delete(query)
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
        properties = []
        for c in query._columns:
            properties.append(c.aliased_for_output())
        if properties:
            kwargs['columns'] = ', '.join(properties)

    kwargs['order_by'] = generate_order_by(query)

    properties = []
    for c in query._additional_columns:
        if c in query._group_by:
            continue
        properties.append(c.aliased_for_output())
    if properties:
        string = ', '.join(properties)
        if kwargs['columns'] or ('aggregates' in kwargs and kwargs['aggregates']):
            string = ', ' + string
        kwargs['additional_columns'] += string
    return template.format(**kwargs)
