
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
    __tablename__ = 'discourse'

    discourse_id = Column(Integer, primary_key=True)

    discourse_label = Column(String(250), nullable=False)

class Node(Base):
    __tablename__ = 'node'

    node_id = Column(Integer, primary_key=True)

    time = Column(Float, nullable=True)

    discourse_id = Column(Integer, ForeignKey('discourse.id'), nullable = False)
    type = relationship(Discourse)


class AnnotationType(Base)
    __tablename__ = 'annotationtype'

    type_id = Column(Integer, primary_key=True)

    type_label = Column(String(250), nullable=False)

class Annotation(Base):
    __tablename__ = 'annotation'

    annotation_id = Column(Integer, primary_key=True)

    annotation_label = Column(String(250), nullable=False)


class Edge(Base):
    __tablename__ = 'edge'

    edge_id = Column(Integer, primary_key=True)

    source_id = Column(Integer,
                        ForeignKey('node.node_id'),
                        primary_key = True)

    target_id = Column(Integer,
                        ForeignKey('node.node_id'),
                        primary_key = True)

    type_id = Column(Integer, ForeignKey('annotationtype.id'), primary_key = True)
    type = relationship(AnnotationType)

    annotation_id = Column(Integer, ForeignKey('annotation.id'))
    annotation = relationship(Annotation)

    source_node = relationship(Node,
                                primaryjoin=source_id==Node.node_id,
                                backref='source_edges')
    target_node = relationship(Node,
                                primaryjoin=target_id==Node.node_id,
                                backref='target_edges')
