from uuid import uuid1

from py2neo import Node, Relationship

from polyglotdb.exceptions import GraphModelError

from .helper import key_for_cypher, value_for_cypher

class BaseAnnotation(object):

    def load(self, id):
        """ raise NotImplementedError"""
        raise(NotImplementedError)

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
        self._id = item.properties['id']
        for x in self._node.labels():
            if x in self.corpus_context.hierarchy:
                self._type = x
                break

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

    def save(self):
        pass


class LinguisticAnnotation(BaseAnnotation):
    def __init__(self, corpus_context = None):
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

        self._preloaded = False

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
        for k,v in self._supers.items():
            v.corpus_context = context
        for k,v in self._subs.items():
            for t in v:
                t.corpus_context = context
        for k,v in self._subannotations.items():
            for t in v:
                t.corpus_context = context

    def __getitem__(self, key):
        return getattr(self, key)

    @property
    def properties(self):
        """ Returns sorted untion of node property keys and type_node property keys """ 
        return sorted(set(self._node.properties.keys()) | set(self._type_node.properties.keys()))

    def __getattr__(self, key):
        if self.corpus_context is None:
            raise(GraphModelError('This object is not bound to a corpus context.'))
        if self._id is None:
            raise(GraphModelError('This object has not been loaded with an id yet.'))
        if key == 'previous':
            if self._previous == 'empty':
                return None
            if self._previous is None:
                res = list(self.corpus_context.execute_cypher(
                    '''MATCH (previous_type)<-[:is_a]-(previous_token)-[:precedes]->(token {id: {id}})
                        RETURN previous_token, previous_type''', id = self._id))
                if len(res) == 0:
                    self._previous = 'empty'
                    return None
                self._previous = LinguisticAnnotation(self.corpus_context)
                self._previous.node = res[0]['previous_token']
                self._previous.type_node = res[0]['previous_type']
            return self._previous
        if key == 'following':
            if self._following == 'empty':
                return None
            if self._following is None:
                res = list(self.corpus_context.execute_cypher(
                    '''MATCH (following_type)<-[:is_a]-(following_token)<-[:precedes]-(token {id: {id}})
                            RETURN following_token, following_type''', id = self._id))
                if len(res) == 0:
                    self._following = 'empty'
                    return None
                self._following = LinguisticAnnotation(self.corpus_context)
                self._following.node = res[0]['following_token']
                self._following.type_node = res[0]['following_type']
            return self._following
        if key == 'speaker':
            if self._speaker == 'empty':
                return None
            if self._speaker is None:
                res = list(self.corpus_context.execute_cypher(
                    '''MATCH (speaker:Speaker)<-[:spoken_by]-(token {id: {id}})
                        RETURN speaker''', id = self._id))
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
                res = list(self.corpus_context.execute_cypher(
                    '''MATCH (discourse:Discourse)<-[:spoken_in]-(token {id: {id}})
                        RETURN discourse''', id = self._id))
                if len(res) == 0:
                    self._discourse = 'empty'
                    return None
                self._discourse = Discourse(self.corpus_context)
                self._discourse.node = res[0]['discourse']
            return self._discourse
        if key in self.corpus_context.hierarchy.get_lower_types(self._type):
            if key not in self._subs:
                res = self.corpus_context.execute_cypher(
                    '''MATCH (lower_type)<-[:is_a]-(lower_token:{a_type})-[:contained_by*1..]->(token {{id: {{id}}}})
                        RETURN lower_token, lower_type ORDER BY lower_token.begin'''.format(a_type = key), id = self._id)
                self._subs[key] = []
                for r in res:
                    a = LinguisticAnnotation(self.corpus_context)
                    a.node = r['lower_token']
                    a.type_node = r['lower_type']
                    self._subs[key].append(a)
            return self._subs[key]
        if key in self.corpus_context.hierarchy.get_higher_types(self._type):
            if key not in self._supers:
                res = list(self.corpus_context.execute_cypher(
                    '''MATCH (higher_type)<-[:is_a]-(higher_token:{a_type})<-[:contained_by*1..]-(token {{id: {{id}}}})
                        RETURN higher_token, higher_type'''.format(a_type = key), id = self._id))
                if len(res) == 0:
                    return None
                a =  LinguisticAnnotation(self.corpus_context)
                a.node = res[0]['higher_token']
                a.type_node = res[0]['higher_type']
                self._supers[key] = a
            return self._supers[key]
        try:
            if key in self.corpus_context.hierarchy.subannotations[self._type]:
                if self._preloaded and key not in self._subannotations:
                    return []
                elif key not in self._subannotations:
                    res = self.corpus_context.execute_cypher(
                        '''MATCH (sub:{a_type})-[:annotates]->(token {{id: {{id}}}})
                            RETURN sub'''.format(a_type = key), id = self._id)

                    self._subannotations[key] = []
                    for r in res:
                        a = SubAnnotation(self.corpus_context)
                        a._annotation = self
                        a.node = r['sub']
                        self._subannotations[key].append(a)
                return self._subannotations[key]
        except KeyError:
            pass
        if key in self._node.properties:
            return self._node.properties[key]
        if key in self._type_node.properties:
            return self._type_node.properties[key]

    def update_properties(self,**kwargs):
        """ 
        updates node properties with kwargs

        Parameters
        ----------
        kwards : dict
            keyword arguments to update properties
        """
        for k,v in kwargs.items():
            if k in self._type_node.properties:
                 self._type_node.update(**{k: v})
            self._node.update(**{k: v})
        if self._node['begin'] > self._node['end']:
            self._node.update(begin = self._node['end'], end = self._node['begin'])

    def save(self):
        """ saves the node to the graph"""
        self.corpus_context.graph.push(self.node)
        for k,v in self._subannotations.items():
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
            '''MATCH (token {id: {id}})-[:is_a]->(type)
                RETURN token, type''', id = id))
        self.node = res[0]['token']
        self.type_node = res[0]['type']

    @property
    def channel(self):
        speaker = self.corpus_context.census[self.speaker.name]
        for x in speaker.discourses:
            if x.discourse.name == self.discourse.name:
                return x.channel
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
            raise(GraphModelError('Can\'t delete a subannotation that doesn\'t belong to this annotation.'))
        subannotation = self._subannotations[subannotation._type].pop(i)

        statement = '''MATCH (n:{type} {{id: {{id}}}}) DETACH DELETE n'''.format(type = subannotation._type)

        self.corpus_context.execute_cypher(statement, id = subannotation.id)

    def add_subannotation(self, type, commit = True, transaction = None, **properties):
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
        if 'begin' not in properties:
            properties['begin'] = self.begin
        if 'end' not in properties:
            properties['end'] = self.end
        properties['id'] = str(uuid1())

        discourse = self.discourse.name

        self.corpus_context.hierarchy.add_subannotation_type(self._type, type)

        if transaction is not None:
            statement = '''MATCH (n:{type}:{corpus}:{discourse} {{id:{{id}}}})
            CREATE (n)<-[:annotates]-(sub:{sub_type}:{corpus}:{discourse} {{{props}}})'''
            props = ['{}: {}'.format(key_for_cypher(k),value_for_cypher(v))
                            for k,v in properties.items()]
            statement = statement.format(type = self.type, sub_type = type,
                            corpus=self.corpus_context.corpus_name,
                            discourse = discourse,props = ', '.join(props))
            transaction.append(statement, id = self._id)
        else:
            to_return = []
            sa = SubAnnotation(self.corpus_context)
            sa._annotation = self
            sa._unsaved = True
            sa._type = type
            sa.node = Node(type, self.corpus_context.corpus_name,
                                discourse, **properties)
            rel = Relationship(sa.node, 'annotates', self.node)

            if commit:
                self.corpus_context.graph.create(sa.node)
                self.corpus_context.graph.create(rel)
            else:
                to_return.append(sa.node)
                to_return.append(rel)

            if type not in self._subannotations:
                self._subannotations[type] = []
            self._subannotations[type].append(sa)
            self._subannotations[type].sort(key = lambda x: x.begin)
            if not commit:
                return to_return

