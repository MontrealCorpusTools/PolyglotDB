
# Base exception classes


class PGError(Exception):
    """
    Base class for all exceptions explicitly raised in PolyglotDB.
    """

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return '{}: {}'.format(type(self).__name__, self.value)

    def __str__(self):
        return self.value


# Context Manager exceptions

class PGContextError(PGError):
    """
    Exception class for when context managers should be used and aren't.
    """
    pass


# Corpus loading exceptions

class ParseError(PGError):
    """
    Exception class for parsing errors
    """
    pass


class PGOSError(PGError):
    """
    Exception class for when files or directories that are expected are missing.
    Wrapper for OSError.
    """
    pass


class CorpusIntegrityError(PGError):
    """
    Exception for when a problem arises while loading in the corpus.
    """
    pass


class DelimiterError(PGError):
    """
    Exception for mismatch between specified delimiter and the actual text
    when loading in CSV files and transcriptions.
    """
    pass


class ILGError(ParseError):
    """
    Exception for general issues when loading interlinear gloss files.
    """
    pass


class ILGWordMismatchError(ParseError):
    """
    Exception for when interlinear gloss files have different numbers of
    words across lines that should have a one-to-one mapping.

    Parameters
    ----------
    spelling_line : list
        List of words in the spelling line
    transcription_line : list
        List of words in the transcription line
    """

    def __init__(self, mismatching_lines):
        self.main = "There doesn't appear to be equal numbers of words in one or more of the glosses."

        self.information = ''
        self.details = 'The following glosses did not have matching numbers of words:\n\n'
        for ml in mismatching_lines:
            line_inds, line = ml
            self.details += 'From lines {} to {}:\n'.format(*line_inds)
            for k, v in line.items():
                self.details += '({}, {} words) '.format(k, len(v))
                self.details += ' '.join(str(x) for x in v) + '\n'


class ILGLinesMismatchError(ParseError):
    """
    Exception for when the number of lines in a interlinear gloss file
    is not a multiple of the number of types of lines.

    Parameters
    ----------
    lines : list
        List of the lines in the interlinear gloss file
    """

    def __init__(self, lines):
        self.main = "There doesn't appear to be equal numbers of orthography and transcription lines"

        self.information = ''
        self.details = 'The following is the contents of the file after initial preprocessing:\n\n'
        for line in lines:
            if isinstance(line, tuple):
                self.details += '{}: {}\n'.format(*line)
            else:
                self.details += str(line) + '\n'


class TextGridError(ParseError):
    """
    Exception class for parsing TextGrids
    """
    pass


class TextGridTierError(TextGridError):
    """
    Exception for when a specified tier was not found in a TextGrid.

    Parameters
    ----------
    tier_type : str
        The type of tier looked for (such as spelling or transcription)
    tier_name : str
        The name of the tier specified
    tiers : list
        List of tiers in the TextGrid that were inspected
    """

    def __init__(self, tier_type, tier_name, tiers):
        self.main = 'The {} tier name was not found'.format(tier_type)
        self.information = 'The tier name \'{}\' was not found in any tiers'.format(tier_name)
        self.details = 'The tier name looked for (ignoring case) was \'{}\'.\n'.format(tier_name)
        self.details += 'The following tiers were found:\n\n'
        for t in tiers:
            self.details += '{}\n'.format(t.name)


class BuckeyeParseError(ParseError):
    """
    Exception class for parsing Buckeye formatted files
    """
    def __init__(self, path, misparsed_lines):
        if len(misparsed_lines) == 1:
            self.main = 'One line in \'{}\' was not parsed correctly.'.format(path)
        else:
            self.main = '{} lines in \'{}\' were not parsed correctly.'.format(len(misparsed_lines), path)
        self.information = 'The lines did not have enough fields to be parsed correctly.'
        self.details = 'The following lines were missing entries:\n\n'
        for t in misparsed_lines:
            self.details += '{}\n'.format(t)

        self.value = '\n'.join([self.main, self.details])


# Acoustic exceptions


class AcousticError(PGError):
    """
    Exception class for errors in acoustic processing
    """
    pass


class NoSoundFileError(AcousticError):
    """
    Exception class for when no sound file exists
    """
    pass


class GraphQueryError(PGError):
    """
    Exception class for errors in querying the Neo4j database
    """
    pass


class CorpusConfigError(PGError):
    """
    Exception class for misconfigured CorpusContext objects
    """
    pass


class SubannotationError(PGError):
    """
    Exception class for subannotations
    """
    pass


class GraphModelError(PGError):
    """
    Exception class for generating Python objects from Neo4j queries
    """
    pass


class ConnectionError(PGError):
    """
    Exception class for connection failures
    """
    pass


class AuthorizationError(PGError):
    """
    Exception class for authentication failures
    """
    pass


class NetworkAddressError(PGError):
    """
    Exception class for malformed network addresses
    """
    pass


class TemporaryConnectionError(PGError):
    """
    Exception class for transient connection errors
    """
    pass


class SubsetError(PGError):
    """
    Exception class for not finding a specified subset
    """
    pass


class HierarchyError(PGError):
    """
    Exception class for Hierarchy errors
    """
    pass


class ClientError(PGError):
    """
    Exception class for connecting to remote/local ISCAN servers
    """
    pass


class NodeAttributeError(GraphQueryError):
    """
    Exception class for errors in attributes for base nodes in constructing queries
    """
    pass


class SpeakerAttributeError(NodeAttributeError):
    """
    Exception class for errors in attributes for speakers in constructing queries
    """
    pass


class DiscourseAttributeError(NodeAttributeError):
    """
    Exception class for errors in attributes for discourses in constructing queries
    """
    pass


class AnnotationAttributeError(NodeAttributeError):
    """
    Exception class for errors in attributes for annotations in constructing queries
    """
    pass


class LexiconAttributeError(NodeAttributeError):
    """
    Exception class for errors in attributes for type annotations in constructing queries
    """
    pass
