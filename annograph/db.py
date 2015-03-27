

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey,Boolean,Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.associationproxy import association_proxy

Base = declarative_base()

class Discourse(Base):
    """
    Discourses act as a group for nodes that occupy the same timeline.

    Attributes
    ----------
    discourse_label : str
        Name to identify the discourse

    sound_file_path : str or None
        Fully specified path to a sound file, if applicable
    """
    __tablename__ = 'discourse'

    discourse_id = Column(Integer, primary_key=True)

    discourse_label = Column(String(250), nullable=False)

    sound_file_path = Column(String(250), nullable=True)

    def __repr__(self):
        return '<Discourse: id {} with label {}>'.format(self.discourse_id,
                                                        self.discourse_label)

    def __str__(self):
        return repr(self)

class Node(Base):
    """
    Node for edges to connect to.  These can be anchored in time, or
    more abstract.

    Attributes
    ----------
    time : float
        Time point in seconds from the beginning of some file, can be None

    discourse : Discourse
        Discourse that the node belongs to
    """
    __tablename__ = 'node'

    node_id = Column(Integer, primary_key=True)

    time = Column(Float, nullable=True)

    discourse_id = Column(Integer, ForeignKey('discourse.discourse_id'), nullable = False)
    discourse = relationship(Discourse)

    def __repr__(self):
        return '<Node: id {} of discourse {}>'.format(self.node_id, self.discourse)

    def __str__(self):
        return repr(self)


class AnnotationType(Base):
    """
    Annotation type, such as for phones, words, sentences, speakers, etc.

    Attributes
    ----------
    type_label : str
        Label of the annotation type
    """
    __tablename__ = 'annotationtype'

    type_id = Column(Integer, primary_key=True)

    type_label = Column(String(250), nullable=False)

    def __repr__(self):
        return '<AnnotationType: id {}, label \'{}\'>'.format(self.type_id,
                                                            self.type_label)

    def __str__(self):
        return self.type_label

class Annotation(Base):
    """
    Annotation for edges.

    Attributes
    ----------
    annotation_label : str
        Label of the annotation
    """
    __tablename__ = 'annotation'

    annotation_id = Column(Integer, primary_key=True)

    annotation_label = Column(String(250), nullable=False)

    def __repr__(self):
        return '<Annotation: id {}, label \'{}\'>'.format(self.annotation_id,
                                                            self.annotation_label)

    def __str__(self):
        return self.annotation_label

class Edge(Base):
    """
    Edge for annotation graphs.

    Attributes
    ----------
    source_node : Node
        Source node of the edge

    target_node : Node
        Target node of the edge

    annotation : Annotation
        Label for the edge

    type : AnnotationType
        Type of the annotation associated with the edge
    """
    __tablename__ = 'edge'

    source_id = Column(Integer,
                        ForeignKey('node.node_id'),
                        primary_key = True)

    target_id = Column(Integer,
                        ForeignKey('node.node_id'),
                        primary_key = True)

    type_id = Column(Integer, ForeignKey('annotationtype.type_id'), primary_key = True)
    type = relationship(AnnotationType)

    annotation_id = Column(Integer, ForeignKey('annotation.annotation_id'))
    annotation = relationship(Annotation)

    source_node = relationship(Node,
                                primaryjoin=source_id==Node.node_id,
                                backref='source_edges')
    target_node = relationship(Node,
                                primaryjoin=target_id==Node.node_id,
                                backref='target_edges')

    #parent_id = Column(Integer, nullable=True)
    #parent = relationship("Edge", backref = 'subarcs')

    def __repr__(self):
        return '<Edge: {} from Node {} to Node {} of Type {}>'.format(str(self.annotation),
                                                                self.source_id,
                                                                self.target_id,
                                                                str(self.type))

    def __str__(self):
        return str(self.annotation)

    def subarc(self, type):
        s = self.source_node
        t = self.target_node
        subarc = list()
        edges = s.source_edges
        while True:
            print(edges)
            for e in edges:
                print(e, e.type, type)

                if e.type == type:
                    break
            subarc.append(e)
            edges = e.target_node.source_edges
            if e.target_node == t:
                break
        return subarc

