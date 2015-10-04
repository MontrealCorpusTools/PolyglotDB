

match_template = '''MATCH {}
{}
WITH {}'''


#contained_by_template = '''({containing_begin})-[{relationship_type_alias}]->({containing_end}),
#p = shortestPath(({end_node_alias})-[:{annotation_type}*0..5]->({containing_end})),
#p2 = shortestPath(({containing_begin})-[:{annotation_type}*0..5]->({begin_node_alias}))
#'''
contained_by_template = '''({begin_node_alias})<-[:{annotation_type}*0..10]-({containing_begin})-[{relationship_type_alias}]->({containing_end})<-[:{annotation_type}*0..10]-({end_node_alias})'''

prec_template = '''({b_name})-[{name}]->'''
foll_template = '''-[{name}]->({e_name})'''

contains_template = '''({begin_node_alias})-[{relationship_type_alias}*0..30]->({end_node_alias})'''

left_align_template = '''()<-[:{align_type}]-({begin_node_alias})'''
right_align_template = '''()-[:{align_type}]->({end_node_alias})'''

def create_annotation_set(query):
    annotation_set = set()
    for c in query._criterion:
        annotation_set.update(c.annotations)
    return annotation_set


def generate_additional_where(query, criterion_ignored):
    properties = []
    for c in query._criterion:
        if any(x.type != query.to_find.type for x in c.annotations):
            criterion_ignored.append(c)
            continue
        properties.append(c.for_cypher())
    if properties:
        additional_where = '\nAND ' + '\nAND '.join(properties)
    else:
        additional_where = ''
    return additional_where, criterion_ignored

def generate_preceding_following(query, annotation_set):
    to_add = sorted((x for x in annotation_set if x.type == query.to_find.type), key = lambda x: x.pos)
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
                    b_name = query.to_find.begin_template.format(query.to_find.type,current)
                    prec_condition += prec_template.format(name = ':{}'.format(query.to_find.type),
                                                        b_name = b_name)
                    current += 1

                prec_condition += prec_template.format(name = a.rel_alias,
                                                    b_name = a.begin_alias)
            elif a.pos > 0:
                while a.pos != current:
                    e_name = query.to_find.end_template.format(query.to_find.type, current)
                    foll_condition += foll_template.format(name = ':{}'.format(query.to_find.type),
                                                        e_name = e_name)
                    current += 1
                foll_condition += foll_template.format(name = a.rel_alias,
                                                        e_name = a.end_alias)
            current += 1
            with_properties.extend(generate_relationship_with(a))
    return prec_condition, foll_condition, with_properties

def generate_contained_by_subqueries(query, criterion_ignored, withs, allowed_types):
    contained_by_withs = []
    matches = []

    for a in query._contained_by_annotations:

        match_string = contained_by_template.format(annotation_type = query.to_find.type,
                                            relationship_type_alias = a.rel_alias,
                                            containing_begin = a.begin_alias,
                                            containing_end = a.end_alias,
                                            begin_node_alias = query.to_find.begin_alias,
                                            end_node_alias = query.to_find.end_alias)
        matches.append(match_string)
        contained_by_withs.extend(generate_relationship_with(a))
    criterion_still_ignored = []
    properties = []
    for c in criterion_ignored:
        if any(x.type not in allowed_types for x in c.annotations):
            criterion_still_ignored.append(c)
            continue
        properties.append(c.for_cypher())
    if properties:
        where_string = 'WHERE ' + '\nAND'.join(properties)
    else:
        where_string = ''
    withs.update(contained_by_withs)
    withs_string = ', '.join(withs)
    if matches:
        match_string = match_template.format(',\n'.join(matches),
                                                        where_string,
                                                        withs_string)
    else:
        match_string = ''
    return match_string, withs, criterion_still_ignored

