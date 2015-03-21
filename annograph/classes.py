
import sqlalchemy, sqlalchemy.orm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .db import Base, Discourse, Node, AnnotationType, Annotation, Edge

class Corpus(object):
    """"""

    def __init__(self, engine_string):
        self.engine_string = engine_string
        self.engine = create_engine(self.engine_string)

    def initial_setup(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def add_discourses(self, discourses):
        for data in discourses:
            self.add_discourse(data)

    def add_discourse(self, data):
        """
        """
        DBSession = sessionmaker(bind=self.engine)
        session = DBSession()

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

        wt = AnnotationType(type_label = 'word')
        session.add(wt)
        session.flush()

        for w in data['data']['words']:
            query = session.query(Annotation).filter_by(annotation_label=p['label'])
            if query.count() == 0:
                annotation = Annotation(annotation_label = p['label'])
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

        lt = AnnotationType(type_label = 'line')
        session.add(lt)
        session.flush()

        for l in data['data']['lines']:
            query = session.query(Annotation).filter_by(annotation_label=p['label'])
            if query.count() == 0:
                annotation = Annotation(annotation_label = p['label'])
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
                        type = wt,
                        source_node = nodes[begin],
                        target_node = nodes[end - 1])
            session.add(edge)
            session.flush()




        session.commit()
