
from collections import defaultdict

from .helper import type_attributes

from .attributes import AnnotationAttribute, PathAnnotation, Attribute

aggregate_template = '''RETURN {aggregates}{additional_columns}{order_by}'''

distinct_template = '''RETURN {columns}{additional_columns}{order_by}'''

set_pause_template = '''SET {alias} :pause
REMOVE {alias}:speech
WITH {alias}
MATCH ({begin_alias})-[:{rel_type}]->({alias})-[:{rel_type}]->({end_alias})
CREATE ({begin_alias})-[:r_pause]->({alias})-[:r_pause]->({end_alias})'''

unset_pause_template = '''SET {alias} :speech
REMOVE {alias}:pause
WITH {alias}
MATCH ({begin_alias})-[r1:r_pause]->({alias})-[r2:r_pause]->({end_alias})
DELETE r1, r2'''

change_label_template = '''SET {alias} {value}
REMOVE {alias}{alt_value}
WITH {alias}
MATCH (a:Anchor)-[:{rel_type}]->({alias})-[:{rel_type}]->(b:Anchor)
CREATE (a:Anchor)-[:{rel_value}]->({alias})-[:{rel_value}]->(b:Anchor)'''

set_label_template = '''SET {alias} {value}
WITH {alias}
MATCH (a:Anchor)-[:{rel_type}]->({alias})-[:{rel_type}]->(b:Anchor)
CREATE (a:Anchor)-[:{rel_value}]->({alias})-[:{rel_value}]->(b:Anchor)'''

remove_label_template = '''REMOVE {alias}{value}'''

set_property_template = '''SET {alias}.{attribute} = {value}'''

anchor_template = '''({begin_alias})-[:{rel_type}]->({node_alias})-[:{rel_type}]->({end_alias})'''

prec_template = '''{path_alias} = ({begin_alias})-[:{rel_type}]->({node_alias})-[:{rel_type}]->({end_alias})-[:r_pause*0..]->({main_begin_alias})'''
foll_template = '''{path_alias} = ({main_end_alias})-[:r_pause*0..]->({begin_alias})-[:{rel_type}]->({node_alias})-[:{rel_type}]->({end_alias})'''

template = '''{match}
{optional_match}
{where}
{with}
{return}'''

def generate_annotation_with(annotation):
    return [annotation.alias, annotation.begin_alias, annotation.end_alias]

def criterion_to_where(criterion):
    properties = []
    for c in criterion:
        properties.append(c.for_cypher())
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
    if query._set or query._set_labels or query._remove_labels:
        for k,v in query._set.items():
            if k == 'pause':
                kwargs = {}
                kwargs['alias'] = query.to_find.alias
                kwargs['begin_alias'] = query.to_find.begin_alias
                kwargs['end_alias'] = query.to_find.end_alias
                if v:
                    kwargs['rel_type'] = query.to_find.rel_type_alias
                    return_statement = set_pause_template.format(**kwargs)
                else:
                    return_statement = unset_pause_template.format(**kwargs)
        return return_statement
        return_statement = ''
        if query._set_labels:
            kwargs = {}
            kwargs['alias'] = query.to_find.alias
            kwargs['value'] = ':' + ':'.join(query._set_labels) #FIXME
            kwargs['alt_value'] = ':' + ':'.join(query._remove_labels) #FIXME
            kwargs['rel_type'] = query.to_find.rel_type_alias
            kwargs['rel_value'] = ':' + ':'.join(map(lambda x: 'r_'+ x,query._set_labels)) #FIXME
            kwargs['alt_rel_value'] = ':' + ':'.join(map(lambda x: 'r_'+ x,query._remove_labels)) #FIXME
            return_statement += set_label_template.format(alias = query.to_find.alias, value = value)
        if query._remove_labels:
            if return_statement:
                return_statement += '\nWITH {alias}\n'.format(alias = query.to_find.alias)
            value = ':' + ':'.join(query._remove_labels) #FIXME
            return_statement += remove_label_template.format(alias = query.to_find.alias, value = value)
        return return_statement
    elif query._aggregate:
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
    kwargs = {}
    kwargs['begin_alias'] = annotation_type.define_begin_alias
    kwargs['end_alias'] = annotation_type.define_end_alias
    kwargs['node_alias'] = annotation_type.define_alias
    kwargs['rel_type'] = annotation_type.rel_type_alias
    anchor_string = anchor_template.format(**kwargs)
    statements.append(anchor_string)
    defined.update(generate_annotation_with(annotation_type))
    current = annotation_list[0].pos
    optional_statements = []
    for a in annotation_list:
        if a.pos == 0:
            continue
        elif a.pos < 0:

            kwargs = {}
            kwargs['begin_alias'] = figure_property(a, 'begin_alias', defined)
            kwargs['main_begin_alias'] = annotation_type.begin_alias
            kwargs['end_alias'] = figure_property(a, 'end_alias', defined)
            kwargs['node_alias'] = a.define_alias
            kwargs['rel_type'] = a.rel_type_alias
            kwargs['path_alias'] = a.path_alias
            anchor_string = prec_template.format(**kwargs)
        elif a.pos > 0:

            kwargs = {}
            kwargs['begin_alias'] = figure_property(a, 'begin_alias', defined)
            kwargs['main_end_alias'] = annotation_type.end_alias
            kwargs['end_alias'] = figure_property(a, 'end_alias', defined)
            kwargs['node_alias'] = a.define_alias
            kwargs['rel_type'] = a.rel_type_alias
            kwargs['path_alias'] = a.path_alias
            anchor_string = foll_template.format(**kwargs)
        if a in filter_annotations:
            statements.append(anchor_string)
        else:
            optional_statements.append(anchor_string)
        defined.update(generate_annotation_with(a))
        defined.add(kwargs['path_alias'])
    return statements, optional_statements, defined

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
            statements.append(hierarchy_template.format(contained_alias = sub.alias,
                                                    containing_alias = sup.alias))
    return statements