def generate_contains_subqueries(query, criterion_ignored, withs, allowed_types):
    matches = []
    contains_withs = []
    for a in query._contains_annotations:
        match_string = contains_template.format(relationship_type_alias = a.rel_alias,
                            begin_node_alias = query.to_find.begin_alias,
                            end_node_alias = query.to_find.end_alias)
        matches.append(match_string)
        contains_withs.extend([a.alias])
    criterion_still_ignored = []
    properties = []
    for c in criterion_ignored:
        if any(x.type not in allowed_types for x in c.annotations):
            criterion_still_ignored.append(c)
            continue
        properties.append(c.for_cypher())
    if properties:
        where_string = 'WHERE ' + '\nAND'.join(properties)
    else:
        where_string = ''
    withs.update(contains_withs)
    withs_string = ', '.join(withs)
    if matches:
        match_string = match_template.format(',\n'.join(matches),
                                                        where_string,
                                                        withs_string)
    else:
        match_string = ''
    return match_string, withs, criterion_still_ignored


def generate_relationship_with(relationship):
    return [relationship.alias, relationship.begin_alias, relationship.end_alias]

def query_to_cypher(query):
    kwargs = {'corpus_name': query.graph.corpus_name,
                'preceding_condition': '',
                'relationship_type_alias':query.to_find.rel_alias,
                'begin_node_alias': query.to_find.begin_alias,
                'end_node_alias': query.to_find.end_alias,
                'following_condition': '',
                'additional_match': '',
                'with': '',
                'additional_where': '',
                'additional_columns': '',
                'order_by': ''}
    if query._aggregate:
        template = '''MATCH {preceding_condition}({begin_node_alias})-[{relationship_type_alias}]->({end_node_alias}){following_condition}
                WHERE {begin_node_alias}.corpus = '{corpus_name}'
                {additional_where}
                WITH {with}
                {additional_match}
                RETURN {aggregates}{additional_columns}{order_by}'''
        properties = []
        for g in query._group_by:
            properties.append(g.aliased_for_output())
        if len(query._order_by) == 0 and len(query._group_by) > 0:
            query._order_by.append((query._group_by[0], False))
        for a in query._aggregate:
            properties.append(a.for_cypher())
        kwargs['aggregates'] = ', '.join(properties)

    else:
        template = '''MATCH {preceding_condition}({begin_node_alias})-[{relationship_type_alias}]->({end_node_alias}){following_condition}
                WHERE {begin_node_alias}.corpus = '{corpus_name}'
                {additional_where}
                WITH {with}
                {additional_match}
                RETURN DISTINCT {columns}{additional_columns}{order_by}'''
        kwargs['columns'] = ''
        properties = []
        for c in query._columns:
            properties.append(c.aliased_for_output())
        if properties:
            kwargs['columns'] = ', '.join(properties)
        kwargs['relationship_alias'] = query.to_find.alias

    withs = set(generate_relationship_with(query.to_find))
    annotation_set = create_annotation_set(query)

    criterion_ignored = []
    where, criterion_ignored = generate_additional_where(query, criterion_ignored)
    kwargs['additional_where'] += where

    (kwargs['preceding_condition'],
        kwargs['following_condition'],
        precfoll_with) = generate_preceding_following(query, annotation_set)

    withs.update(precfoll_with)
    kwargs['with'] = ', '.join(withs)

    other_to_finds = [x for x in annotation_set if x.type != query.to_find.type]
    for o in other_to_finds:
        if o.pos == 0:
            if o.type in [x.type for x in query._contained_by_annotations]:
                continue
            if o.type in [x.type for x in query._contains_annotations]:
                continue
            query._contained_by_annotations.add(o) # FIXME

    allowed_types = [query.to_find.type]+[x.type for x in query._contained_by_annotations]

    match_string, withs, criterion_ignored = generate_contained_by_subqueries(query, criterion_ignored, withs, allowed_types)

    if match_string:
        kwargs['additional_match'] += '\n' + match_string

    matches = []
    allowed_types += [x.type for x in query._contains_annotations]

    match_string, withs, criterion_ignored = generate_contains_subqueries(query, criterion_ignored, withs, allowed_types)

    if match_string:
        kwargs['additional_match'] += '\n' + match_string


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
    cypher = template.format(**kwargs)
    return cypher
