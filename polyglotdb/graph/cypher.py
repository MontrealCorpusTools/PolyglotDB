
from collections import defaultdict

from .helper import type_attributes, key_for_cypher, value_for_cypher

from .attributes import AnnotationAttribute, PathAnnotation, Attribute, PauseAnnotation

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

anchor_template = '''({token_alias})-[:is_a]->({type_alias})'''

prec_template = '''({prev_type_alias})<-[:is_a]-({prev_alias})-[:precedes]->({node_alias})'''
foll_template = '''({node_alias})-[:precedes]->({foll_alias})-[:is_a]->({foll_type_alias})'''

prec_pause_template = '''{path_alias} = (:speech:word)-[:precedes_pause*0..]->({node_alias})'''
foll_pause_template = '''{path_alias} = ({node_alias})-[:precedes_pause*0..]->(:speech:word)'''

delete_template = '''DETACH DELETE {alias}'''

template = '''{match}
{where}
{optional_match}
{with}
{return}'''

def generate_annotation_with(annotation):
    return [annotation.alias, annotation.begin_alias, annotation.end_alias]

def criterion_to_where(criterion, wheres = None):
    properties = []
    for c in criterion:
        properties.append(c.for_cypher())
    if wheres is not None:
        properties.extend(wheres)
    where_string = ''
    if properties:
        where_string += 'WHERE ' + '\nAND '.join(properties)
    return where_string

def figure_property(annotation, property_string, withs):
    if getattr(annotation, property_string) in withs:
        return getattr(annotation, property_string)
    else:
        return getattr(annotation, 'define_'+property_string)

    return match_template.format(anchor_string, where_string, with_string), withs

def create_return_statement(query):
    kwargs = {'order_by': '', 'additional_columns':'', 'columns':''}
    return_statement = ''
    if query._delete:
        kwargs = {}
        kwargs['alias'] = query.to_find.alias
        return_statement = delete_template.format(**kwargs)
        return return_statement
    set_strings = []
    set_label_strings = []
    remove_label_strings = []
    if 'pause' in query._set_token:
        kwargs = {}
        kwargs['alias'] = query.to_find.alias
        kwargs['type_alias'] = query.to_find.type_alias

        return_statement = set_pause_template.format(**kwargs)
        return return_statement
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
        properties = []
        for g in query._group_by:
            properties.append(g.aliased_for_output())
        if len(query._order_by) == 0 and len(query._group_by) > 0:
            query._order_by.append((query._group_by[0], False))
        for a in query._aggregate:
            properties.append(a.for_cypher())
        kwargs['aggregates'] = ', '.join(properties)
    else:
        template = distinct_template
        properties = []
        for c in query._columns:
            properties.append(c.aliased_for_output())
        if properties:
            kwargs['columns'] = ', '.join(properties)

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
        kwargs['order_by'] += '\nORDER BY ' + ', '.join(properties)

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


def generate_token_match(annotation_type, annotation_list, filter_annotations):
    annotation_list = sorted(annotation_list, key = lambda x: x.pos)
    prec_condition = ''
    foll_condition = ''
    defined = set()

    statements = []
    wheres = []
    optional_wheres = []
    current = annotation_list[0].pos
    optional_statements = []
    if isinstance(annotation_type, PauseAnnotation):
        prec = prec_pause_template
        foll = foll_pause_template
    else:
        prec = prec_template
        foll = foll_template
        kwargs = {}
        kwargs['token_alias'] = annotation_type.define_alias
        kwargs['type_alias'] = annotation_type.define_type_alias
        anchor_string = anchor_template.format(**kwargs)
        statements.append(anchor_string)
        defined.add(annotation_type.alias)
        defined.add(annotation_type.type_alias)
    for a in annotation_list:
        where = ''
        if a.pos == 0:
            if isinstance(annotation_type, PauseAnnotation):
                kwargs = {}
                kwargs['token_alias'] = annotation_type.define_alias
                kwargs['type_alias'] = annotation_type.define_type_alias
                anchor_string = anchor_template.format(**kwargs)

                statements.append(anchor_string)
                defined.add(annotation_type.alias)
                defined.add(annotation_type.type_alias)
            continue
        elif a.pos < 0:

            kwargs = {}
            if isinstance(annotation_type, PauseAnnotation):
                kwargs['node_alias'] = AnnotationAttribute('word',0,a.corpus).alias
                kwargs['path_alias'] = a.path_alias
                where = a.additional_where()
            else:
                kwargs['node_alias'] = AnnotationAttribute(a.type,0,a.corpus).alias
                kwargs['prev_alias'] = a.define_alias
                kwargs['prev_type_alias'] = a.define_type_alias
            anchor_string = prec.format(**kwargs)
        elif a.pos > 0:

            kwargs = {}
            if isinstance(annotation_type, PauseAnnotation):
                kwargs['node_alias'] = AnnotationAttribute('word',0,a.corpus).alias
                kwargs['path_alias'] = a.path_alias
                where = a.additional_where()
            else:
                kwargs['node_alias'] = AnnotationAttribute(a.type,0,a.corpus).alias
                kwargs['foll_alias'] = a.define_alias
                kwargs['foll_type_alias'] = a.define_type_alias
            anchor_string = foll.format(**kwargs)
        if a in filter_annotations:
            statements.append(anchor_string)
            if where:
                wheres.append(where)
        else:
            optional_statements.append(anchor_string)
            if where:
                optional_wheres.append(where)
        defined.add(a.alias)
        if isinstance(annotation_type, PauseAnnotation):
            defined.add(a.path_alias)
        else:
            defined.add(a.type_alias)
    return statements, optional_statements, defined, wheres, optional_wheres

