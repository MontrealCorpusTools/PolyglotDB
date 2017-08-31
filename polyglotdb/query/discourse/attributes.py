from ..base import NodeAttribute, Node, CollectionAttribute, CollectionNode
from ...exceptions import SpeakerAttributeError, DiscourseAttributeError


class DiscourseAttribute(NodeAttribute):
    def __init__(self, node, label):
        super(DiscourseAttribute, self).__init__(node, label)

    def __repr__(self):
        return '<DiscourseAttribute "{}">'.format(str(self))


class DiscourseNode(Node):
    def __init__(self, corpus=None, hierarchy=None):
        super(DiscourseNode, self). __init__('Discourse', corpus, hierarchy)

    def __repr__(self):
        return '<DiscourseNode "{}">'.format(str(self))

    def __getattr__(self, key):
        if key == 'speakers':
            return SpeakerCollectionNode(self)
        if not self.hierarchy.has_discourse_property(key):
            properties = [x[0] for x in self.hierarchy.discourse_properties]
            raise DiscourseAttributeError(
                'Discourses do not have a \'{}\' property (available: {}).'.format(key, ', '.join(properties)))
        return DiscourseAttribute(self, key)


class SpeakerNode(Node):
    def __init__(self, corpus=None, hierarchy=None):
        super(SpeakerNode, self). __init__('Speaker', corpus, hierarchy)

    def __repr__(self):
        return '<SpeakerNode "{}">'.format(str(self))


class SpeakerCollectionNode(CollectionNode):
    non_optional = True
    subquery_match_template = '''({anchor_node_alias})<-[speaks:speaks_in]-({def_collection_alias})'''

    def __repr__(self):
        return '<SpeakerCollectionNode "{}">'.format(str(self))

    def __init__(self, discourse_node):
        s = SpeakerNode(discourse_node.corpus, discourse_node.hierarchy)
        super(SpeakerCollectionNode, self). __init__(discourse_node, s)

    @property
    def speaks_in_alias(self):
        return 'speaks'

    @property
    def with_pre_collection(self):
        return ', '.join([self.speaks_in_alias])

    def with_statement(self):
        withs = [self.collect_template.format(a=self.collection_alias),
                 self.collect_template.format(a=self.speaks_in_alias)
                 ]
        return ', '.join(withs)

    @property
    def withs(self):
        withs = [self.collection_alias, self.speaks_in_alias]
        return withs

    def __getattr__(self, key):
        if key.startswith('channel'):
            return ChannelAttribute(self)
        if not self.hierarchy.has_speaker_property(key):
            properties = [x[0] for x in self.hierarchy.speaker_properties]
            raise SpeakerAttributeError(
                'Speakers do not have a \'{}\' property (available: {}).'.format(key, ', '.join(properties)))
        return CollectionAttribute(self, key)

    @property
    def collection_alias(self):
        return self.collected_node.alias

    @property
    def def_collection_alias(self):
        return self.collected_node.alias

class ChannelAttribute(CollectionAttribute):
    def __init__(self, node):
        super(ChannelAttribute, self).__init__(node, 'channel')

    def __repr__(self):
        return '<ChannelAttribute "{}">'.format(str(self))

    def for_cypher(self):
        return '{}.{}'.format(self.node.speaks_in_alias, 'channel')

    def for_return(self):
        return self.return_template.format(alias=self.node.speaks_in_alias, property=self.label)
