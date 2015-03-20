
import sqlalchemy, sqlalchemy.orm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .db import Base, Discourse, Node, AnnotationType, Annotation, Edge

protected = ['label', 'begin', 'end']

def add_recursive(data, session):
    k, v = data
    annoTypes = session.query(AnnotationType).filter_by(type_label = k)
    if annoTypes.count() == 0:
        t = AnnotationType(type_label = k)
        session.add(t)
        session.flush()
    else:
        t = annoTypes.first()

    if not any(x not in protected for x in v):
        #Add nodes
        pass
    else:
        #Recurse
        for x in v:
            newk, newv = next(x.items())
            begin_node, end_node = add_recursive(newk, newv)




class Corpus(object):
    """"""

    def __init__(self, engine_string):
        self.engine_string = engine_string
        self.engine = create_engine(self.engine_string)

    def initial_setup(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def add_discourse(self, data):
        """
        """
        DBSession = sessionmaker(bind=self.engine)
        session = DBSession()

        new_discourse = Speaker(discourse_label=data['name'])
        session.add(new_discourse)
        session.flush()

        #Recursively add data
        session.commit()
