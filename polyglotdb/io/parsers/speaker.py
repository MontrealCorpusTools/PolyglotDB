import os


class SpeakerParser(object):
    def parse_path(self, path):
        raise (NotImplementedError)


class FilenameSpeakerParser(SpeakerParser):
    def __init__(self, number_of_characters, orientation='left'):
        self.number_of_characters = number_of_characters
        self.orientation = orientation

    def parse_path(self, path):
        """
        parses a file path and returns a speaker name

        Parameters
        ----------
        path : str
            the path of the file

        Returns
        -------
        name : str
            the substring of path that is the speaker name
        """
        name = os.path.basename(path)
        name, ext = os.path.splitext(name)
        if self.orientation == 'left':
            return name[:self.number_of_characters]
        else:
            return name[-1 * self.number_of_characters:]


class DirectorySpeakerParser(SpeakerParser):
    def __init__(self):
        pass

    def parse_path(self, path):
        """
        parses a directory path and returns a speaker name

        Parameters
        ----------
        path : str
            the path of the directory

        Returns
        -------
        name : str
            the name of the speaker
        """
        name = os.path.dirname(path)
        name = os.path.basename(name)
        return name
