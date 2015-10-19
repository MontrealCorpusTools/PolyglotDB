

match_template = '''MATCH {}
{}
WITH {}'''

is_a_template = '''({node_alias})-[:is_a]->({node_type_alias})'''

anchor_template = '''({begin_alias})-[:{rel_type}]->({node_alias})-[:{rel_type}]->({end_alias})'''

#contained_by_template = '''({containing_begin})-[{relationship_type_alias}]->({containing_end}),
#p = shortestPath(({end_node_alias})-[:{annotation_type}*0..5]->({containing_end})),
#p2 = shortestPath(({containing_begin})-[:{annotation_type}*0..5]->({begin_node_alias}))
#'''
contained_by_template = '''({begin_node_alias})<-[:{annotation_type}*0..30]-({containing_begin})-[:{rel_type}]->({containing_alias})-[:{rel_type}]->({containing_end})<-[:{annotation_type}*0..30]-({end_node_alias})'''

id_contained_by_template = '''({containing_alias})'''
id_contained_by_where = '''{containing_alias}.id = {alias}.{containing_type}'''

time_contained_by_match_template = '''({containing_begin})-[:{rel_type}]->({containing_alias})-[:{rel_type}]->({containing_end})'''
time_contained_by_where_template = '''{containing_begin}.time <= {begin_node_alias}.time
AND {containing_end}.time >= {end_node_alias}.time'''

prec_template = '''({begin_alias})-[:{rel_type}]->({node_alias})-[:{rel_type}]->'''
foll_template = '''-[:{rel_type}]->({node_alias})-[:{rel_type}]->({end_alias})'''

contains_template = '''{alias} = ({begin_node_alias})-[:{relationship_type_alias}*0..30]->({end_node_alias})'''


left_align_template = '''()<-[:{align_type}]-({begin_node_alias})'''
right_align_template = '''()-[:{align_type}]->({end_node_alias})'''

def generate_preceding_following(query, withs):
    to_add = sorted((x for x in query.annotation_set if x.type == query.to_find.type), key = lambda x: x.pos)
    prec_condition = ''
    foll_condition = ''
    with_properties = []
    if to_add:
        current = to_add[0].pos
        for a in to_add:
            if a.pos == 0:
                current += 1
                continue
            if a.pos < 0:
                while a.pos != current:
                    kwargs = {}
                    temp_a = AnnotationAttribute(query.to_find.type, current)
                    kwargs['node_alias'] = figure_property(temp_a, 'alias', withs)
                    kwargs['begin_alias'] = figure_property(temp_a, 'begin_alias', withs)
                    kwargs['rel_type'] = temp_a.rel_type_alias
                    prec_condition += prec_template.format(**kwargs)
                    current += 1

                kwargs = {}
                kwargs['node_alias'] = figure_property(a, 'alias', withs)
                kwargs['begin_alias'] = figure_property(a, 'begin_alias', withs)
                kwargs['rel_type'] = a.rel_type_alias
                prec_condition += prec_template.format(**kwargs)
            elif a.pos > 0:
                while a.pos != current:
                    kwargs = {}
                    temp_a = AnnotationAttribute(query.to_find.type, current)
                    kwargs['node_alias'] = figure_property(temp_a, 'alias', withs)
                    kwargs['end_alias'] = figure_property(temp_a, 'end_alias', withs)
                    kwargs['rel_type'] = temp_a.rel_type_alias
                    foll_condition += foll_template.format(**kwargs)
                    current += 1

                kwargs = {}
                kwargs['node_alias'] = figure_property(a, 'alias', withs)
                kwargs['end_alias'] = figure_property(a, 'end_alias', withs)
                kwargs['rel_type'] = a.rel_type_alias
                foll_condition += foll_template.format(**kwargs)

            current += 1
            withs.update(generate_annotation_with(a))

    kwargs = {}
    kwargs['begin_alias'] = figure_property(query.to_find, 'begin_alias', withs)
    kwargs['end_alias'] = figure_property(query.to_find, 'end_alias', withs)
    kwargs['node_alias'] = figure_property(query.to_find, 'alias', withs)
    kwargs['rel_type'] = query.to_find.rel_type_alias
    anchor_string = anchor_template.format(**kwargs)

    anchor_queries = query.anchor_subqueries()
    criterion = []
    withs.update(generate_annotation_with(query.to_find))
    for k,v in anchor_queries.items():
        criterion.extend(v)
        withs.update(generate_annotation_with(k))
    withs_string = ', '.join(withs)
    where_string = criterion_to_where(criterion)
    statement = match_template.format(prec_condition+anchor_string+foll_condition, where_string, withs_string)
    return statement, withs

