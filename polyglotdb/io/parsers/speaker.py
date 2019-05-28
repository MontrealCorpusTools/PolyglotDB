import os


class SpeakerParser(object):
    def parse_path(self, path):
        raise (NotImplementedError)


class FilenameSpeakerParser(SpeakerParser):
    """
    Class for parsing a speaker name from a path that gets a specified number of characters from either the left or
    the right of the base file name.

    Parameters
    ----------
    number_of_characters : int
        Number of characters to include in the speaker designation, set to 0 to get the full file name
    left_orientation : bool
        Whether to pull characters from the left or right of the base file name, defaults to True

    """
    def __init__(self, number_of_characters, left_orientation=True):
        self.number_of_characters = number_of_characters
        self.left_orientation = left_orientation

    def parse_path(self, path):
        """
        Parses a file path and returns a speaker name

        Parameters
        ----------
        path : str
            File path

        Returns
        -------
        str
            Substring of path that is the speaker name
        """
        name = os.path.basename(path)
        name, ext = os.path.splitext(name)
        if not self.number_of_characters:
            return name
        if self.left_orientation:
            return name[:self.number_of_characters]
        else:
            return name[-1 * self.number_of_characters:]


class DirectorySpeakerParser(SpeakerParser):
    """
    Class for parsing a speaker name from a path that gets the directory immediately containing the file and uses
    its name as the speaker name
    """
    def __init__(self):
        pass

    def parse_path(self, path):
        """
        Parses a file path and returns a speaker name

        Parameters
        ----------
        path : str
            File path

        Returns
        -------
        str
            Directory that is the name of the speaker
        """
        name = os.path.dirname(path)
        name = os.path.basename(name)
        return name
