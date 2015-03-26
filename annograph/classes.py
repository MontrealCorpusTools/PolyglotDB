
import sqlalchemy, sqlalchemy.orm
from sqlalchemy import create_engine
from sqlalchemy.orm import joinedload

from .db import Base, Discourse, Node, AnnotationType, Annotation, Edge

from .config import Session, session_scope

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

            q = session.query(Edge).options(joinedload('*'))
            q = q.join(Edge.type)
            q = q.join(Edge.annotation)
            q = q.filter(AnnotationType.type_id == t.type_id)
            q = q.filter(Annotation.annotation_label.ilike(orthography))
            return q.first()

    def get_wordlist(self):
        pass

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
        with session_scope() as session:
            new_discourse = Discourse(discourse_label=data['name'])

            session.add(new_discourse)
            session.flush()
            nodes = list()
            begin_node = Node(time = 0, discourse = new_discourse)
            session.add(begin_node)
            nodes.append(begin_node)
            pt = AnnotationType(type_label = 'phone')
            session.add(pt)
            session.flush()
            prev = begin_node
            for p in data['data']['phones']:
                if 'end' in p:
                    time = p['end']
                else:
                    time = None
                node = Node(time = time, discourse = new_discourse)
                session.add(node)
                query = session.query(Annotation).filter_by(annotation_label=p['label'])
                if query.count() == 0:
                    annotation = Annotation(annotation_label = p['label'])
                    session.add(annotation)
                else:
                    annotation = query.first()
                session.flush()
                nodes.append(node)
                edge = Edge(annotation = annotation, type = pt,
                            source_node = prev, target_node = node)
                session.add(edge)

                prev = node
                session.flush()
            if 'words' in data['data']:

                wt = AnnotationType(type_label = 'word')
                session.add(wt)
                session.flush()
                for w in data['data']['words']:
                    query = session.query(Annotation).filter_by(annotation_label=w['label'])
                    if query.count() == 0:
                        annotation = Annotation(annotation_label = w['label'])
                        session.add(annotation)
                    else:
                        annotation = query.first()
                    begin, end = w['phones']
                    session.flush()
                    edge = Edge(annotation = annotation,
                                type = wt,
                                source_node = nodes[begin],
                                target_node = nodes[end - 1])
                    session.add(edge)
                    session.flush()

            if 'lines' in data['data']:
                lt = AnnotationType(type_label = 'line')
                session.add(lt)
                session.flush()
                for l in data['data']['lines']:
                    query = session.query(Annotation).filter_by(annotation_label=l['label'])
                    if query.count() == 0:
                        annotation = Annotation(annotation_label = l['label'])
                        session.add(annotation)
                    else:
                        annotation = query.first()
                    session.add(annotation)
                    first_ind, final_ind = l['words']
                    words = data['data']['words'][first_ind:final_ind]
                    first_word = words[0]
                    final_word = words[-1]
                    begin = first_word['phones'][0]
                    end = final_word['phones'][1]
                    session.flush()
                    edge = Edge(annotation = annotation,
                                type = lt,
                                source_node = nodes[begin],
                                target_node = nodes[end - 1])
                    session.add(edge)
                    session.flush()

            session.commit()
