from uuid import uuid1
from decimal import Decimal
from polyglotdb.exceptions import GraphModelError

from ..base.helper import value_for_cypher


class BaseAnnotation(object):
    def load(self, id):
        """ raise NotImplementedError"""
        raise (NotImplementedError)

    @property
    def node(self):
        """ returns the BaseAnnotation's node"""
        return self._node

    @node.setter
    def node(self, item):
        """ 
        sets the BaseAnnotation's node

        Parameters
        ----------
        item : 
            the node will be set to item
        """
        self._node = item
        self._id = item['id']
        if self._node['neo4j_label'] in self.corpus_context.hierarchy:
            self._type = self._node['neo4j_label']

    @property
    def duration(self):
        """ returns the duration of annotation """
        return self.end - self.begin

    @property
    def corpus_context(self):
        """returns the corpus context """
        return self._corpus_context

    @corpus_context.setter
    def corpus_context(self, context):
        """
        sets the corpus context to the parameter
        
        Parameters
        ----------
        context : : class: `~polyglotdb.corpus.BaseContext`
            The objects corpus_context will be set to this parameter
        """
        self._corpus_context = context

    def __getitem__(self, key):
        return getattr(self, key)

    def save(self):
        pass


class LinguisticAnnotation(BaseAnnotation):
    def __init__(self, corpus_context=None):
        self._corpus_context = corpus_context
        self._unsaved = False
        self._type = None
        self._node = None
        self._type_node = None

        self._previous = None
        self._following = None
        self._subannotations = {}
        self._id = None
        self._label = None

        self._supers = {}
        self._subs = {}
        self._speaker = None
        self._discourse = None
        self._tracks = {}

        self._preloaded = False

    def __str__(self):
        return '<{} annotation with id: {}>'.format(self._type, self._node['id'])

    @property
    def corpus_context(self):
        return self._corpus_context

    @corpus_context.setter
    def corpus_context(self, context):
        if self._corpus_context == context:
            return
        self._corpus_context = context
        f = self._following
        while True:
            if f is None:
                break
            f.corpus_context = context
            f = f._following
        f = self._previous
        while True:
            if f is None:
                break
            f.corpus_context = context
            f = f._previous
        f = self._speaker
        if f is not None:
            f.corpus_context = context
        f = self._discourse
        if f is not None:
            f.corpus_context = context
        for k, v in self._supers.items():
            v.corpus_context = context
        for k, v in self._subs.items():
            for t in v:
                t.corpus_context = context
        for k, v in self._subannotations.items():
            for t in v:
                t.corpus_context = context

    @property
    def properties(self):
        """ Returns sorted untion of node property keys and type_node property keys """
        return sorted(set(self._node.keys()) | set(self._type_node.keys()))

    def _load_track(self, track_attribute):
        if self._type == 'utterance':
            utt_id = self.id
        else:
            utt_id = self.utterance.id
        results = track_attribute.hydrate(self.corpus_context, utt_id, self.begin, self.end)
        if track_attribute.attribute.relative_time:
            begin = Decimal(self.begin)
            end = Decimal(self.end)
            duration = end - begin
            for p in results:
                p.time = (p.time - begin) / duration

        self._tracks[track_attribute.attribute.label] = results

    @property
    def pitch_track(self):
        if 'pitch' not in self._tracks:
            self._load_track(getattr(getattr(self.corpus_context, self._type), 'pitch'))
        data = self._tracks['pitch']
        return data

    @property
    def waveform(self):
        signal, sr = self.corpus_context.load_waveform(self.discourse.name, 'low_freq', begin=self.begin, end=self.end)
        step = 1 / sr
        data = [{'amplitude': float(p), 'time': i * step + self.begin} for i, p in enumerate(signal)]
        return data

    @property
    def spectrogram(self):
        orig, time_step, freq_step = self.corpus_context.generate_spectrogram(self.discourse.name, 'consonant',
                                                                              begin=self.begin,
                                                                              end=self.end)
        reshaped = []

        for i in range(orig.shape[0]):
            for j in range(orig.shape[1]):
                reshaped.append({'time': j * time_step + self.begin, 'frequency': i * freq_step,
                                 'power': float(orig[i, j])})
        data = {'values': reshaped,
                'time_step': time_step,
                'freq_step': freq_step,
                'num_time_bins': orig.shape[1],
                'num_freq_bins': orig.shape[0]}
        return data

    @property
    def spectrogram_fast(self):
        orig, time_step, freq_step = self.corpus_context.generate_spectrogram(self.discourse.name, 'consonant',
                                                                              begin=self.begin,
                                                                              end=self.end)
        data = {'values': orig,
                'time_step': time_step,
                'freq_step': freq_step,
                'num_time_bins': orig.shape[1],
                'num_freq_bins': orig.shape[0]}
        return data

    def __getattr__(self, key):
        if self.corpus_context is None:
            raise (GraphModelError('This object is not bound to a corpus context.'))
        if self._id is None:
            raise (GraphModelError('This object has not been loaded with an id yet.'))
        if key == self._type:
            return self
        if key == 'current':
            return self
        if key == 'label' and self._type == 'utterance':
            return '{} ({} to {})'.format(self.discourse.name, self.begin, self.end)
        if key == 'previous':
            if self._previous == 'empty':
                return None
            if self._previous is None:
                print('Warning: fetching previous annotation from the database, '
                      'preload this annotation for faster access.')
                res = list(self.corpus_context.execute_cypher(
                    '''MATCH (previous_type)<-[:is_a]-(previous_token)-[:precedes]->(token {id: $id})
                        RETURN previous_token, previous_type''', id=self._id))
                if len(res) == 0:
                    self._previous = 'empty'
                    return None
                self._previous = LinguisticAnnotation(self.corpus_context)
                res[0]['previous_token']['neo4j_label'] = self._type
                self._previous.node = res[0]['previous_token']
                self._previous.type_node = res[0]['previous_type']
            return self._previous
        if key == 'following':
            if self._following == 'empty':
                return None
            if self._following is None:
                print('Warning: fetching following annotation from the database, '
                      'preload this annotation for faster access.')
                res = list(self.corpus_context.execute_cypher(
                    '''MATCH (following_type)<-[:is_a]-(following_token)<-[:precedes]-(token {id: $id})
                            RETURN following_token, following_type''', id=self._id))
                if len(res) == 0:
                    self._following = 'empty'
                    return None
                self._following = LinguisticAnnotation(self.corpus_context)
                res[0]['following_token']['neo4j_label'] = self._type
                self._following.node = res[0]['following_token']
                self._following.type_node = res[0]['following_type']
            return self._following
        if key.startswith('previous'):
            p, key = key.split('_', 1)
            p = self.previous
            if p is None:
                return None
            return getattr(p, key)
        if key.startswith('following'):
            p, key = key.split('_', 1)
            f = self.following
            if f is None:
                return None
            return getattr(f, key)
        if key == 'speaker':
            if self._speaker == 'empty':
                return None
            if self._speaker is None:
                print('Warning: fetching speaker information from the database, '
                      'preload speakers for faster access.')
                res = list(self.corpus_context.execute_cypher(
                    '''MATCH (speaker:Speaker)<-[:spoken_by]-(token {id: $id})
                        RETURN speaker''', id=self._id))
                if len(res) == 0:
                    self._speaker = 'empty'
                    return None
                self._speaker = Speaker(self.corpus_context)
                self._speaker.node = res[0]['speaker']
            return self._speaker
        if key == 'discourse':
            if self._discourse == 'empty':
                return None
            if self._discourse is None:
                print('Warning: fetching discourse information from the database, '
                      'preload discourses for faster access.')
                res = list(self.corpus_context.execute_cypher(
                    '''MATCH (discourse:Discourse)<-[:spoken_in]-(token {id: $id})
                        RETURN discourse''', id=self._id))
                if len(res) == 0:
                    self._discourse = 'empty'
                    return None
                self._discourse = Discourse(self.corpus_context)
                self._discourse.node = res[0]['discourse']
            return self._discourse
        if key in self.corpus_context.hierarchy.get_lower_types(self._type):
            if key not in self._subs:
                print('Warning: fetching {0} information from the database, '
                      'preload {0} annotations for faster access.'.format(key))
                res = self.corpus_context.execute_cypher(
                    '''MATCH (lower_type)<-[:is_a]-(lower_token:{a_type})-[:contained_by*1..]->(token {{id: $id}})
                        RETURN lower_token, lower_type, labels(lower_token) as neo4j_labels ORDER BY lower_token.begin'''.format(a_type=key), id=self._id)
                self._subs[key] = []
                for r in res:
                    a = LinguisticAnnotation(self.corpus_context)
                    labels = r['neo4j_labels']
                    for label in labels:
                        if label in self.corpus_context.hierarchy:
                            r['lower_token']['neo4j_label'] = label
                            break
                    a.node = r['lower_token']
                    a.type_node = r['lower_type']
                    self._subs[key].append(a)
            return self._subs[key]
        if key in self.corpus_context.hierarchy.get_higher_types(self._type):
            if key not in self._supers:
                print('Warning: fetching {0} information from the database, '
                      'preload {0} annotations for faster access.'.format(key))
                res = list(self.corpus_context.execute_cypher(
                    '''MATCH (higher_type)<-[:is_a]-(higher_token:{a_type})<-[:contained_by*1..]-(token {{id: $id}})
                        RETURN higher_token, higher_type, labels(higher_token) as neo4j_labels'''.format(a_type=key), id=self._id))
                if len(res) == 0:
                    return None
                a = LinguisticAnnotation(self.corpus_context)
                labels = res[0]['neo4j_labels']
                for label in labels:
                    if label in self.corpus_context.hierarchy:
                        res[0]['higher_token']['neo4j_label'] = label
                        break
                a.node = res[0]['higher_token']
                a.type_node = res[0]['higher_type']
                self._supers[key] = a
            return self._supers[key]
        try:
            if key in self.corpus_context.hierarchy.subannotations[self._type]:
                if self._preloaded and key not in self._subannotations:
                    return []
                elif key not in self._subannotations:
                    print('Warning: fetching {0} information from the database, '
                          'preload {0} annotations for faster access.'.format(key))
                    res = self.corpus_context.execute_cypher(
                        '''MATCH (sub:{a_type})-[:annotates]->(token {{id: $id}})
                            RETURN sub'''.format(a_type=key), id=self._id)

                    self._subannotations[key] = []
                    for r in res:
                        a = SubAnnotation(self.corpus_context)
                        a._annotation = self
                        a.node = r['sub']
                        self._subannotations[key].append(a)
                return self._subannotations[key]
        except KeyError:
            pass
        if key == 'duration':
            return self.end - self.begin
        if key in self._node.keys():
            return self._node[key]
        if key in self._type_node.keys():
            return self._type_node[key]

    def update_properties(self, **kwargs):
        """ 
        updates node properties with kwargs

        Parameters
        ----------
        kwards : dict
            keyword arguments to update properties
        """
        for k, v in kwargs.items():
            if k in self._type_node.keys():
                self._type_node._update({k: v})
            self._node._update({k: v})
        if self._node['begin'] > self._node['end']:
            self._node._update({}, begin=self._node['end'], end=self._node['begin'])
        self._unsaved = True

    def save(self):
        """ saves the node to the graph"""
        if self._unsaved:
            props = {k: v for k, v in self.node.items() if k != 'id'}
            prop_string = ',\n'.join(['n.{} = {}'.format(k, value_for_cypher(v)) for k, v in props.items()])
            statement = '''MATCH (n:{corpus_name}:{type}) WHERE n.id = $id
                        SET {prop_string}'''.format(corpus_name=self.corpus_context.cypher_safe_name,
                                                    type=self._type, prop_string=prop_string)
            self.corpus_context.execute_cypher(statement, id=self._id)
        for k, v in self._subannotations.items():
            for s in v:
                s.save()

    def load(self, id):
        """ 
        loads a node from the graph with a specific ID

        Parameters
        ----------
        id : str
            the ID of the desired node
        """
        res = list(self.corpus_context.execute_cypher(
            '''MATCH (token {id: $id})-[:is_a]->(type)
                RETURN token, type, labels(token) as neo4j_labels''', id=id))
        labels = res[0]['neo4j_labels']
        for label in labels:
            if label in self.corpus_context.hierarchy:
                res[0]['token']['neo4j_label'] = label
                break
        self.node = res[0]['token']
        self.type_node = res[0]['type']

    @property
    def channel(self):
        statement = '''MATCH (s:Speaker:{corpus_name})-[r:speaks_in]->(d:Discourse:{corpus_name})
        WHERE s.name = $speaker_name and d.name = $discourse_name
        RETURN r.channel as channel'''.format(corpus_name=self.corpus_context.cypher_safe_name)
        results = self.corpus_context.execute_cypher(statement, speaker_name=self.speaker.name,
                                                     discourse_name=self.discourse.name)
        for r in results:
            return r['channel']
        return None

    @property
    def type_node(self):
        """ returns the node type """
        return self._type_node

    @type_node.setter
    def type_node(self, item):
        """ sets the node type to item """
        self._type_node = item

    def delete_subannotation(self, subannotation):
        """
        Deletes a subannotation from the graph
        
        Parameters
        ----------
        subannotation : :class: `~polyglotdb.graph.SubAnnotation`
            the subannotation to be deleted
         """
        for i, sa in enumerate(self._subannotations[subannotation._type]):
            if sa.id == subannotation.id:
                break
        else:
            raise (GraphModelError('Can\'t delete a subannotation that doesn\'t belong to this annotation.'))
        subannotation = self._subannotations[subannotation._type].pop(i)

        statement = '''MATCH (n:{type} {{id: $id}}) DETACH DELETE n'''.format(type=subannotation._type)

        self.corpus_context.execute_cypher(statement, id=subannotation.id)

    def add_subannotation(self, type, commit=True, transaction=None, **properties):
        """
        Adds a subannotation to the graph

        Parameters
        ----------
        type : str
            the type of the subannotation

        commit : boolean, defaults to False

        transaction :  , defaults to None

        properties : dict
        """
        # if 'begin' not in properties:
        #    properties['begin'] = self.begin
        # if 'end' not in properties:
        #    properties['end'] = self.end
        properties['id'] = str(uuid1())
        properties['type'] = type
        discourse = self.discourse.name
        statement = '''MATCH (n:{type}:{corpus} {{id:$a_id}})
        CREATE (n)<-[r:annotates]-(sub:{sub_type}:{corpus})
        WITH sub, r
        SET {props}
        return sub, r'''
        props = []
        for k, v in properties.items():
            props.append('sub.%s = $%s' % (k, k))
            if self._corpus_context.hierarchy.has_subannotation_property(type, k):
                for name, t in self._corpus_context.hierarchy.subannotation_properties[type]:
                    if name == k:
                        properties[k] = t(v)
        statement = statement.format(type=self._type, sub_type=type,
                                     corpus=self.corpus_context.cypher_safe_name, props=', '.join(props))

        if transaction is not None:
            transaction.append(statement, a_id=self._id, **properties)
        else:
            sa = SubAnnotation(self.corpus_context)
            sa._annotation = self
            sa._type = type
            res = self.corpus_context.execute_cypher(statement, a_id=self._id, **properties)[0]
            sa.node = res['sub']
            rel = res['r']

            if type not in self._subannotations:
                self._subannotations[type] = []
            self._subannotations[type].append(sa)
            # self._subannotations[type].sort(key=lambda x: x.begin)
            return sa.node, rel


