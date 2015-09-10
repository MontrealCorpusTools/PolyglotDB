import re
import operator
import sqlalchemy, sqlalchemy.orm
from sqlalchemy import create_engine, func
from sqlalchemy.orm import joinedload, aliased
from sqlalchemy.sql.expression import and_

from .db import (Base, Discourse, Node, Edge, generate_edge_class, AnnotationType, Annotation,
                            AnnotationFrequencies, AnnotationAttributes, AnnotationSubarcs)

from .config import Session, session_scope


class Attribute(object):
    """
    Attributes are for collecting summary information about attributes of
    Words or WordTokens, with different types of attributes allowing for
    different behaviour

    Parameters
    ----------
    name : str
        Python-safe name for using `getattr` and `setattr` on Words and
        WordTokens

    att_type : str
        Either 'spelling', 'tier', 'numeric' or 'factor'

    display_name : str
        Human-readable name of the Attribute, defaults to None

    default_value : object
        Default value for initializing the attribute

    Attributes
    ----------
    name : string
        Python-readable name for the Attribute on Word and WordToken objects

    display_name : string
        Human-readable name for the Attribute

    default_value : object
        Default value for the Attribute.  The type of `default_value` is
        dependent on the attribute type.  Numeric Attributes have a float
        default value.  Factor and Spelling Attributes have a string
        default value.  Tier Attributes have a Transcription default value.

    range : object
        Range of the Attribute, type depends on the attribute type.  Numeric
        Attributes have a tuple of floats for the range for the minimum
        and maximum.  The range for Factor Attributes is a set of all
        factor levels.  The range for Tier Attributes is the set of segments
        in that tier across the corpus.  The range for Spelling Attributes
        is None.
    """
    ATT_TYPES = ['spelling', 'tier', 'numeric', 'factor']
    def __init__(self, name, att_type, display_name = None, default_value = None):
        self.name = name
        self.att_type = att_type
        self._display_name = display_name

        if self.att_type == 'numeric':
            self._range = [0,0]
            if default_value is not None and isinstance(default_value,(int,float)):
                self._default_value = default_value
            else:
                self._default_value = 0
        elif self.att_type == 'factor':
            if default_value is not None and isinstance(default_value,str):
                self._default_value = default_value
            else:
                self._default_value = ''
            if default_value:
                self._range = set([default_value])
            else:
                self._range = set()
        elif self.att_type == 'spelling':
            self._range = None
            if default_value is not None and isinstance(default_value,str):
                self._default_value = default_value
            else:
                self._default_value = ''
        elif self.att_type == 'tier':
            self._range = set()
            self._delim = None
            if default_value is not None:
                self._default_value = default_value
            else:
                self._default_value = []

    @property
    def delimiter(self):
        if self.att_type != 'tier':
            return None
        else:
            return self._delim

    @delimiter.setter
    def delimiter(self, value):
        self._delim = value

    @staticmethod
    def guess_type(values, trans_delimiters = None):
        if trans_delimiters is None:
            trans_delimiters = ['.',' ', ';', ',']
        probable_values = {x: 0 for x in Attribute.ATT_TYPES}
        for i,v in enumerate(values):
            try:
                t = float(v)
                probable_values['numeric'] += 1
                continue
            except ValueError:
                for d in trans_delimiters:
                    if d in v:
                        probable_values['tier'] += 1
                        break
                else:
                    if v in [v2 for j,v2 in enumerate(values) if i != j]:
                        probable_values['factor'] += 1
                    else:
                        probable_values['spelling'] += 1
        return max(probable_values.items(), key=operator.itemgetter(1))[0]

    @staticmethod
    def sanitize_name(name):
        """
        Sanitize a display name into a Python-readable attribute name

        Parameters
        ----------
        name : string
            Display name to sanitize

        Returns
        -------
        string
            Sanitized name
        """
        return re.sub('\W','',name.lower())

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.display_name

    def __eq__(self,other):
        if isinstance(other,Attribute):
            if self.name == other.name:
                return True
        if isinstance(other,str):
            if self.name == other:
                return True
        return False

    @property
    def display_name(self):
        if self._display_name is not None:
            return self._display_name
        return self.name.title()

    @property
    def default_value(self):
        return self._default_value

    @default_value.setter
    def default_value(self, value):
        self._default_value = value
        self._range = set([value])

    @property
    def range(self):
        return self._range

    def update_range(self,value):
        """
        Update the range of the Attribute with the value specified.
        If the attribute is a Factor, the value is added to the set of levels.
        If the attribute is Numeric, the value expands the minimum and
        maximum values, if applicable.  If the attribute is a Tier, the
        value (a segment) is added to the set of segments allowed. If
        the attribute is Spelling, nothing is done.

        Parameters
        ----------
        value : object
            Value to update range with, the type depends on the attribute
            type
        """
        if value is None:
            return
        if self.att_type == 'numeric':
            if isinstance(value, str):
                try:
                    value = float(value)
                except ValueError:
                    self.att_type = 'spelling'
                    self._range = None
                    return
            if value < self._range[0]:
                self._range[0] = value
            elif value > self._range[1]:
                self._range[1] = value
        elif self.att_type == 'factor':
            self._range.add(value)
            #if len(self._range) > 1000:
            #    self.att_type = 'spelling'
            #    self._range = None
        elif self.att_type == 'tier':
            if isinstance(self._range, list):
                self._range = set(self._range)
            self._range.update([x for x in value])

class Word(object):
    pass

class Environment(object):
    pass

