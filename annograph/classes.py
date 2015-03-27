
import sqlalchemy, sqlalchemy.orm
from sqlalchemy import create_engine
from sqlalchemy.orm import joinedload

from .db import Base, Discourse, Node, AnnotationType, Annotation, Edge

from .config import Session, session_scope

from .helper import inspect_discourse, align_phones, get_or_create

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
            print('querying')
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

    def get_wordlist(self):
        pass

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

        Data should be a dictionary with keys for 'name', and for the
        relevant annotation types.  The lowest level of annotation should
        have timestamps, if applicable and the higher levels should have
        a key for the lower level they're associated with, with values of
        spans.

        In general, this function should not be called, as helper functions
        should exist to facilitate adding data to the corpus.

        Parameters
        ----------
        data : dict
            Data associated with the discourse
        """
        base_levels, has_name, has_label, process_order = inspect_discourse(data)
        with session_scope() as session:
            new_discourse = Discourse(discourse_label=data['name'])

            session.add(new_discourse)
            session.flush()
            nodes = list()
            begin_node = Node(time = 0, discourse = new_discourse)
            session.add(begin_node)
            pts = list()
            base_ind_to_node = dict()
            for b in base_levels:
                base_ind_to_node[b] = dict()
                pt = AnnotationType(type_label = b)
                session.add(pt)
                pts.append(pt)
            nodes.append(begin_node)
            for i, level in enumerate(process_order):
                anno_type = AnnotationType(type_label = level)
                session.add(anno_type)
                session.flush()
                for d in data['data'][level]:
                    annotation = get_or_create(session, Annotation, annotation_label = d['label'])
                    if i == 0:
                        begin_node = nodes[-1]
                        if len(base_levels) == 1:
                            begin, end = d[base_levels[0]]
                            base_ind_to_node[base_levels[0]][begin] = begin_node

                            base = data['data'][base_levels[0]][begin:end]
                            for b in base:
                                if 'end' in b:
                                    time = b['end']
                                else:
                                    time = None
                                phone_annotation = get_or_create(session,
                                                                Annotation,
                                                                annotation_label = b['label'])
                                node = Node(time = time, discourse = new_discourse)
                                session.add(node)
                                nodes.append(node)
                                session.flush()
                                edge = Edge(annotation = phone_annotation, type = pt,
                                            source_node = nodes[-2], target_node = node)
                                session.add(edge)
                                session.flush()
                            base_ind_to_node[base_levels[0]][end] = nodes[-1]
                        elif len(base_levels) == 2:
                            first_begin, first_end = d[base_levels[0]]
                            second_begin, second_end = d[base_levels[1]]

                            first_base = data['data'][base_levels[0]][first_begin:first_end]
                            second_base = data['data'][base_levels[1]][second_begin:second_end]

                            base_ind_to_node[base_levels[0]][first_begin] = begin_node
                            base_ind_to_node[base_levels[1]][second_begin] = begin_node
                            first_aligned, second_aligned = align_phones(first_base,
                                                                        second_base)
                            for j, f in enumerate(first_aligned):
                                s = second_aligned[j]
                                if f != '-' and 'end' in f:
                                    time = f['end']
                                elif s != '-' and 'end' in s:
                                    time = s['end']
                                else:
                                    time = None
                                node = Node(time = time, discourse = new_discourse)
                                session.add(node)
                                nodes.append(node)
                                session.flush()
                                first_begin_node = -2
                                if f != '-':
                                    first_annotation = get_or_create(session,
                                                                    Annotation,
                                                                    annotation_label = f['label'])
                                    for k in range(j-1, -1, -1):
                                        if first_aligned[k] != '-':
                                            break
                                        first_begin_node -= 1
                                    edge = Edge(annotation = first_annotation, type = pts[0],
                                            source_node = nodes[first_begin_node],
                                            target_node = node)
                                    session.add(edge)
                                second_begin_node = -2
                                if s != '-':
                                    second_annotation = get_or_create(session,
                                                                Annotation,
                                                                annotation_label = s['label'])
                                    for k in range(j-1, -1, -1):
                                        if second_aligned[k] != '-':
                                            break
                                        second_begin_node -= 1
                                    edge = Edge(annotation = second_annotation, type = pts[1],
                                            source_node = nodes[second_begin_node],
                                            target_node = node)
                                    session.add(edge)
                                session.flush()
                            base_ind_to_node[base_levels[0]][first_end] = nodes[-1]
                            base_ind_to_node[base_levels[1]][second_end] = nodes[-1]
                        end_node = nodes[-1]
                    else:
                        for b in base_levels:
                            if b in d:

                                begin, end = d[b]
                                if begin not in base_ind_to_node[b]:
                                    n = nodes[0]
                                    for i in range(begin+1):
                                        for e in n.source_edges:
                                            if str(e.type) == b:
                                                n = e.target_node
                                    base_ind_to_node[b][begin] = n
                                begin_node = base_ind_to_node[b][begin]
                                if end not in base_ind_to_node[b]:
                                    n = nodes[0]
                                    for i in range(end):
                                        for e in n.source_edges:
                                            if str(e.type) == b:
                                                n = e.target_node
                                    base_ind_to_node[b][end] = n
                                end_node = base_ind_to_node[b][end]

                    edge = Edge(annotation = annotation,
                            type = anno_type,
                            source_node = begin_node,
                            target_node = end_node)
                    session.add(edge)
                    session.flush()



            session.commit()
