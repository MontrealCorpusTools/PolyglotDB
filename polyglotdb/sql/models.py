from sqlalchemy import (Table, Column, Integer, SmallInteger, String, MetaData, ForeignKey,
                        Boolean,Float, PickleType, types, select, func )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, aliased
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import Comparator, hybrid_property
from sqlalchemy.sql.expression import cast, literal_column, column, and_, text

Base = declarative_base()

class CaseInsensitiveComparator(Comparator):
    def __eq__(self, other):
        return func.lower(self.__clause_element__()) == func.lower(other)

class AnnotationType(Base):
    __tablename__ = 'annotation_type'

    id = Column(Integer, primary_key = True)

    label = Column(String(250), nullable = False)

    def __repr__(self):
        return '<AnnotationType \'{}\'>'.format(self.label)

class Annotation(Base):
    __tablename__ = 'annotation'

    id = Column(Integer, primary_key = True)

    label = Column(String(250), nullable = False)

    annotation_type_id = Column(Integer, ForeignKey('annotation_type.id'), nullable = False)
    annotation_type = relationship(AnnotationType)

    properties = relationship('Property', backref = 'annotation')

    numeric_properties = relationship('NumericProperty', backref = 'annotation')

    @property
    def frequency(self):
        """ Returns frequency of an Annotation object"""
        for a in self.numeric_properties:
            if a.property_type.label == 'frequency':
                return a.value
        return None

    @property
    def transcription(self):
        """ Returns transcription of an Annotation object"""
        for a in self.properties:
            if a.property_type.label == 'transcription':
                return a.value
        return None

    def __repr__(self):
        return '<Annotation \'{}\'>'.format(self.label)

    @hybrid_property
    def label_insensitive(self):
        """ Returns lowercase label"""
        return self.label.lower()

    @label_insensitive.comparator
    def label_insensitive(cls):
        return CaseInsensitiveComparator(cls.label)

class PropertyType(Base):
    __tablename__ = 'property_type'

    id = Column(Integer, primary_key = True)

    label = Column(String(250), nullable = False)

    def __repr__(self):
        return '<PropertyType \'{}\'>'.format(self.label)

class NumericProperty(Base):
    __tablename__ = 'numeric_property'
    id = Column(Integer, primary_key = True)

    annotation_id = Column(Integer, ForeignKey('annotation.id'), nullable = False)

    property_type_id = Column(Integer, ForeignKey('property_type.id'), nullable = False)
    property_type = relationship(PropertyType)

    value = Column(Float, nullable = False)

class Property(Base):
    __tablename__ = 'property'
    id = Column(Integer, primary_key = True)

    annotation_id = Column(Integer, ForeignKey('annotation.id'), nullable = False)

    property_type_id = Column(Integer, ForeignKey('property_type.id'), nullable = False)
    property_type = relationship(PropertyType)

    value = Column(String(250), nullable = False)

class SpeaksIn(Base):
    __tablename__ = 'speaks_in'
    discourse_id = Column(Integer, ForeignKey('discourse.id'), primary_key = True)
    speaker_id = Column(Integer, ForeignKey('speaker.id'), primary_key = True)
    channel = Column(Integer, default = 0)
    speaker = relationship("Speaker", back_populates="discourses")
    discourse = relationship("Discourse", back_populates="speakers")


class Discourse(Base):
    __tablename__ = 'discourse'

    id = Column(Integer, primary_key = True)

    name = Column(String(250), nullable = False)

    properties = relationship('DiscourseProperty', backref = 'discourse')

    speakers = relationship("SpeaksIn",
        back_populates = "discourse")

    def get(self, key):
        """ Returns frequency of an Annotation object"""
        for a in self.properties:
            if a.property_type.label == key:
                return a.value
        return None

class Speaker(Base):
    __tablename__ = 'speaker'

    id = Column(Integer, primary_key = True)

    name = Column(String(250), nullable = False)

    properties = relationship('SpeakerProperty', backref = 'speaker')

    discourses = relationship("SpeaksIn",
        back_populates="speaker")

class SpeakerProperty(Base):
    __tablename__ = 'speaker_property'

    id = Column(Integer, primary_key = True)

    speaker_id = Column(Integer, ForeignKey('speaker.id'), nullable = False)

    property_type_id = Column(Integer, ForeignKey('property_type.id'), nullable = False)
    property_type = relationship(PropertyType)

    value = Column(String(250), nullable = False)


class SpeakerAnnotation(Base):
    __tablename__ = 'speaker_annotation'

    #speaker id
    id = Column(Integer, primary_key = True)

    speaker_id = Column(Integer, ForeignKey('speaker.id'), nullable=False)

    annotation_id = Column(Integer, ForeignKey('annotation_type.id') , nullable=False)

    property_type_id = Column(Integer, ForeignKey('property_type.id'), nullable=False)

    property_type = relationship(PropertyType)

    annotation_type = relationship(AnnotationType)

    speaker = relationship(Speaker)



    numerical_value = Column(Integer)

class DiscourseProperty(Base):
    __tablename__ = 'discourse_property'

    id = Column(Integer, primary_key = True)

    discourse_id = Column(Integer, ForeignKey('discourse.id'), nullable = False)

    property_type_id = Column(Integer, ForeignKey('property_type.id'), nullable = False)
    property_type = relationship(PropertyType)

    value = Column(String(250), nullable = False)

class SoundFile(Base):
    __tablename__ = 'sound_file'

    id = Column(Integer, primary_key = True)

    filepath = Column(String(250), nullable = False)

    consonant_filepath = Column(String(250), nullable = False)
    vowel_filepath = Column(String(250), nullable = False)
    low_freq_filepath = Column(String(250), nullable = False)

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

    channel = Column(Integer, default = 0)

    source = Column(String(250), nullable = False)

class Pitch(Base):
    __tablename__ = 'pitch'

    id = Column(Integer, primary_key = True)

    file_id = Column(Integer, ForeignKey('sound_file.id'), nullable = False)
    sound_file = relationship(SoundFile, back_populates= "pitches")

    time = Column(Float, nullable = False)

    F0 = Column(Float, nullable = False)

    channel = Column(Integer, default = 0)

    source = Column(String(250), nullable = False)
