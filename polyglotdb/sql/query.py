

from sqlalchemy import distinct

from .models import (AnnotationType, PropertyType, Property,
                        NumericProperty, Annotation, Speaker, Discourse,
                        SpeakerProperty, DiscourseProperty, SpeakerAnnotation)

from .helper import get_or_create

class BasePropertyStore(object):
    def __init__(self, corpus_context):
        self.corpus_context = corpus_context
        self.cache = {}
        self.prop_type_cache = {}

    def get_or_create_property_type(self, property_type):
        """ 
        Gets property_type if it is in the cache, creates it otherwise 

        Parameters
        ----------
        property_type : str
            the PropertyType label

        Returns
        -------
        the value of the cache at the property_type
        """

        if property_type not in self.prop_type_cache:
            pt, _ = get_or_create(self.corpus_context.sql_session,
                                    PropertyType, label = property_type)
            self.prop_type_cache[property_type] = pt
        return self.prop_type_cache[property_type]

    def get_property_type(self, property_type):
        """ 
        Gets property_type if it is in the cache, throws error otherwise

        Parameters
        ----------
        property_type : str
            the PropertyType label

        Returns
        -------
        the value of the cache at the property_type
        """

        if property_type not in self.prop_type_cache:
            q = self.corpus_context.sql_session.query(PropertyType)
            q = q.filter(PropertyType.label == property_type)
            pt = q.first()
            if pt is None:
                raise(AttributeError('Property type \'{}\' not found.'.format(property_type)))
            self.prop_type_cache[property_type] = pt
        return self.prop_type_cache[property_type]

    def get_or_create_annotation_type(self, annotation_type):
        """ 
        Gets annotation_type if it is in the cache, creates it otherwise 

        Parameters
        ----------
        annotation_type : str 
            the annotation_type label

        Returns
        -------
        the value of the cache at the annotation_type
        """
        if annotation_type not in self.anno_type_cache:
            at, _ = get_or_create(self.corpus_context.sql_session,
                                    AnnotationType, label = annotation_type)
            self.anno_type_cache[annotation_type] = at
        return self.anno_type_cache[annotation_type]


    def get_annotation_type(self, annotation_type):
        """ 
        Gets annotation_type if it is in the cache, throws error otherwise

        Parameters
        ----------
        annotation_type : str
            the AnnotationType label

        Returns
        -------
        the value of the cache at the annotation_type
        """
        if annotation_type not in self.anno_type_cache:
            q = self.corpus_context.sql_session.query(AnnotationType)
            q = q.filter(AnnotationType.label == annotation_type)
            at = q.first()
            if at is None:
                raise(AttributeError('Annotation type \'{}\' not found.'.format(annotation_type)))
            self.anno_type_cache[annotation_type] = at
        return self.anno_type_cache[annotation_type]

    def lookup(self, key, annotation_type, case_sensitive = False):
        """
        searches for an annotation by label in the database

        Parameters
        ----------
        key : str
            The label of the annotation
        annotation_type : str
            the label of the annotation type
        case_sensitive : boolean
            Defaults to False

        Returns 
        -------
        annotation : Annotation
            the found Annotation object
        """
        q =  self.corpus_context.sql_session.query(Annotation)
        q = q.join(AnnotationType)
        q = q.filter(AnnotationType.label == annotation_type)
        if case_sensitive:
            q = q.filter(Annotation.label == key)
        else:
            q = q.filter(Annotation.label_insensitive == key)
        annotation = q.first()
        return annotation

