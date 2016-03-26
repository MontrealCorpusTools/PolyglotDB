from sqlalchemy import (Table, Column, Integer, SmallInteger, String, MetaData, ForeignKey,
                        Boolean,Float, PickleType, types, select )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, aliased
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import cast, literal_column, column, and_, text

Base = declarative_base()

class Word(Base):
    __tablename__ = 'word'

    id = Column(Integer, primary_key = True)

    orthography = Column(String(250), nullable = False)
    transcription = Column(String(250), nullable = False)

    frequency = Column(Float, nullable = False)

class WordPropertyType(Base):
    __tablename__ = 'word_property_type'
    id = Column(Integer, primary_key = True)

    label = Column(String(250), nullable = False)


class WordProperty(Base):
    __tablename__ = 'word_property'
    id = Column(Integer, primary_key = True)

    word_id = Column(Integer, ForeignKey('word.id'), nullable = False)
    word = relationship(Word)

    property_id = Column(Integer, ForeignKey('word_property_type.id'), nullable = False)
    property_type = relationship(WordPropertyType)

    value = Column(String(250), nullable = False)

class WordNumericProperty(Base):
    __tablename__ = 'word_numeric_property'
    id = Column(Integer, primary_key = True)

    word_id = Column(Integer, ForeignKey('word.id'), nullable = False)
    word = relationship(Word)

    property_id = Column(Integer, ForeignKey('word_property_type.id'), nullable = False)
    property_type = relationship(WordPropertyType)

    value = Column(Float, nullable = False)

class AnnotationType(Base):
    __tablename__ = 'annotation_type'

    id = Column(Integer, primary_key = True)

    label = Column(String(250), nullable = False)

    def __repr__(self):
        return '<AnnotationType \'{}\'>'.format(self.label)

class InventoryItem(Base):
    __tablename__ = 'inventory_item'

    id = Column(Integer, primary_key = True)

    label = Column(String(250), nullable = False)

    type_id = Column(Integer, ForeignKey('annotation_type.id'), nullable = False)
    annotation_type = relationship(AnnotationType)

class InventoryProperty(Base):
    __tablename__ = 'inventory_property'
    id = Column(Integer, primary_key = True)

    inventory_id = Column(Integer, ForeignKey('inventory_item.id'), nullable = False)
    inventory_item = relationship(InventoryItem)

    label = Column(String(250), nullable = False)

    value = Column(String(250), nullable = False)

class Discourse(Base):
    __tablename__ = 'discourse'

    id = Column(Integer, primary_key = True)

    name = Column(String(250), nullable = False)

class Speaker(Base):
    __tablename__ = 'speaker'

    id = Column(Integer, primary_key = True)

    name = Column(String(250), nullable = False)

class SpeakerProperty(Base):
    __tablename__ = 'speaker_property'

    id = Column(Integer, primary_key = True)

    speaker_id = Column(Integer, ForeignKey('speaker.id'), nullable = False)
    speaker = relationship(Speaker)

    label = Column(String(250), nullable = False)

    value = Column(String(250), nullable = False)

class SoundFile(Base):
    __tablename__ = 'sound_file'

    id = Column(Integer, primary_key = True)

    filepath = Column(String(250), nullable = False)

    duration = Column(Float, nullable = False)

    sampling_rate = Column(Integer, nullable = False)

    n_channels = Column(SmallInteger, nullable = False)

    discourse_id = Column(Integer, ForeignKey('discourse.id'), nullable = False)
    discourse = relationship(Discourse)

    formants = relationship("Formants", back_populates = "sound_file",
                            cascade="all, delete, delete-orphan")

    pitches = relationship("Pitch", back_populates = "sound_file",
                            cascade="all, delete, delete-orphan")

class Formants(Base):
    __tablename__ = 'formants'

    id = Column(Integer, primary_key = True)

    file_id = Column(Integer, ForeignKey('sound_file.id'), nullable = False)
    sound_file = relationship(SoundFile, back_populates="formants")

    time = Column(Float, nullable = False)

    F1 = Column(Integer, nullable = False)

    F2 = Column(Integer, nullable = False)

    F3 = Column(Integer, nullable = False)

    source = Column(String(250), nullable = False)

class Pitch(Base):
    __tablename__ = 'pitch'

    id = Column(Integer, primary_key = True)

    file_id = Column(Integer, ForeignKey('sound_file.id'), nullable = False)
    sound_file = relationship(SoundFile, back_populates= "pitches")

    time = Column(Float, nullable = False)

    F0 = Column(Float, nullable = False)

    source = Column(String(250), nullable = False)
