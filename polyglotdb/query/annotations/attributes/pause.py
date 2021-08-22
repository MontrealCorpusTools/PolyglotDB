from .base import AnnotationNode, AnnotationAttribute, key_for_cypher, AnnotationCollectionNode, \
    AnnotationCollectionAttribute


class PauseAnnotation(AnnotationNode):
    def __init__(self, corpus, hierarchy):
        super(PauseAnnotation, self).__init__('word', corpus, hierarchy)
        self.subset_labels = ['pause']

    def __repr__(self):
        return '<PauseAnnotation \'{}\'>'.format(str(self))

    def __getattr__(self, key):
        if key == 'speaker':
            from .speaker import SpeakerAnnotation
            return SpeakerAnnotation(self)
        elif key == 'discourse':
            from .discourse import DiscourseAnnotation
            return DiscourseAnnotation(self)
        return PauseAttribute(self, key)

    @property
    def define_alias(self):
        """ Returns a cypher string for getting all token_labels"""
        label_string = ':{}:pause'.format(self.node_type)
        label_string += ':{}'.format(key_for_cypher(self.corpus))
        return '{}{}'.format(self.alias, label_string)

    @property
    def key(self):
        """Returns 'pause' """
        return 'pause'


class PauseAttribute(AnnotationAttribute):
    def __repr__(self):
        return '<PauseAttribute \'{}\'>'.format(str(self))


class NearPauseAttribute(PauseAttribute):
    def __init__(self, node):
        self.node = node

    def __repr__(self):
        return '<NearPauseAttribute \'{}\'>'.format(str(self))


class FollowsPauseAttribute(NearPauseAttribute):
    def __eq__(self, other):
        if not isinstance(other, bool):
            raise (ValueError('Value must be a boolean for follows_pause.'))
        from ..elements import FollowsPauseClauseElement, NotFollowsPauseClauseElement
        if other:
            return FollowsPauseClauseElement(self.node)
        else:
            return NotFollowsPauseClauseElement(self.node)

    def __repr__(self):
        return '<FollowsPauseAttribute \'{}\'>'.format(str(self))


class PrecedesPauseAttribute(NearPauseAttribute):
    def __eq__(self, other):
        if not isinstance(other, bool):
            raise (ValueError('Value must be a boolean for precedes_pause.'))
        from ..elements import PrecedesPauseClauseElement, NotPrecedesPauseClauseElement
        if other:
            return PrecedesPauseClauseElement(self.node)
        else:
            return NotPrecedesPauseClauseElement(self.node)

    def __repr__(self):
        return '<PrecedesPauseAttribute \'{}\'>'.format(str(self))


class FollowingPauseAnnotation(AnnotationCollectionNode):
    has_subquery = True
    path_prefix = 'path_'

    subquery_match_template = '''{collection_alias} = ({anchor_alias})-[:precedes_pause*0..]->(:speech:word)'''
    subquery_template = '''{optional}MATCH {for_match}
        WHERE NONE (x in nodes({collection_alias})[1..-1] where x:speech)
         AND size(nodes({collection_alias})[1..-1]) > 0
        WITH {output_with_string}'''
    collect_template = 'collect({a}) as {a}'

    def __str__(self):
        return self.key

    def __lt__(self, other):
        return False

    def __repr__(self):
        return '<FollowingPauseAnnotation \'{}\'>'.format(str(self))

    def __init__(self, anchor_node):
        self.anchor_node = anchor_node

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        if not isinstance(other, FollowingPauseAnnotation):
            return False
        return True

    @property
    def nodes(self):
        return [self] + self.anchor_node.nodes

    @property
    def withs(self):
        withs = [self.collection_alias]
        return withs

    def subquery(self, withs, filters=None, optional=False):
        """Generates a subquery given a list of alias and type_alias """
        input_with = ', '.join(withs)
        new_withs = withs - {self.collection_alias}
        output_with = ', '.join(new_withs) + ', ' + self.with_statement()

        where_string = ''
        if filters is not None:
            relevant = []
            for c in filters:
                if c.involves(self):
                    relevant.append(c.for_cypher())
            if relevant:
                where_string = 'WHERE ' + '\nAND '.join(relevant)
        for_match = self.subquery_match_template.format(anchor_alias=self.anchor_node.alias,
                                                        collection_alias=self.collection_alias)
        kwargs = {'for_match': for_match,
                  'optional': '',
                  'collection_alias': self.collection_alias,
                  'output_with_string': output_with}
        if optional:
            kwargs['optional'] = 'OPTIONAL '
        return self.subquery_template.format(**kwargs)

    def with_statement(self):
        return 'nodes({alias})[1..-1] as {alias}'.format(alias=self.collection_alias)

    @property
    def key(self):
        return 'pause_following_{}'.format(self.anchor_node.key)

    def __getattr__(self, key):
        return PausePathAttribute(self, key)

    @property
    def collection_alias(self):
        return key_for_cypher(self.key)

    alias = collection_alias


class PreviousPauseAnnotation(FollowingPauseAnnotation):
    subquery_match_template = '''{collection_alias} = (:speech:word)-[:precedes_pause*0..]->({anchor_alias})'''

    @property
    def key(self):
        """ Returns 'pause'"""
        return 'pause_preceding_{}'.format(self.anchor_node.key)


class PausePathAttribute(AnnotationCollectionAttribute):
    duration_filter_template = '[n in nodes({alias})[-1..]| n.end][0] - [n in nodes({alias})[0..1]| n.begin][0]'
    duration_return_template = '[n in {alias}[-1..]| n.end][0] - [n in {alias}[0..1]| n.begin][0]'
    filter_template = '[n in nodes({alias})|n.{property}]'

    def for_filter(self):
        if self.label == 'duration':
            return self.duration_filter_template.format(alias=self.node.collection_alias)
        return self.filter_template.format(alias=self.node.collection_alias, property=self.label)

    def for_return(self):
        if self.label == 'duration':
            return self.duration_return_template.format(alias=self.node.collection_alias)
        return self.return_template.format(alias=self.node.collection_alias, property=self.label)

    def __repr__(self):
        return '<PausePathAttribute \'{}\'>'.format(str(self))