class SubAnnotation(BaseAnnotation):
    def __init__(self, corpus_context=None):
        self._corpus_context = corpus_context
        self._type = None
        self._id = None
        self._node = None
        self._annotation = None
        self._unsaved = False

    def __getattr__(self, key):
        if self.corpus_context is None:
            raise (GraphModelError('This object is not bound to a corpus context.'))
        if self._id is None:
            raise (GraphModelError('This object has not been loaded with an id yet.'))
        if key == self._annotation._type:
            return self._annotation
        if key in self._node.keys():
            return self._node[key]
        if key == 'label':
            return None
        if not self._corpus_context.hierarchy.has_subannotation_property(self._type, key):
            raise AttributeError
        return None

    def update_properties(self, **kwargs):
        """ 
        updates node properties with kwargs

        Parameters
        ----------
        kwards : dict
            keyword arguments to update properties
        """
        self._node.update(kwargs)
        if self._node['begin'] > self._node['end']:
            self._node.update({}, begin=self._node['end'], end=self._node['begin'])
        self._unsaved = True

    @property
    def node(self):
        """ returns the node"""
        return self._node

    @node.setter
    def node(self, item):
        """ Sets the node to item"""
        self._node = item
        self._id = item['id']
        if self._annotation._type in self.corpus_context.hierarchy.subannotations and self._node['type'] in \
                self.corpus_context.hierarchy.subannotations[self._annotation._type]:
            self._type = self._node['type']

    def load(self, id):
        """ 
        loads a node from the graph with a specific ID

        Parameters
        ----------
        id : str
            the ID of the desired node
        """
        res = list(self.corpus_context.execute_cypher(
            '''MATCH (sub {id: $id})-[:annotates]->(token)-[:is_a]->(type)
                RETURN sub, token, type, labels(token) as neo4j_labels, labels(sub) as sub_neo4j_labels''', id=id))
        self._annotation = LinguisticAnnotation(self.corpus_context)
        labels = res[0]['neo4j_labels']
        for label in labels:
            if label in self.corpus_context.hierarchy:
                res[0]['token']['neo4j_label'] = label
                break
        self._annotation.node = res[0]['token']
        self._annotation.type_node = res[0]['type']
        labels = res[0]['sub_neo4j_labels']
        for x in labels:
            if self._annotation._type in self.corpus_context.hierarchy.subannotations and x in \
                    self.corpus_context.hierarchy.subannotations[self._annotation._type]:
                res[0]['sub']['neo4j_label'] = x
                break
        self.node = res[0]['sub']

    def save(self):
        """ saves the current node to the graph"""
        if self._unsaved:
            props = {k: v for k, v in self.node.items() if k != 'id'}
            prop_string = ',\n'.join(['n.{} = {}'.format(k, value_for_cypher(v)) for k, v in props.items()])
            statement = '''MATCH (n:{corpus_name}:{type}) WHERE n.id = $id
                        SET {prop_string}'''.format(corpus_name=self.corpus_context.cypher_safe_name,
                                                    type=self._type, prop_string=prop_string)
            self.corpus_context.execute_cypher(statement, id=self._id)


class Speaker(SubAnnotation):
    def __init__(self, corpus_context=None):
        self._corpus_context = corpus_context
        self._type = 'Speaker'
        self._id = None
        self._node = None

    def __getattr__(self, key):
        if self.corpus_context is None:
            raise (GraphModelError('This object is not bound to a corpus context.'))
        if key in self._node.keys():
            return self._node[key]
        return None

    @property
    def node(self):
        """ returns the SubAnnotations's node"""
        return self._node

    @node.setter
    def node(self, item):
        """ 
        sets the SubAnnotation's node

        Parameters
        ----------
        item : 
            the node will be set to item
        """
        self._node = item
        self._id = item['name']

    def load(self, id):
        """ 
        loads a node from the graph with a specific ID

        Parameters
        ----------
        id : str
            the ID of the desired node"""
        res = list(self.corpus_context.execute_cypher(
            '''MATCH (speaker:{a_type} {{id: $id}})
                RETURN speaker'''.format(a_type=self._type), id=id))
        self.node = res[0]['speaker']


class Discourse(Speaker):
    def __init__(self, corpus_context=None):
        self._corpus_context = corpus_context
        self._type = 'Discourse'
        self._id = None
        self._node = None
