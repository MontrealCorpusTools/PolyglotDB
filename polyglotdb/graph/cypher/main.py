
from collections import defaultdict

from ..helper import type_attributes, key_for_cypher, value_for_cypher

from ..attributes import AnnotationAttribute, PathAnnotation, Attribute, PathAttribute, PauseAnnotation

from .matches import generate_match

from .withs import generate_withs

from .wheres import generate_wheres

from .returns import generate_return

template = '''{match}
{where}
{optional_match}
{with}
{return}'''

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
        statements,optional_statements, withs, wheres, optional_wheres = generate_match(k,v, filter_annotations)
        all_withs.update(withs)
        match_strings.extend(statements)
        optional_match_strings.extend(optional_statements)
        optional_where_strings.extend(optional_wheres)
        where_strings.extend(wheres)

    #statements = generate_hierarchical_match(annotation_levels, query.corpus.hierarchy)
    #match_strings.extend(statements)

    kwargs['match'] = 'MATCH ' + ',\n'.join(match_strings)

    if optional_match_strings:
        kwargs['optional_match'] = 'OPTIONAL MATCH ' + ',\n'.join(optional_match_strings)
        if optional_where_strings:
            kwargs['optional_match'] += '\nWHERE ' + ',\n'.join(optional_where_strings)

    kwargs['where'] = generate_wheres(query._criterion, wheres)

    kwargs['with'] = generate_withs(query, all_withs)


    kwargs['return'] = generate_return(query)
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
    type_extract_template = '''w.{annotation} as {annotation}'''
    token_extract_template = '''wt.{annotation} as {annotation}'''
    extracts = []
    word = corpus_context.word
    for a in annotations:
        if a in type_attributes:
            extract_string = type_extract_template.format(annotation = a)
        else:
            extract_string = token_extract_template.format(annotation = a)
        extracts.append(extract_string)
    query = template.format(discourse = discourse, corpus = corpus_context.corpus_name,
                            returns = ', '.join(extracts))
    return corpus_context.graph.cypher.execute(query)