class Lexicon(BasePropertyStore):
    """
    The primary way of querying Word, Phone, and Syllable entries in a relational database.
    """
    def __init__(self, corpus_context):
        super(Lexicon, self).__init__(corpus_context)
        self.anno_type_cache = {}

    def __getitem__(self, key):
        if key not in self.cache:
            q =  self.corpus_context.sql_session.query(Annotation).filter(Annotation.label == key)
            word = q.first()
            self.cache[key] = word
        return self.cache[key]

    def add_properties(self, annotation_type, data, types, case_sensitive = False):
        """
        Adds properties to the Lexicon

        Parameters
        ----------
        annotation_type : str
            the label of the annotation type
        data : dict
            the properties to add
        types : dict
            the types of properties to add
        case_sensitive : boolean
            Defaults to False
        """
        for label, d in data.items():
            annotation = self.lookup(label, annotation_type, case_sensitive = case_sensitive)
            if annotation is None:
                continue
            for k, v in d.items():
                if v is None or v == "":
                    continue
                pt = self.get_or_create_property_type(k)
                if types[k] in [int, float]:
                    c = NumericProperty
                    v = float(v)
                    
                else:
                    c = Property
                    v = str(v)
                try:
                    prop, _ = get_or_create(self.corpus_context.sql_session, c,
                                    annotation = annotation, property_type = pt, value = v)
                except:
                    print(pt)
    def get_property_levels(self, property_type, annotation_type = None):
        """
        Searches for matching Property matching property_type, gets property levels from that
        Parameters
        ----------
        property_type : str
            the label of the property type
        annotation_type : str
            the label of the annotation_type
            Defaults to None

        Returns
        -------
        list
            list of property levels for property_type
        """
        q = self.corpus_context.sql_session.query(distinct(Property.value))
        q = q.join(PropertyType, Property.property_type_id == PropertyType.id)
        q = q.filter(PropertyType.label == property_type)
        if annotation_type is not None:
            q = q.join(Annotation, Property.annotation_id == Annotation.id)
            q = q.join(AnnotationType, Annotation.annotation_type_id == AnnotationType.id)
            q = q.filter(AnnotationType.label == annotation_type)
        return [x[0] for x in q.all()]


    def get_or_create_annotation(self, label, annotation_type):
        """ 
        Gets label and annotation_type if they are in the cache, inserts them otherwise

        Parameters
        ----------
        annotation_type : str 
            the AnnotationType label
        label : str
            the Annotation label

        Returns
        -------
        the value of the cache at the annotation_type and label

        created : boolean
            True if the items were inserted, False if they already existed
        """
        created = False
        if (label, annotation_type) not in self.cache:
            at = self.get_or_create_annotation_type(annotation_type)
            a, _ = get_or_create(self.corpus_context.sql_session,
                                    Annotation,
                                    label = label,
                                    annotation_type = at)
            self.cache[(label, annotation_type)] = a
            created = True
        return self.cache[(label, annotation_type)], created

    def list_labels(self, annotation_type):
        """
        Lists labels of an AnnotationType
        
        Parameters
        ----------
        annotation_type : str
            the type of Annotation to list

        Returns
        -------
        list
            a sorted list of labels of that AnnotationType     
         """
        q =  self.corpus_context.sql_session.query(Annotation.label)
        q = q.join(AnnotationType)
        q = q.filter(AnnotationType.label == annotation_type)
        return sorted([x[0] for x in q.all()])

    def words(self):
        """
        Lists words of an Annotation
        
        Returns
        -------
        list
            a sorted list of words of that Annotation     
         """
        q =  self.corpus_context.sql_session.query(Annotation.label)
        q = q.join(AnnotationType)
        q = q.filter(AnnotationType.label == self.corpus_context.word_name)
        return sorted([x[0] for x in q.all()])

    def phones(self):
        """
        Lists phones of an Annotation
        
        Returns
        -------
        list
            a sorted list of phones of that Annotation     
         """
        q =  self.corpus_context.sql_session.query(Annotation.label)
        q = q.join(AnnotationType)
        q = q.filter(AnnotationType.label == self.corpus_context.phone_name)
        return sorted([x[0] for x in q.all()])

    def syllables(self):
        """
        Lists syllables of an Annotation
        
        Returns
        -------
        list
            a sorted list of syllables of that Annotation     
         """
        q = self.corpus_context.sql_session.query(Annotation.label)
        q = q.join(AnnotationType)
        q = q.filter(AnnotationType.label == 'syllable')
        return sorted([x[0] for x in q.all()])

