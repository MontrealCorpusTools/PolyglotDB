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

class LexiconItem(Base):
    __tablename__ = 'lexicon_item'

    id = Column(Integer, primary_key = True)

    orthography = Column(String(250), nullable = False)
    transcription = Column(String(250), nullable = False)

    frequency = Column(Float, nullable = False)

class WordProperty(Base):
    __tablename__ = 'lexicon_property'
    id = Column(Integer, primary_key = True)

    lexicon_id = Column(Integer, ForeignKey('lexicon_item.id'), nullable = False)
    lexicon_item = relationship(LexiconItem)

    label = Column(String(250), nullable = False)


class InventoryItem(Base):
    __tablename__ = 'inventory_item'

    id = Column(Integer, primary_key = True)

    label = Column(String(250), nullable = False)

class AnnotationType(Base):
    __tablename__ = 'annotation_type'

    id = Column(Integer, primary_key = True)

    label = Column(String(250), nullable = False)

class InventoryProperty(Base):
    __tablename__ = 'inventory_property'
    id = Column(Integer, primary_key = True)

    inventory_id = Column(Integer, ForeignKey('inventory_item.id'), nullable = False)
    inventory_item = relationship(InventoryItem)

    label = Column(String(250), nullable = False)
