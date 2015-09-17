import json
from uuid import uuid1
from py2neo import Node, Relationship

from .attributes import MetaAnnotation


class Annotation(Relationship, metaclass = MetaAnnotation):
    def __init__(self, begin_node, end_node, type, label):
        Relationship.__init__(self, begin_node, type, end_node)
        self.properties['label'] = label
        self.properties['id'] = str(uuid1())


class Anchor(Node):
    def __init__(self, **kwargs):
        Node.__init__(self, uuid1(), **kwargs)
