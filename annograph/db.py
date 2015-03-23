
import os
import pickle

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey,Boolean,Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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

    def subarcs(self, type = None):
        s = self.source_node
        t = self.target_node
        for e in s.target_edges:
            if e == self:
                continue