def generate_contained_by_subqueries(query, withs):
    contained_by_withs = []
    matches = []
    properties = []

    #query.is_timed = False
    for a in query._contained_by_annotations:
        if False and query.to_find.type in query.corpus.hierarchy and \
            query.corpus.hierarchy[query.to_find.type] == a.type:
            kwargs = {}
            kwargs['begin_alias'] = figure_property(a, 'begin_alias', withs)
            kwargs['end_alias'] = figure_property(a, 'end_alias', withs)
            kwargs['node_alias'] = figure_property(a, 'alias', withs)
            kwargs['rel_type'] = a.rel_type_alias
            match_string = anchor_template.format(**kwargs)
            kwargs = {}
            kwargs['containing_alias'] = a.alias
            kwargs['containing_type'] = a.type
            kwargs['alias'] = query.to_find.alias
            properties.append(id_contained_by_where.format(**kwargs))
        elif False and query.is_timed:
            match_string = time_contained_by_match_template.format(
                                containing_alias = figure_property(a, 'alias', withs),
                                containing_begin = figure_property(a, 'begin_alias', withs),
                                containing_end = figure_property(a, 'end_alias', withs),
                                rel_type = a.rel_type_alias)
            properties.append(time_contained_by_where_template.format(
                                    containing_begin = a.begin_alias,
                                    containing_end = a.end_alias,
                                    begin_node_alias = query.to_find.begin_alias,
                                    end_node_alias = query.to_find.end_alias))
        else:
            kwargs = {}
            kwargs['containing_begin'] = figure_property(a, 'begin_alias', withs)
            kwargs['containing_end'] = figure_property(a, 'end_alias', withs)
            kwargs['containing_alias'] = figure_property(a, 'alias', withs)
            kwargs['annotation_type'] = query.to_find.rel_type_alias
            kwargs['begin_node_alias'] = figure_property(query.to_find, 'begin_alias', withs)
            kwargs['end_node_alias'] = figure_property(query.to_find, 'end_alias', withs)
            kwargs['rel_type'] = a.rel_type_alias
            match_string = contained_by_template.format(**kwargs)
        matches.append(match_string)
        contained_by_withs.extend(generate_annotation_with(a))
    withs.update(contained_by_withs)
    withs_string = ', '.join(withs)
    for x in query._criterion:
        try:
            if x.attribute.annotation in query._contained_by_annotations:
                properties.append(x.for_cypher())
        except AttributeError:
            if x.first in query._contained_by_annotations or \
                x.second in query._contained_by_annotations:
                properties.append(x.for_cypher())

    where_string = ''
    if properties:
        where_string = 'WHERE ' + ' AND '.join(properties)
    if matches:
        match_string = match_template.format(',\n'.join(matches),
                                                        where_string,
                                                        withs_string)
    else:
        match_string = ''
    return match_string, withs

def generate_contains_subqueries(query, withs):
    matches = []
    contains_withs = []
    for a in query._contains_annotations:
        match_string = contains_template.format(alias = a.alias,
                            relationship_type_alias = a.rel_type_alias,
                            begin_node_alias = figure_property(query.to_find, 'begin_alias', withs),
                            end_node_alias = figure_property(query.to_find, 'end_alias', withs))
        matches.append(match_string)
        contains_withs.extend([a.alias])
    withs.update(contains_withs)
    withs_string = ', '.join(withs)
    properties = []
    for x in query._criterion:
        try:
            if x.attribute.annotation in query._contains_annotations:
                properties.append(x.for_cypher())
        except AttributeError:
            if x.first in query._contains_annotations or \
                x.second in query._contains_annotations:
                properties.append(x.for_cypher())
    where_string = ''
    if properties:
        where_string = 'WHERE ' + 'AND '.join(properties)
    if matches:
        match_string = match_template.format(',\n'.join(matches),
                                                        where_string,
                                                        withs_string)
    else:
        match_string = ''
    return match_string, withs