hierarchy_template = '''({contained_alias})-[:contained_by*1..]->({containing_alias})'''

def generate_hierarchical_match(annotation_levels, hierarchy):
    statements = []
    annotation_types = [x.type for x in annotation_levels.keys()]
    for k in sorted(annotation_types):
        if k in hierarchy:
            supertype = hierarchy[k]
            while supertype not in annotation_types:
                if supertype is None:
                    break
                supertype = hierarchy[supertype]
            if supertype is None:
                continue
            sub = AnnotationAttribute(k, 0)
            sup = AnnotationAttribute(supertype, 0)
            statement = hierarchy_template.format(contained_alias = sub.alias,
                                                    containing_alias = sup.alias)
            if statement not in statements:
                statements.append(statement)
    return statements

def generate_type_matches(query, filter_annotations):
    analyzed = defaultdict(set)
    defined = set()
    for c in query._criterion:
        for a in c.attributes:
            if a.annotation.has_subquery:
                continue
            type_token =  'type' if a.label in type_attributes else 'token'
            analyzed[a.annotation].add(type_token)
    for a in query._columns + query._group_by + query._additional_columns:
        if a.annotation.has_subquery:
            continue
        type_token =  'type' if a.label in type_attributes else 'token'
        analyzed[a.annotation].add(type_token)

    matches = []
    optional_matches = []
    for k, v in analyzed.items():
        if 'type' in v:
            statement = type_match_template.format(token_alias = k.alias,
                                        type_alias = k.define_type_alias)
            if k.pos == 0 or k in filter_annotations:
                matches.append(statement)
            else:
                optional_matches.append(statement)
            defined.add(k.type_alias)
    return matches, optional_matches, defined

def generate_additional_withs(query):
    defined = set()
    for c in query._criterion:
        for a in c.attributes:
            if hasattr(a, 'for_with'):
                defined.add(a.for_with())
    for a in query._columns + query._group_by + query._additional_columns:
        if hasattr(a, 'for_with'):
            defined.add(a.for_with())
    return defined

def generate_additional_matches(query):
    matches = []
    for c in query._criterion:
        for a in c.attributes:
            if hasattr(a, 'for_match'):
                matches.append(a.for_match())
    for a in query._columns + query._group_by + query._additional_columns:
        if hasattr(a, 'for_match'):
            matches.append(a.for_match())
    return matches

def generate_withs(query, all_withs):
    statements = [withs_to_string(all_withs)]
    for c in query._criterion:
        for a in c.attributes:
            if a.with_alias not in all_withs:
                statement = a.annotation.subquery(all_withs)
                statements.append(statement)

                all_withs.update(a.with_aliases)
    for a in query._columns + query._group_by + query._additional_columns:
        if a.with_alias not in all_withs:
            statement = a.annotation.subquery(all_withs)
            statements.append(statement)

            all_withs.update(a.with_aliases)
    return '\n'.join(statements)

def withs_to_string(withs):
    return 'WITH ' + ', '.join(withs)

def query_to_cypher(query):
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
        statements,optional_statements, withs, wheres, optional_wheres = generate_token_match(k,v, filter_annotations)
        all_withs.update(withs)
        match_strings.extend(statements)
        optional_match_strings.extend(optional_statements)
        optional_where_strings.extend(optional_wheres)
        where_strings.extend(wheres)

    statements = generate_hierarchical_match(annotation_levels, query.corpus.hierarchy)
    match_strings.extend(statements)

    #statements,optional_statements, withs = generate_type_matches(query, filter_annotations)
    #all_withs.update(withs)
    #match_strings.extend(statements)
    #optional_match_strings.extend(optional_statements)

    kwargs['match'] = 'MATCH ' + ',\n'.join(match_strings)

    if optional_match_strings:
        kwargs['optional_match'] = 'OPTIONAL MATCH ' + ',\n'.join(optional_match_strings)
        if optional_where_strings:
            kwargs['optional_match'] += '\nWHERE ' + ',\n'.join(optional_where_strings)

    kwargs['where'] = criterion_to_where(query._criterion, wheres)

    kwargs['with'] = generate_withs(query, all_withs)


    kwargs['return'] = create_return_statement(query)
    cypher = template.format(**kwargs)
    return cypher

def query_to_params(query):
    params = {}
    for c in query._criterion:
        try:
            if not isinstance(c.value, Attribute):
                params[c.attribute.alias] = c.value
        except AttributeError:
            pass
    return params

def discourse_query(corpus_context, discourse, annotations):
    if annotations is None:
        annotations = ['label']
    template = '''MATCH (discourse_b0:word:{corpus}:{discourse})
WITH min(discourse_b0.begin) as mintime, discourse_b0
WHERE discourse_b0.begin = mintime
WITH discourse_b0
MATCH p = (discourse_b0)-[:precedes*0..]->(:word:{corpus}:{discourse})
WITH COLLECT(p) AS paths, MAX(length(p)) AS maxLength
WITH FILTER(path IN paths
  WHERE length(path)= maxLength) AS longestPath
WITH nodes(head(longestPath)) as np
UNWIND np as wt
MATCH (wt)-[:is_a]->(w:word_type)
RETURN {returns}'''
    extract_template = '''w.{annotation} as {annotation}'''
    extracts = []
    word = corpus_context.word
    for a in annotations:
        extract_string = extract_template.format(annotation = a)
        extracts.append(extract_string)
    query = template.format(discourse = discourse, corpus = corpus_context.corpus_name,
                            returns = ', '.join(extracts))
    return corpus_context.graph.cypher.execute(query)
