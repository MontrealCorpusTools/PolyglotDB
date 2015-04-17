
import sqlalchemy, sqlalchemy.orm
from sqlalchemy import create_engine, func
from sqlalchemy.orm import joinedload, aliased
from sqlalchemy.sql.expression import and_

from .db import (Base, Discourse, Node, Edge, generate_edge_class, AnnotationType, Annotation,
                            AnnotationFrequencies, AnnotationAttributes, AnnotationSubarcs)

from .config import Session, session_scope

from .helper import align_phones, get_or_create


class Corpus(object):
    """
    Basic corpus object that has information about the SQL database
    and serves as an abstraction layer between the SQL representations
    and Python usage.

    Parameters
    ----------
    engine_string : str
        String specifying the url of the database to use, such as 'sqlite:///dev.db'

    """

    def __init__(self, engine_string, **kwargs):
        self.engine_string = engine_string
        self.engine = create_engine(self.engine_string)
        Session.configure(bind=self.engine)

        self.column_mapping = kwargs
        self.lexicon_only = False

    def initial_setup(self):
        """
        Clears the current database and sets up the various tables needed.
        This function should only be called once.
        """
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def _type(self, session, name):
        q = session.query(AnnotationType)
        if name in self.column_mapping:
            q = q.filter(AnnotationType.type_label == self.column_mapping[name])
        else:
            q = q.filter(AnnotationType.type_label.ilike(name))
        return q.first()

    def _wordtype(self, session):
        q = session.query(AnnotationType)
        if 'word' in self.column_mapping:
            q = q.filter(AnnotationType.type_label == self.column_mapping['word'])
        else:
            q = q.filter(AnnotationType.type_label.ilike("word") |
                        AnnotationType.type_label.ilike("orthography"))
        return q.first()

    def find(self, orthography):
        with session_scope() as session:
            t = self._wordtype(session)
            if t is None:
                return
            q = session.query(Edge).options(joinedload('*'))
            q = q.join(Edge.type)
            q = q.join(Edge.annotation)
            q = q.filter(AnnotationType.type_id == t.type_id)
            q = q.filter(Annotation.annotation_label.ilike(orthography))
            return q.first()

    def _find(self, session, key, type):
        t = self._type(session, type)
        if t is None:
            return
        q = session.query(Edge).options(joinedload('*'))
        q = q.join(Edge.type)
        q = q.join(Edge.annotation)
        q = q.filter(AnnotationType.type_id == t.type_id)
        q = q.filter(Annotation.annotation_label.ilike(key))
        return q.all()

    def _get_transitive_closures(self, higher_type, lower_type):
        with session_scope() as session:
            subarcs = session.query(
                                Edge.type_id.label('type_id'),
                                Edge.source_id.label('source_id'),
                                Edge.target_id.label('target_id'),
                                Edge.annotation_id.label('annotation_id')).\
                                join(Edge.annotation).\
                                join(Edge.type).\
                                filter(AnnotationType.type_label == lower_type).\
                                add_columns(Annotation.annotation_label.concat('.').label(lower_type)).\
                                cte("subarcs", recursive = True)
            subarc_alias = aliased(subarcs, name="s")
            edge_alias = aliased(Edge, name='e')
            subarcs = subarcs.union_all(
                      session.query(
                                edge_alias.type_id.label('type_id'),
                                subarc_alias.c.source_id.label('source_id'),
                                edge_alias.target_id.label('target_id'),
                                edge_alias.target_id.label('annotation_id')).\
                      join(subarc_alias, edge_alias.source_id == subarc_alias.c.target_id).\
                      join(edge_alias.annotation).\
                      join(edge_alias.type).\
                      filter(AnnotationType.type_label == lower_type).\
                      add_columns(getattr(subarc_alias.c, lower_type).\
                                    concat(Annotation.annotation_label).concat('.').\
                                    label(lower_type)
                                    )
                    )
            q = session.query(Edge.annotation_id, Edge.type_id.label('higher_type_id'),).\
                            join(Edge.type).\
                            join(subarcs, and_(subarcs.c.target_id == Edge.target_id, \
                                            subarcs.c.source_id == Edge.source_id)).\
                            add_columns(subarcs.c.type_id.label('lower_type_id'),getattr(subarcs.c, lower_type))
            q = q.filter(AnnotationType.type_label == higher_type).distinct()
            for row in q.all():
                #e, count = row
                r = AnnotationSubarcs(annotation_id = row[0],
                                            higher_type_id = row[1],
                                            lower_type_id = row[2],
                                            subarc = row[3])
                session.add(r)
            session.flush()


    def get_wordlist(self):
        with session_scope() as session:
            wt = self._wordtype(session)
            pt = self._type(session, 'phone')
            #print(Edge.phone.expression)
            #subarcs = self._get_transitive_closures(session, 'word', 'phone')
            q = session.query(Annotation.annotation_label,
                    AnnotationFrequencies.frequency).options(joinedload('*'))
            q = q.join(Edge, Edge.annotation_id == Annotation.annotation_id)
            q = q.join(AnnotationFrequencies,
                        Annotation.annotation_id == AnnotationFrequencies.annotation_id)
            q = q.join(AnnotationSubarcs, and_(AnnotationSubarcs.annotation_id == Annotation.annotation_id,
                                            AnnotationSubarcs.higher_types == wt))
            q = q.filter(Edge.type_id == wt.type_id)
            q = q.filter(AnnotationSubarcs.lower_types == pt)
            q = q.add_columns(AnnotationSubarcs.subarc)
            q = q.distinct()

            results = q.all()
        return results

    def _generate_frequency_table(self):
        if self.lexicon_only:
            return

        with session_scope() as session:
            q = session.query(AnnotationFrequencies)
            q.delete()
            session.flush()

            q = session.query(Edge, func.count(Edge.annotation_id))
            q = q.join(Edge.type)
            q = q.join(Edge.annotation)
            q = q.group_by(Edge.annotation_id, Edge.type_id)
            for row in q.all():
                e, count = row
                r = AnnotationFrequencies(annotation = e.annotation,
                                            type = e.type,
                                            frequency = count)
                session.add(r)
            session.flush()

    def get_edge_labels(self):
        labels = dict()
        with session_scope() as session:
            q = session.query(Edge)
            q = q.join(Edge.type)
            q = q.join(Edge.annotation)
            for e in q.all():
                if str(e.type) not in labels:
                    labels[str(e.type)] = dict()
                labels[str(e.type)][e.source_id,e.target_id] = '{}/{}'.format(str(e.type),str(e.annotation))
        return labels

    def add_discourses(self, discourses):
        for data in discourses:
            self.add_discourse(data)

    def add_discourse(self, data):
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
                    annotation = get_or_create(session, Annotation, annotation_label = d['label'])

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
                                time = first['end']
                            else:
                                for second in aligned:
                                    s = second[j]
                                    if s != '-' and 'end' in s:
                                        time = s['end']
                            node = Node(time = time, discourse = new_discourse)
                            session.add(node)
                            nodes.append(node)
                            session.flush()
                            first_begin_node = -2
                            second_begin_nodes = [-2 for k in aligned]
                            if first != '-':
                                first_annotation = get_or_create(session,
                                                                Annotation,
                                                                annotation_label = first['label'])
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
                                                                annotation_label = s['label'])
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
                            if b in d:

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