class Census(BasePropertyStore):
    def __init__(self, corpus_context):
        super(Census, self).__init__(corpus_context)
        self.anno_type_cache = {}

    def __getitem__(self, key):
        if key not in self.cache:
            q =  self.corpus_context.sql_session.query(Speaker).filter(Speaker.name == key)
            speaker = q.first()
            self.cache[key] = speaker
        return self.cache[key]

    def lookup_discourse(self, name):
        """ 
        Looks up a discourse by name

        Parameters
        ----------
        name : str
            the name of the discourse to find

        Returns
        -------
        discourse : Discourse
            the found Discourse object
        """
        q =  self.corpus_context.sql_session.query(Discourse).filter(Discourse.name == name)
        discourse = q.first()
        return discourse

    def lookup_speaker(self,name):
        """
        looks up speaker by name

        Parameters
        ----------
        name :str
            name of speaker
        Returns
        -------
        speaker : Speaker
            found speaker
        """
        q = self.corpus_context.sql_session.query(Speaker).filter(Speaker.name == name)
        speaker = q.first()
        return speaker

    def add_speaker_properties(self, data, types):
        """
        Adds speaker properties to the Census

        Parameters
        ----------
        data : dict
            the properties to add
        types : dict
            the types of properties to add
        """
        for label, d in data.items():
            speaker = self[label]
            if speaker is None:
                continue
            for k, v in d.items():
                if v is None:
                    continue
                pt = self.get_or_create_property_type(k)
                v = str(v)
                prop, _ = get_or_create(self.corpus_context.sql_session, SpeakerProperty,
                                    speaker = speaker, property_type = pt, value = v)

    def add_discourse_properties(self, data, types):
        """
        Adds discourse properties to the Census

        Parameters
        ----------
        data : dict
            the properties to add
        types : dict
            the types of properties to add
        """
        for label, d in data.items():
            discourse = self.lookup_discourse(label)
            if discourse is None:
                continue
            for k, v in d.items():
                if v is None:
                    continue
                pt = self.get_or_create_property_type(k)
                v = str(v)
                prop, _ = get_or_create(self.corpus_context.sql_session, DiscourseProperty,
                                    discourse = discourse, property_type = pt, value = v)

    def get_speaker_property_levels(self, property_type):
        """
        Searches for matching Property matching property_type, gets property levels from that
        Parameters
        ----------
        property_type : str
            the label of the property type
        
          
        Returns
        -------
        list
            list of property levels for property_type
        """
        q = self.corpus_context.sql_session.query(distinct(SpeakerProperty.value))
        q = q.join(PropertyType, SpeakerProperty.property_type_id == PropertyType.id)
        q = q.filter(PropertyType.label == property_type)
        
        return [x[0] for x in q.all()]


    def add_speaker_annotation(self, data):
        """
        Adds per-speaker data to census

        Parameters
        ----------
        data : dict
            the properties to add
            format : {speaker : {property_type : {annotation : value}}}
                    {'speaker1' : {average_duration : {'aa1' : 0.3221, 'sh' : 1.222}}}
        """
        for name, d in data.items():
            speaker = self.lookup_speaker(name)
            if speaker is None:
                continue

            for k, v in d.items():
                if v is None:
                    continue
                pt = self.get_or_create_property_type(k)

                for a, value in v.items():
                    at = self.get_or_create_annotation_type(a)
                    prop, _ = get_or_create(self.corpus_context.sql_session, SpeakerAnnotation, speaker= speaker, \
                    annotation_type = at, property_type = pt, numerical_value = value)

    def get_speaker_annotations(self, property, speaker):
        """
        Searches for matching Property matching property_type spoken by speaker, gets property levels from that
        Parameters
        ----------
        property_type : str
            the label of the property type
        
        Returns
        -------
        list
            list of property levels for property_type
        """
        pt = self.get_property_type(property)
        spk = self.lookup_speaker(speaker)
        q = self.corpus_context.sql_session.query(SpeakerAnnotation).filter(SpeakerAnnotation.property_type_id == pt.id)
        q = q.filter(SpeakerAnnotation.speaker_id == spk.id)

        return {spk.name:{pt.label:{x.annotation_type.label:x.numerical_value for x in q.all()} }}