type_match_template = '''({token_alias})-[:is_a]->({type_alias})'''

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
                if a.is_type_attribute:
                    statement = a.annotation.type_subquery(all_withs)
                else:
                    statement = a.annotation.times_subquery(all_withs)
                statements.append(statement)

                all_withs.add(a.with_alias)
    for a in query._columns + query._group_by + query._additional_columns:
        if a.with_alias not in all_withs:
            if a.is_type_attribute:
                statement = a.annotation.type_subquery(all_withs)
            else:
                statement = a.annotation.times_subquery(all_withs)
            statements.append(statement)

            all_withs.add(a.with_alias)
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
    where_strings = []

    all_withs = set()

    filter_annotations = set()
    for c in query._criterion:
        for a in c.attributes:
            t = a.base_annotation
            filter_annotations.add(t)

    for k,v in annotation_levels.items():
        if k.has_subquery:
            continue
        statements,optional_statements, withs = generate_token_match(k,v, filter_annotations)
        all_withs.update(withs)
        match_strings.extend(statements)
        optional_match_strings.extend(optional_statements)


    statements = generate_hierarchical_match(annotation_levels, query.corpus.hierarchy)
    match_strings.extend(statements)

    statements,optional_statements, withs = generate_type_matches(query, filter_annotations)
    all_withs.update(withs)
    match_strings.extend(statements)
    optional_match_strings.extend(optional_statements)

    kwargs['match'] = 'MATCH ' + ',\n'.join(match_strings)

    if optional_match_strings:
        kwargs['optional_match'] = 'OPTIONAL MATCH ' + ',\n'.join(optional_match_strings)

    kwargs['where'] = criterion_to_where(query._criterion)

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
    template = '''MATCH (discourse_b0:Anchor:{corpus}:{discourse})
WHERE discourse_b0.time = 0
WITH discourse_b0
MATCH p = (discourse_b0)-[:{word_rel_type}*0..]->()
WITH COLLECT(p) AS paths, MAX(length(p)) AS maxLength
WITH FILTER(path IN paths
  WHERE length(path)= maxLength) AS longestPath
WITH filter(n in nodes(head(longestPath)) WHERE n:{token_node_type}) as np
UNWIND np as wt
MATCH (wt)-[:is_a]->(w:{word_node_type})
RETURN {returns}'''
    extract_template = '''w.{annotation} as {annotation}'''
    extracts = []
    word = corpus_context.word
    for a in annotations:
        extract_string = extract_template.format(annotation = a)
        extracts.append(extract_string)
    query = template.format(discourse = discourse, corpus = corpus_context.corpus_name,
                            word_rel_type = word.rel_type_alias,
                            token_node_type = word.type,
                            word_node_type = word.type + '_type',
                            returns = ', '.join(extracts))
    return corpus_context.graph.cypher.execute(query)