class SubAnnotation(BaseAnnotation):
    def __init__(self, corpus_context = None):
        self._corpus_context = corpus_context
        self._type = None
        self._id = None
        self._node = None
        self._annotation = None

    def __getattr__(self, key):
        if self.corpus_context is None:
            raise(GraphModelError('This object is not bound to a corpus context.'))
        if self._id is None:
            raise(GraphModelError('This object has not been loaded with an id yet.'))
        if key == self._annotation._type:
            return self._annotation
        if key in self._node.properties:
            return self._node.properties[key]
        if key == 'label':
            return None
        raise(AttributeError)

    def update_properties(self,**kwargs):
        """ 
        updates node properties with kwargs

        Parameters
        ----------
        kwards : dict
            keyword arguments to update properties
        """
        self._node.update(**kwargs)
        if self._node['begin'] > self._node['end']:
            self._node.update(begin = self._node['end'], end = self._node['begin'])

    @property
    def node(self):
        """ returns the node"""
        return self._node

    @node.setter
    def node(self, item):
        """ Sets the node to item"""
        self._node = item
        self._id = item.properties['id']
        for x in self._node.labels():
            if x in self.corpus_context.hierarchy.subannotations[self._annotation._type]:
                self._type = x
                break

    def load(self, id):
        """ 
        loads a node from the graph with a specific ID

        Parameters
        ----------
        id : str
            the ID of the desired node
        """
        res = list(self.corpus_context.execute_cypher(
            '''MATCH (sub {id: {id}})-[:annotates]->(token)-[:is_a]->(type)
                RETURN sub, token, type''', id = id))
        self._annotation = LinguisticAnnotation(self.corpus_context)
        self._annotation.node = res[0]['token']
        self._annotation.type_node = res[0]['type']
        self.node = res[0]['sub']

    def save(self):
        """ saves the current node to the graph"""
        self.corpus_context.graph.push(self._node)

class Speaker(SubAnnotation):
    def __init__(self, corpus_context = None):
        self._corpus_context = corpus_context
        self._type = 'Speaker'
        self._id = None
        self._node = None

    def __getattr__(self, key):
        if self.corpus_context is None:
            raise(GraphModelError('This object is not bound to a corpus context.'))
        if key in self._node.properties:
            return self._node.properties[key]
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
        self._id = item.properties['name']

    def load(self, id):
        """ 
        loads a node from the graph with a specific ID

        Parameters
        ----------
        id : str
            the ID of the desired node"""
        res = list(self.corpus_context.execute_cypher(
            '''MATCH (speaker:{a_type} {{id: {{id}}}})
                RETURN speaker'''.format(a_type = self._type), id = id))
        self.node = res[0]['speaker']

class Discourse(Speaker):
    def __init__(self, corpus_context = None):
        self._corpus_context = corpus_context
        self._type = 'Discourse'
        self._id = None
        self._node = None
