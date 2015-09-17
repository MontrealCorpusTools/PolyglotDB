import os
import re
import shutil
from py2neo import Graph


from annograph.io.graph import data_to_graph_csvs

from annograph.graph.query import GraphQuery

class CorpusContext(object):
    def __init__(self, user, password, corpus_name, host = 'localhost', port = 7474):
        self.graph = Graph("http://{}:{}@{}:{}/db/data/".format(user, password, host, port))
        self.corpus_name = corpus_name
        self.base_dir = os.path.join(os.path.expanduser('~/Documents/SCT'), self.corpus_name)

        self.log_dir = os.path.join(self.base_dir, 'logs')
        os.makedirs(self.log_dir, exist_ok = True)

        self.temp_dir = os.path.join(self.base_dir, 'temp')
        os.makedirs(self.temp_dir, exist_ok = True)

        self.data_dir = os.path.join(self.base_dir, 'data')
        os.makedirs(self.data_dir, exist_ok = True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        if exc_type is None:
            shutil.rmtree(self.temp_dir)
            return True

    def reset_graph(self):
        self.graph.delete_all()

    def remove_discourse(self, name):
        pass

    def query(self, annotation_type):
        return GraphQuery(self, annotation_type)

    def import_csvs(self, name, annotation_types):
        node_path = 'file:{}'.format(os.path.join(self.temp_dir, '{}_nodes.csv'.format(name)).replace('\\','/'))

        node_import_statement = '''LOAD CSV WITH HEADERS FROM "%s" AS csvLine
CREATE (n:Anchor { id: toInt(csvLine.id),
time: toFloat(csvLine.time), label: csvLine.label, corpus: csvLine.corpus,
discourse: csvLine.discourse })'''
        self.graph.cypher.execute(node_import_statement % node_path)
        self.graph.cypher.execute('CREATE INDEX ON :Anchor(corpus)')
        self.graph.cypher.execute('CREATE INDEX ON :Anchor(discourse)')
        self.graph.cypher.execute('CREATE CONSTRAINT ON (node:Anchor) ASSERT node.id IS UNIQUE')
        self.graph.cypher.execute('CREATE CONSTRAINT ON (node:Anchor) ASSERT node.label IS UNIQUE')

        for at in annotation_types:
            rel_path = 'file:{}'.format(os.path.join(self.temp_dir, '{}_{}.csv'.format(name, at)).replace('\\','/'))
            rel_import_statement = '''USING PERIODIC COMMIT 1000
    LOAD CSV WITH HEADERS FROM "%s" AS csvLine
    MATCH (begin_node:Anchor { id: toInt(csvLine.from_id)}),(end_node:Anchor { id: toInt(csvLine.to_id)})
    CREATE (begin_node)-[:%s { label: csvLine.label, id: csvLine.id }]->(end_node)'''
            self.graph.cypher.execute(rel_import_statement % (rel_path,at))
            self.graph.cypher.execute('CREATE INDEX ON :%s(label)' % at)
        self.graph.cypher.execute('DROP CONSTRAINT ON (node:Anchor) ASSERT node.id IS UNIQUE')
        self.graph.cypher.execute('''MATCH (n)
                                    WHERE n:Anchor
                                    REMOVE n.id''')

    def add_discourse(self, data):
        data.corpus_name = self.corpus_name
        data_to_graph_csvs(data, self.temp_dir)
        self.import_csvs(data.name, data.types)

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
