
from collections import defaultdict

from .helper import type_attributes

from .attributes import AnnotationAttribute, Attribute

aggregate_template = '''RETURN {aggregates}{additional_columns}{order_by}'''

distinct_template = '''RETURN {columns}{additional_columns}{order_by}'''

anchor_template = '''({begin_alias})-[:{rel_type}]->({node_alias})-[:{rel_type}]->({end_alias})'''

template = '''{match}
{where}
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


def generate_token_match(annotation_type, annotation_list):
    if all(x.pos != 0 for x in annotation_list):
        annotation_list.add(AnnotationAttribute(annotation_type, 0))
    annotation_list = sorted(annotation_list, key = lambda x: x.pos)
    prec_condition = ''
    foll_condition = ''
    defined = set()

    current = annotation_list[0].pos
    anchor_string = '()'
    statements = []
    for a in annotation_list:
        if a.pos == 0:
            kwargs = {}
            kwargs['begin_alias'] = figure_property(a, 'begin_alias', defined)
            kwargs['end_alias'] = figure_property(a, 'end_alias', defined)
            kwargs['node_alias'] = a.define_alias
            kwargs['rel_type'] = a.rel_type_alias
            anchor_string = anchor_template.format(**kwargs)
        elif a.pos < 0:
            while a.pos != current:
                kwargs = {}
                temp_a = AnnotationAttribute(annotation_type, current)
                kwargs['node_alias'] = temp_a.define_alias
                kwargs['begin_alias'] = temp_a.define_begin_alias
                kwargs['rel_type'] = temp_a.rel_type_alias
                prec_condition += prec_template.format(**kwargs)
                current += 1

            kwargs = {}
            kwargs['begin_alias'] = figure_property(a, 'begin_alias', defined)
            kwargs['end_alias'] = figure_property(a, 'end_alias', defined)
            kwargs['node_alias'] = a.define_alias
            kwargs['rel_type'] = a.rel_type_alias
            anchor_string = anchor_template.format(**kwargs)
        elif a.pos > 0:
            while a.pos != current:
                kwargs = {}
                temp_a = AnnotationAttribute(annotation_type, current)
                kwargs['node_alias'] = temp_a.define_alias
                kwargs['end_alias'] = temp_a.define_end_alias
                kwargs['rel_type'] = temp_a.rel_type_alias
                foll_condition += foll_template.format(**kwargs)
                current += 1

            kwargs = {}
            kwargs['begin_alias'] = figure_property(a, 'begin_alias', defined)
            kwargs['end_alias'] = figure_property(a, 'end_alias', defined)
            kwargs['node_alias'] = a.define_alias
            kwargs['rel_type'] = a.rel_type_alias
            anchor_string = anchor_template.format(**kwargs)
        statements.append(anchor_string)
        current += 1
        defined.update(generate_annotation_with(a))

    return statements

hierarchy_template = '''({contained_alias})-[:contained_by*1..]->({containing_alias})'''

def generate_hierarchical_match(annotation_levels, hierarchy):
    statements = []
    for k in sorted(annotation_levels.keys()):
        if k in hierarchy:
            supertype = hierarchy[k]
            while supertype not in annotation_levels.keys():
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

def generate_type_matches(query):
    analyzed = defaultdict(set)
    for c in query._criterion:
        for a in c.attributes:
            type_token =  'type' if a.label in type_attributes else 'token'
            analyzed[a.annotation].add(type_token)
    for a in query._columns + query._group_by + query._additional_columns:
        type_token =  'type' if a.label in type_attributes else 'token'
        analyzed[a.annotation].add(type_token)

    matches = []
    for k, v in analyzed.items():
        if 'type' in v:
            matches.append(type_match_template.format(token_alias = k.alias,
                                        type_alias = k.define_type_alias))
    return matches

def query_to_cypher(query):
    kwargs = {'match': '',
            'where': '',
            'return':''}
    annotation_levels = query.annotation_levels()

    match_strings = []
    where_strings = []

    for k,v in annotation_levels.items():
        match_strings.extend(generate_token_match(k,v))
    match_strings.extend(generate_hierarchical_match(annotation_levels, query.corpus.hierarchy))

    match_strings.extend(generate_type_matches(query))

    kwargs['match'] = 'MATCH ' + ',\n'.join(match_strings)

    kwargs['where'] = criterion_to_where(query._criterion)

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
