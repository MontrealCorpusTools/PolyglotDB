


from annograph.helper import align_phones, get_or_create

from annograph.sql.config import session_scope

from annograph.sql.db import (Base, Discourse, Node, Edge, generate_edge_class, AnnotationType, Annotation,
                            AnnotationFrequencies, AnnotationAttributes, AnnotationSubarcs)

def add_discourse(corpus, data):
    """
    Add a discourse to the corpus.

    In general, this function should not be called, as helper functions
    should exist to facilitate adding data to the corpus.

    Parameters
    ----------
    data : DiscourseData
        Data associated with the discourse
    """
    with session_scope() as session:
        new_discourse = Discourse(discourse_label=data.name)

        session.add(new_discourse)
        session.flush()
        nodes = list()
        begin_node = Node(time = 0, discourse = new_discourse)
        session.add(begin_node)
        pts = list()
        base_ind_to_node = dict()
        base_levels = data.base_levels
        for b in base_levels:
            base_ind_to_node[b] = dict()
            pt = get_or_create(session,
                                AnnotationType,
                                type_label = b)
            pts.append(pt)
        nodes.append(begin_node)
        for i, level in enumerate(data.process_order):
            anno_type = get_or_create(session,
                                AnnotationType,
                                type_label = level)
            for d in data[level]:
                annotation = get_or_create(session, Annotation, annotation_label = d.label)

                print(i, level)
                if i == 0: #Anchor level, should have all base levels in it
                    begin_node = nodes[-1]

                    to_align = list()
                    endpoints = list()
                    print(d)
                    for b in base_levels:
                        begin, end = d[b]
                        endpoints.append(end)
                        base = data[b][begin:end]
                        to_align.append(base)

                    if len(to_align) > 1:
                        aligned = list(align_phones(*to_align))
                    else:
                        aligned = to_align
                    first_aligned = aligned.pop(0)
                    for j, first in enumerate(first_aligned):
                        time = None
                        if first != '-' and 'end' in first:
                            time = first.end
                        else:
                            for second in aligned:
                                s = second[j]
                                if s != '-' and 'end' in s:
                                    time = s.end
                        node = Node(time = time, discourse = new_discourse)
                        session.add(node)
                        nodes.append(node)
                        session.flush()
                        first_begin_node = -2
                        second_begin_nodes = [-2 for k in aligned]
                        if first != '-':
                            first_annotation = get_or_create(session,
                                                            Annotation,
                                                            annotation_label = first.label)
                            for k in range(j-1, -1, -1):
                                if first_aligned[k] != '-':
                                    break
                                first_begin_node -= 1
                            edge = Edge(annotation = first_annotation, type = pts[0],
                                    source_node = nodes[first_begin_node],
                                    target_node = node)
                            session.add(edge)
                        for k, second in enumerate(aligned):
                            s = second[j]
                            if s != '-':
                                second_annotation = get_or_create(session,
                                                            Annotation,
                                                            annotation_label = s.label)
                                for m in range(j-1, -1, -1):
                                    if second[m] != '-':
                                        break
                                    second_begin_nodes[k] -= 1
                                edge = Edge(annotation = second_annotation, type = pts[k+1],
                                        source_node = nodes[second_begin_nodes[k]],
                                        target_node = node)
                                session.add(edge)
                            session.flush()
                    for ind, b in enumerate(base_levels):
                        base_ind_to_node[b][endpoints[ind]] = nodes[-1]
                    end_node = nodes[-1]
                else:
                    for b in base_levels:
                        if b in d.references:

                            begin, end = d[b]
                            if begin not in base_ind_to_node[b]:
                                n = nodes[0]
                                for ind in range(begin+1):
                                    for e in n.source_edges:
                                        if str(e.type) == b:
                                            n = e.target_node
                                base_ind_to_node[b][begin] = n
                            begin_node = base_ind_to_node[b][begin]
                            if end not in base_ind_to_node[b]:
                                n = nodes[0]
                                for ind in range(end):
                                    for e in n.source_edges:
                                        if str(e.type) == b:
                                            n = e.target_node
                                base_ind_to_node[b][end] = n
                            end_node = base_ind_to_node[b][end]
                edge = generate_edge_class(base_levels)(annotation = annotation,
                        type = anno_type,
                        source_node = begin_node,
                        target_node = end_node)
                session.add(edge)
                session.flush()

        session.commit()

def add_discourse_graph(data):
    from py2neo import Graph
    from annograph.graph.models import Anchor, Annotation
    graph = Graph("http://neo4j:n0th1ng@localhost:7474/db/data/")
    graph.delete_all()
    nodes = []
    begin_node = Anchor(time = 0)
    base_ind_to_node = dict()
    base_levels = data.base_levels
    for b in base_levels:
        base_ind_to_node[b] = dict()
    nodes.append(begin_node)
    for i, level in enumerate(data.process_order):
        for d in data[level]:

            print(i, level)
            if i == 0: #Anchor level, should have all base levels in it
                begin_node = nodes[-1]

                to_align = []
                endpoints = []
                print(d)
                for b in base_levels:
                    begin, end = d[b]
                    endpoints.append(end)
                    base = data[b][begin:end]
                    to_align.append(base)

                if len(to_align) > 1:
                    aligned = list(align_phones(*to_align))
                else:
                    aligned = to_align
                first_aligned = aligned.pop(0)
                for j, first in enumerate(first_aligned):
                    time = None
                    if first != '-' and 'end' in first:
                        time = first.end
                    else:
                        for second in aligned:
                            s = second[j]
                            if s != '-' and 'end' in s:
                                time = s.end
                    node = Anchor(time = time)
                    nodes.append(node)
                    first_begin_node = -2
                    second_begin_nodes = [-2 for k in aligned]
                    if first != '-':
                        for k in range(j-1, -1, -1):
                            if first_aligned[k] != '-':
                                break
                            first_begin_node -= 1
                        annotation = Annotation(nodes[first_begin_node],
                                            node, base_levels[0], first.label)
                        graph.create(annotation)
                    for k, second in enumerate(aligned):
                        s = second[j]
                        if s != '-':
                            for m in range(j-1, -1, -1):
                                if second[m] != '-':
                                    break
                                second_begin_nodes[k] -= 1
                            annotation = Annotation(nodes[second_begin_nodes[k]],
                                                node, base_levels[k+1], s.label)
                            graph.create(annotation)
                        session.flush()
                for ind, b in enumerate(base_levels):
                    base_ind_to_node[b][endpoints[ind]] = nodes[-1]
                end_node = nodes[-1]
            else:
                for b in base_levels:
                    if b in d.references:

                        begin, end = d[b]
                        if begin not in base_ind_to_node[b]:
                            n = nodes[0]
                            for ind in range(begin+1):
                                for e in n.match_outgoing(b):
                                    n = e.end_node
                            base_ind_to_node[b][begin] = n
                        begin_node = base_ind_to_node[b][begin]
                        if end not in base_ind_to_node[b]:
                            n = nodes[0]
                            for ind in range(end):
                                for e in n.match_outgoing(b):
                                    n = e.end_node
                            base_ind_to_node[b][end] = n
                        end_node = base_ind_to_node[b][end]
            annotation = Annotation(begin_node, end_node, level, d.label)
            graph.create(annotation)
