from functools import partial

from sqlalchemy import (Table, Column, Integer, String, MetaData, ForeignKey,
                        Boolean,Float, PickleType, types, select )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, aliased
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import cast, literal_column, column, and_, text

Base = declarative_base()


class AnnotationPath(types.TypeDecorator):
    '''
    Returns CHAR values with spaces stripped
    '''

    impl = types.String

    def process_bind_param(self, value, dialect):
        "No-op"
        return value

    def process_result_value(self, value, dialect):
        "Strip the trailing spaces on resulting values"
        return value[:-1]

    def copy(self):
        "Make a copy of this type"
        return AnnotationPath(self.impl.length)

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

    def __init__(self, source_node, target_node, type, annotation):
        self.source_node = source_node
        self.target_node = target_node
        self.type = type
        self.annotation = annotation

    @hybrid_property
    def phone(self):
        return self.subarc('phone')

    @phone.expression
    def phone(cls):
        return cls.subarc_subquery(cls, 'phone')

    def __repr__(self):
        return '<Edge: {} from Node {} to Node {} of Type {}>'.format(str(self.annotation),
                                                                self.source_id,
                                                                self.target_id,
                                                                str(self.type))

    def __str__(self):
        return str(self.annotation)

    def subarc_subquery(cls, type):
        subarcs = select([column("edge.type_id").label('type_id'),
                        column("edge.source_id").label('source_id'),
                        column("edge.target_id").label('target_id'),
                        literal_column("annotation.annotation_label || '.'").label(type)]).\
                        where(
                            and_(column("edge.source_id") == cls.source_id,
                            column("annotationtype.type_label") == type)
                            ).\
                        select_from(text("edge JOIN annotationtype ON \
                                    edge.type_id = annotationtype.type_id \
                                    JOIN annotation ON edge.annotation_id = annotation.annotation_id")).\
                        cte("subarcs", recursive = True)

        subarcs = subarcs.union_all(
                    select(
                            [literal_column("e.type_id").label("type_id"),
                            literal_column("s.source_id").label("source_id"),
                            literal_column("e.target_id").label("target_id"),
                            literal_column("s.{0} || annotation.annotation_label || '.'".format(type)).label(type)]
                    ).\
                    select_from(text("edge AS e JOIN subarcs AS s ON e.source_id = s.target_id \
                                    JOIN annotation ON e.annotation_id = annotation.annotation_id"
                                    ))

                )
        statement = select([column(type, AnnotationPath)]).\
                        where(column("subarcs.target_id") == cls.target_id).\
                        select_from(subarcs)
        return statement

    def subarc_sql(self, session, type):
        subarcs = session.query(
                            Edge.type_id.label('type_id'),
                            Edge.source_id.label('source_id'),
                            Edge.target_id.label('target_id')).\
                            join(Edge.annotation).\
                            filter(Edge.source_id == self.source_id).\
                            filter(Edge.type_id == type.type_id).\
                            add_columns(Annotation.annotation_label.concat('.').label(type.type_label)).\
                            cte("subarcs", recursive = True)
        subarc_alias = aliased(subarcs, name="s")
        edge_alias = aliased(Edge, name='e')
        subarcs = subarcs.union_all(
                  session.query(
                            edge_alias.type_id.label('type_id'),
                            subarc_alias.c.source_id.label('source_id'),
                            edge_alias.target_id.label('target_id')).\
                  join(subarc_alias, edge_alias.source_id == subarc_alias.c.target_id).\
                  join(edge_alias.annotation).\
                  #join(edge_alias.type).\
                  #filter(edge_alias.type == type).\
                  add_columns(getattr(subarc_alias.c,type.type_label).\
                                concat(Annotation.annotation_label).concat('.').\
                                label(type.type_label)
                                )
                )
        q = session.query(cast(getattr(subarcs.c,type.type_label), AnnotationPath)).filter(subarcs.c.target_id == self.target_id)

        return q

    def subarc(self, type):
        s = self.source_node
        t = self.target_node
        subarc = list()
        edges = s.source_edges
        while True:
            for e in edges:

                if str(e.type) == type:
                    break
            subarc.append(e)
            edges = e.target_node.source_edges
            if e.target_node == t:
                break
        return subarc

def generate_edge_class(subarcs, edge_class = Edge):
    #for s in subarcs:
        #func = partial(edge_class.subarc, type = s)
        #exp = partial(edge_class.subarc_subquery, type = s)
        #p = hybrid_property(lambda self: func(self))
        #p.expression = lambda cls: exp(cls)
        #setattr(edge_class, s, p)
    return edge_class


class AnnotationFrequencies(Base):
    """
    Cache table for storing frequency information for annotations and
    how they're used in the corpus.

    Attributes
    ----------
    annotation : Annotation
        Column for annotations

    type : AnnotationType
        column for the types of annotations

    frequency : float
        Frequency of the annotation-type combination
    """
    __tablename__ = 'annotationfrequencies'


    annotation_id = Column(Integer, ForeignKey('annotation.annotation_id'), primary_key = True)
    annotation = relationship(Annotation)

    type_id = Column(Integer, ForeignKey('annotationtype.type_id'), primary_key = True)
    type = relationship(AnnotationType)

    frequency = Column(Float, nullable=False)

class AnnotationAttributes(Base):
    """
    Cache table for storing frequency information for annotations and
    how they're used in the corpus.

    Attributes
    ----------
    annotation : Annotation
        Column for annotations

    type : AnnotationType
        column for the types of annotations

    sound_file_path : str or None
        Fully specified path to a sound file, if applicable
    """
    __tablename__ = 'annotationattributes'


    annotation_id = Column(Integer, ForeignKey('annotation.annotation_id'), primary_key = True)
    annotation = relationship(Annotation)

    type_id = Column(Integer, ForeignKey('annotationtype.type_id'), primary_key = True)
    type = relationship(AnnotationType)

    attributes = Column(PickleType, nullable=True)

class AnnotationSubarcs(Base):
    """
    Cache table for storing subarcs of annotations

    Attributes
    ----------
    annotation : Annotation
        Column for annotations

    type : AnnotationType
        column for the types of annotations

    sound_file_path : str or None
        Fully specified path to a sound file, if applicable
    """
    __tablename__ = 'annotationsubarcs'


    annotation_id = Column(Integer, ForeignKey('annotation.annotation_id'), primary_key = True)
    annotation = relationship(Annotation)

    higher_type_id = Column(Integer, ForeignKey('annotationtype.type_id'), primary_key = True)

    lower_type_id = Column(Integer, ForeignKey('annotationtype.type_id'), primary_key = True)

    higher_types = relationship(AnnotationType,
                                primaryjoin=higher_type_id==AnnotationType.type_id,
                                backref='higher_types')

    lower_types = relationship(AnnotationType,
                                primaryjoin=lower_type_id==AnnotationType.type_id,
                                backref='lower_types')

    subarc = Column(String(250), nullable = False)