def generate_annotation_with(annotation):
    return [annotation.alias, annotation.begin_alias, annotation.end_alias]

def criterion_to_where(criterion):
    properties = []
    for c in criterion:
        properties.append(c.for_cypher())
    where_string = ''
    if properties:
        where_string += 'WHERE ' + 'AND '.join(properties)
    return where_string

def format_property_subquery(annotation, criterion, withs):
    node_pattern = '''({})'''
    node_string = node_pattern.format(annotation.define_type_alias)
    where_string = criterion_to_where(criterion)
    withs.add(annotation.type_alias)
    with_string = ', '.join(withs)

    return match_template.format(node_string, where_string, with_string), withs

def figure_property(annotation, property_string, withs):
    if getattr(annotation, property_string) in withs:
        return getattr(annotation, property_string)
    else:
        return getattr(annotation, 'define_'+property_string)

    return match_template.format(anchor_string, where_string, with_string), withs

def create_relationship_subqueries(query, withs):
    prec_foll_statement, withs = generate_preceding_following(query, withs)

    contained_by_statement, withs = generate_contained_by_subqueries(query, withs)

    contains_statement, withs = generate_contains_subqueries(query, withs)

    return '\n'.join([prec_foll_statement, contained_by_statement, contains_statement]), withs

aggregate_template = '''RETURN {aggregates}{additional_columns}{order_by}'''

distinct_template = '''RETURN {columns}{additional_columns}{order_by}'''

def create_return_statement(query):
    kwargs = {'order_by': '', 'additional_columns':''}
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
        if c[0] not in set(query._additional_columns) and \
                c[0] not in set(query._group_by):
            query._additional_columns.append(c[0])
        element = c[0].output_alias
        if c[1]:
            element += ' DESC'
        properties.append(element)

    if properties:
        kwargs['order_by'] += '\nORDER BY ' + ', '.join(properties)

    properties = []
    for c in query._additional_columns:
        properties.append(c.aliased_for_output())
    if properties:
        kwargs['additional_columns'] += ', ' + ', '.join(properties)
    return template.format(**kwargs)

def generate_isa(annotation, withs, token_criterion = None):
    kwargs = {'node_alias':figure_property(annotation, 'alias', withs),
            'node_type_alias': figure_property(annotation, 'type_alias', withs)}
    isa_string = is_a_template.format(**kwargs)
    withs.update([annotation.alias,annotation.type_alias])
    withs_string = ', '.join(withs)
    where_string = ''
    if token_criterion is not None:
        where_string = criterion_to_where(token_criterion)
    statement = match_template.format(isa_string, where_string, withs_string)

    return statement, withs

def query_to_cypher(query):
    kwargs = {'property_queries': '',
            'anchor_queries': '',
            'type_fallback':''}
    template = '''{property_queries}
    {anchor_queries}
    {relationship_queries}
    {type_fallback}
    {return_statement}'''
    type_property_queries = query.type_property_subqueries()
    token_property_queries = query.token_property_subqueries()
    anchor_queries = query.anchor_subqueries()
    withs = set()
    statements = []
    for k, v in type_property_queries.items():
        s, withs = format_property_subquery(k, v, withs)
        if k in token_property_queries:
            criterion = token_property_queries[k]
        else:
            criterion = None
        isa, withs = generate_isa(k, withs, criterion)
        statements.append('\n'.join([s,isa]))
    if statements:
        kwargs['property_queries'] = '\n'.join(statements)


    kwargs['relationship_queries'], withs = create_relationship_subqueries(query, withs)
    if query.to_find.type_alias not in withs:
        isa, withs = generate_isa(query.to_find, withs)
        kwargs['type_fallback'] = isa
    kwargs['return_statement'] = create_return_statement(query)
    cypher = template.format(**kwargs)
    return cypher

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