class Corpus(object):
    """
    Basic corpus object that has information about the SQL database
    and serves as an abstraction layer between the SQL representations
    and Python usage.

    Parameters
    ----------
    engine_string : str
        String specifying the url of the database to use, such as 'sqlite:///dev.db'

    """

    def __init__(self, engine_string, **kwargs):
        self.engine_string = engine_string
        self.engine = create_engine(self.engine_string)
        Session.configure(bind=self.engine)

        self.column_mapping = kwargs
        self.lexicon_only = False

    def initial_setup(self):
        """
        Clears the current database and sets up the various tables needed.
        This function should only be called once.
        """
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def _type(self, session, name):
        q = session.query(AnnotationType)
        if name in self.column_mapping:
            q = q.filter(AnnotationType.type_label == self.column_mapping[name])
        else:
            q = q.filter(AnnotationType.type_label.ilike(name))
        return q.first()

    def _wordtype(self, session):
        q = session.query(AnnotationType)
        if 'word' in self.column_mapping:
            q = q.filter(AnnotationType.type_label == self.column_mapping['word'])
        else:
            q = q.filter(AnnotationType.type_label.ilike("word") |
                        AnnotationType.type_label.ilike("orthography"))
        return q.first()

    def find(self, orthography):
        with session_scope() as session:
            t = self._wordtype(session)
            if t is None:
                return
            q = session.query(Edge).options(joinedload('*'))
            q = q.join(Edge.type)
            q = q.join(Edge.annotation)
            q = q.filter(AnnotationType.type_id == t.type_id)
            q = q.filter(Annotation.annotation_label.ilike(orthography))
            return q.first()

    def _find(self, session, key, type):
        t = self._type(session, type)
        if t is None:
            return
        q = session.query(Edge).options(joinedload('*'))
        q = q.join(Edge.type)
        q = q.join(Edge.annotation)
        q = q.filter(AnnotationType.type_id == t.type_id)
        q = q.filter(Annotation.annotation_label.ilike(key))
        return q.all()

    def _get_transitive_closures(self, higher_type, lower_type):
        with session_scope() as session:
            subarcs = session.query(
                                Edge.type_id.label('type_id'),
                                Edge.source_id.label('source_id'),
                                Edge.target_id.label('target_id'),
                                Edge.annotation_id.label('annotation_id')).\
                                join(Edge.annotation).\
                                join(Edge.type).\
                                filter(AnnotationType.type_label == lower_type).\
                                add_columns(Annotation.annotation_label.concat('.').label(lower_type)).\
                                cte("subarcs", recursive = True)
            subarc_alias = aliased(subarcs, name="s")
            edge_alias = aliased(Edge, name='e')
            subarcs = subarcs.union_all(
                      session.query(
                                edge_alias.type_id.label('type_id'),
                                subarc_alias.c.source_id.label('source_id'),
                                edge_alias.target_id.label('target_id'),
                                edge_alias.target_id.label('annotation_id')).\
                      join(subarc_alias, edge_alias.source_id == subarc_alias.c.target_id).\
                      join(edge_alias.annotation).\
                      join(edge_alias.type).\
                      filter(AnnotationType.type_label == lower_type).\
                      add_columns(getattr(subarc_alias.c, lower_type).\
                                    concat(Annotation.annotation_label).concat('.').\
                                    label(lower_type)
                                    )
                    )
            q = session.query(Edge.annotation_id, Edge.type_id.label('higher_type_id'),).\
                            join(Edge.type).\
                            join(subarcs, and_(subarcs.c.target_id == Edge.target_id, \
                                            subarcs.c.source_id == Edge.source_id)).\
                            add_columns(subarcs.c.type_id.label('lower_type_id'),getattr(subarcs.c, lower_type))
            q = q.filter(AnnotationType.type_label == higher_type).distinct()
            for row in q.all():
                #e, count = row
                r = AnnotationSubarcs(annotation_id = row[0],
                                            higher_type_id = row[1],
                                            lower_type_id = row[2],
                                            subarc = row[3])
                session.add(r)
            session.flush()


    def get_wordlist(self):
        with session_scope() as session:
            wt = self._wordtype(session)
            pt = self._type(session, 'phone')
            #print(Edge.phone.expression)
            #subarcs = self._get_transitive_closures(session, 'word', 'phone')
            q = session.query(Annotation.annotation_label,
                    AnnotationFrequencies.frequency).options(joinedload('*'))
            q = q.join(Edge, Edge.annotation_id == Annotation.annotation_id)
            q = q.join(AnnotationFrequencies,
                        Annotation.annotation_id == AnnotationFrequencies.annotation_id)
            q = q.join(AnnotationSubarcs, and_(AnnotationSubarcs.annotation_id == Annotation.annotation_id,
                                            AnnotationSubarcs.higher_types == wt))
            q = q.filter(Edge.type_id == wt.type_id)
            q = q.filter(AnnotationSubarcs.lower_types == pt)
            q = q.add_columns(AnnotationSubarcs.subarc)
            q = q.distinct()

            results = q.all()
        return results

    def _generate_frequency_table(self):
        if self.lexicon_only:
            return

        with session_scope() as session:
            q = session.query(AnnotationFrequencies)
            q.delete()
            session.flush()

            q = session.query(Edge, func.count(Edge.annotation_id))
            q = q.join(Edge.type)
            q = q.join(Edge.annotation)
            q = q.group_by(Edge.annotation_id, Edge.type_id)
            for row in q.all():
                e, count = row
                r = AnnotationFrequencies(annotation = e.annotation,
                                            type = e.type,
                                            frequency = count)
                session.add(r)
            session.flush()

    def get_edge_labels(self):
        labels = dict()
        with session_scope() as session:
            q = session.query(Edge)
            q = q.join(Edge.type)
            q = q.join(Edge.annotation)
            for e in q.all():
                if str(e.type) not in labels:
                    labels[str(e.type)] = dict()
                labels[str(e.type)][e.source_id,e.target_id] = '{}/{}'.format(str(e.type),str(e.annotation))
        return labels


