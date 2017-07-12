from ..attributes import AnnotationAttribute, PauseAnnotation, PausePathAnnotation

anchor_template = '''({token_alias})-[:is_a]->({type_alias})'''
prec_template = '''({prev_type_alias})<-[:is_a]-({prev_alias})-[:precedes{dist}]->({node_alias})'''
foll_template = '''({node_alias})-[:precedes{dist}]->({foll_alias})-[:is_a]->({foll_type_alias})'''

prec_pause_template = '''{path_alias} = (:speech:word)-[:precedes_pause*0..]->({node_alias})'''
foll_pause_template = '''{path_alias} = ({node_alias})-[:precedes_pause*0..]->(:speech:word)'''


def generate_match(query, annotation_type, annotation_list, filter_annotations):
    """ 
    
    Parameters
    ----------
    query : :class: `~polyglotdb.graph.GraphQuery`
        the query object
    annotation_type : str
        the type of annotation
    annotation_list : list
        a list of annotations
    filter_annotations : list 
        a list of filters

    Returns
    -------
    statements : list
        a list of 'match' cypher strings
    optional_statements: list
        list of 'match' cypher strings that aren't filters
    defined: set
       path_alias, path_type_alias, and subannotation_alias
    wheres: list
        list of cypher strings and None's
    optional_wheres: list
        list of cypher strings and None's
        only if annotations aren't filters

    """
    annotation_list = sorted(annotation_list, key=lambda x: x.pos)
    positions = set(x.pos for x in annotation_list)
    prec_condition = ''
    foll_condition = ''
    defined = set()

    statements = []
    wheres = []
    if isinstance(annotation_type, PauseAnnotation):
        prec = prec_pause_template
        foll = foll_pause_template
    else:
        prec = prec_template
        foll = foll_template
        anchor_string = annotation_type.for_match()
        defined.update(annotation_type.withs)
        statements.append(anchor_string)
    optionals = {}
    for a in annotation_list:
        where = ''
        if a.pos == 0:
            if isinstance(annotation_type, PauseAnnotation):
                anchor_string = annotation_type.for_match()

                statements.append(anchor_string)
                defined.update(annotation_type.withs)
            continue
        elif a.pos < 0:

            kwargs = {}
            if isinstance(annotation_type, PauseAnnotation):
                if query.to_find.type == query.corpus.word_name:
                    kwargs['node_alias'] = AnnotationAttribute(query.corpus.word_name, 0, a.corpus).alias  # FIXME?
                else:
                    anno = query.to_find
                    while True:
                        t = query.corpus.hierarchy[anno.type]
                        anno = getattr(anno, t)
                        if t == query.corpus.word_name:
                            break
                    kwargs['node_alias'] = anno.alias
                kwargs['path_alias'] = a.path_alias
                where = a.additional_where()
            else:
                if a.pos + 1 in positions:
                    if query.to_find.type != a.type:
                        anno = query.to_find
                        while True:
                            t = query.corpus.hierarchy[anno.type]
                            anno = getattr(anno, t)
                            if t == a.type:
                                break
                        anno.pos = a.pos + 1
                        kwargs['node_alias'] = anno.alias
                    else:
                        kwargs['node_alias'] = AnnotationAttribute(a.type, a.pos + 1, a.corpus).alias

                    kwargs['dist'] = ''
                else:
                    if query.to_find.type != a.type:
                        anno = query.to_find
                        while True:
                            t = query.corpus.hierarchy[anno.type]
                            anno = getattr(anno, t)
                            if t == a.type:
                                break

                    else:
                        kwargs['node_alias'] = AnnotationAttribute(a.type, 0, a.corpus).alias
                    if a.pos == -1:
                        kwargs['dist'] = ''
                    else:
                        kwargs['dist'] = '*{}'.format(a.pos)
                kwargs['prev_alias'] = a.define_alias
                kwargs['prev_type_alias'] = a.define_type_alias
            anchor_string = prec.format(**kwargs)
        elif a.pos > 0:

            kwargs = {}
            if isinstance(annotation_type, PauseAnnotation):
                if query.to_find.type == query.corpus.word_name:
                    kwargs['node_alias'] = AnnotationAttribute(query.corpus.word_name, 0, a.corpus).alias  # FIXME?
                else:
                    anno = query.to_find
                    while True:
                        t = query.corpus.hierarchy[anno.type]
                        anno = getattr(anno, t)
                        if t == query.corpus.word_name:
                            break
                    kwargs['node_alias'] = anno.alias
                kwargs['path_alias'] = a.path_alias
                where = a.additional_where()
            else:
                if a.pos - 1 in positions:
                    if query.to_find.type != a.type:
                        anno = query.to_find
                        while True:
                            t = query.corpus.hierarchy[anno.type]
                            anno = getattr(anno, t)
                            if t == a.type:
                                break
                        anno.pos = a.pos - 1
                        kwargs['node_alias'] = anno.alias
                    else:
                        kwargs['node_alias'] = AnnotationAttribute(a.type, a.pos - 1, a.corpus).alias

                    kwargs['dist'] = ''
                else:
                    if query.to_find.type != a.type:

                        anno = query.to_find
                        while True:
                            t = query.corpus.hierarchy[anno.type]
                            anno = getattr(anno, t)
                            if t == a.type:
                                break
                        kwargs['node_alias'] = anno.alias
                    else:
                        kwargs['node_alias'] = AnnotationAttribute(a.type, 0, a.corpus).alias
                    if a.pos == 1:
                        kwargs['dist'] = ''
                    else:
                        kwargs['dist'] = '*{}'.format(a.pos)

                kwargs['foll_alias'] = a.define_alias
                kwargs['foll_type_alias'] = a.define_type_alias
            anchor_string = foll.format(**kwargs)
        if a in filter_annotations:
            statements.append(anchor_string)
            if where:
                wheres.append(where)
        else:
            if a.type not in optionals:
                optionals[a.type] = []
            optionals[a.type].append((anchor_string, where))
        if isinstance(annotation_type, PauseAnnotation):
            defined.add(a.path_alias)
        else:
            defined.add(a.alias)
            defined.add(a.type_alias)
    optional_wheres = []
    optional_statements = []
    for k, v in optionals.items():
        if len(v) == 1:
            optional_statements.append(v[0][0])
            optional_wheres.append(v[0][1])
        else:
            optional_statements.append(',\n'.join(x[0] for x in v))
            w = [x[1] for x in v if x[1]]
            if w:
                optional_wheres.append('\nAND '.join(w))
            else:
                optional_wheres.append('')

    return statements, optional_statements, defined, wheres, optional_wheres
