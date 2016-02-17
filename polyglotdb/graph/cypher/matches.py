
from ..attributes import AnnotationAttribute


anchor_template = '''({token_alias})-[:is_a]->({type_alias})'''
prec_template = '''({prev_type_alias})<-[:is_a]-({prev_alias})-[:precedes{dist}]->({node_alias})'''
foll_template = '''({node_alias})-[:precedes{dist}]->({foll_alias})-[:is_a]->({foll_type_alias})'''

def generate_match(annotation_type, annotation_list, filter_annotations):
    annotation_list = sorted(annotation_list, key = lambda x: x.pos)
    positions = set(x.pos for x in annotation_list)
    prec_condition = ''
    foll_condition = ''
    defined = set()

    statements = []
    wheres = []
    optional_wheres = []
    current = annotation_list[0].pos
    optional_statements = []
    prec = prec_template
    foll = foll_template
    anchor_string = annotation_type.for_match()
    statements.append(anchor_string)
    defined.update(annotation_type.withs)
    for a in annotation_list:
        where = ''
        if a.pos == 0:
            continue
        elif a.pos < 0:

            kwargs = {}
            if a.pos + 1 in positions:
                kwargs['node_alias'] = AnnotationAttribute(a.type,a.pos+1,a.corpus).alias

                kwargs['dist'] = ''
            else:
                kwargs['node_alias'] = AnnotationAttribute(a.type,0,a.corpus).alias
                if a.pos == -1:
                    kwargs['dist'] = ''
                else:
                    kwargs['dist'] = '*{}'.format(a.pos)
            kwargs['prev_alias'] = a.define_alias
            kwargs['prev_type_alias'] = a.define_type_alias
            anchor_string = prec.format(**kwargs)
        elif a.pos > 0:

            kwargs = {}
            if a.pos - 1 in positions:
                kwargs['node_alias'] = AnnotationAttribute(a.type,a.pos-1,a.corpus).alias

                kwargs['dist'] = ''
            else:
                kwargs['node_alias'] = AnnotationAttribute(a.type,0,a.corpus).alias
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
            optional_statements.append(anchor_string)
            if where:
                optional_wheres.append(where)
        defined.add(a.alias)
        defined.add(a.type_alias)
    return statements, optional_statements, defined, wheres, optional_wheres
