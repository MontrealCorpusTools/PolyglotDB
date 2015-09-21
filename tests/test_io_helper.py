
from annograph.io.helper import parse_transcription, AnnotationType


def test_parse_transcription():
    delimited_at = AnnotationType('test', None, None)
    delimited_at.delimiter = '.'

    assert(parse_transcription('a.t', delimited_at) == ['a','t'])
    assert(parse_transcription('ae.t', delimited_at) == ['ae','t'])
    assert(parse_transcription('a1.t', delimited_at) == ['a1','t'])

    digraph_at = AnnotationType('test', None, None)

    digraph_at.digraphs = set(['ae'])
    assert(parse_transcription('aet', digraph_at) == ['ae','t'])
    assert(parse_transcription('ae', digraph_at) == ['ae'])
    assert(parse_transcription('et', digraph_at) == ['e','t'])

    regular = AnnotationType('test', None, None)
    assert(parse_transcription('aet', regular) == ['a','e','t'])
    assert(parse_transcription('a.et', regular) == ['a','.','e','t'])

    ignored = AnnotationType('test', None, None)
    ignored.ignored_characters = set('.')
    assert(parse_transcription('aet', ignored) == ['a','e','t'])
    assert(parse_transcription('a.et', ignored) == ['a','e','t'])
