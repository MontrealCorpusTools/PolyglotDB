import os
import sys
import logging
import socket
import configparser

CONFIG_DIR = os.path.expanduser('~/.pgdb')

BASE_DIR = os.path.join(CONFIG_DIR, 'data')

CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.ini')

CONFIG = configparser.ConfigParser()
if os.path.exists(CONFIG_PATH):
    CONFIG.read(CONFIG_PATH)
    BASE_DIR = os.path.expanduser(os.path.join(CONFIG['Data']['directory'], 'data'))


def setup_logger(logger_name, log_file, level=logging.INFO):
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s : %(message)s')
    fileHandler = logging.FileHandler(log_file, mode='a')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(logging.ERROR)
    streamHandler.setFormatter(formatter)

    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)
    l.info('---------INIT-----------')


class CorpusConfig(object):
    """
    Class for storing configuration information about a corpus.

    Parameters
    ----------
    corpus_name : str
        Identifier for the corpus
    kwargs : keyword arguments
        All keywords will be converted to attributes of the object

    Attributes
    ----------
    corpus_name : str
        Identifier of the corpus
    graph_user : str
        Username for connecting to the graph database
    graph_password : str
        Password for connecting to the graph database
    graph_host : str
        Host for the graph database
    graph_port : int
        Port for connecting to the graph database
    engine : str
        Type of SQL database
    base_dir : str
        Base directory to store information and temporary files for the corpus
        defaults to "Documents/SCT" under the current user's home directory
    """

    def __init__(self, corpus_name, data_dir=None, **kwargs):
        self.corpus_name = corpus_name
        self.acoustic_user = None
        self.acoustic_password = None
        self.acoustic_http_port = 8086
        self.graph_user = None
        self.graph_password = None
        self.host = 'localhost'
        self.graph_http_port = 7474
        self.graph_bolt_port = 7687

        if data_dir is None:
            data_dir = BASE_DIR
        self.base_dir = os.path.join(data_dir, self.corpus_name)

        self.log_level = logging.DEBUG

        self.log_dir = os.path.join(self.base_dir, 'logs')

        self.temp_dir = os.path.join(self.base_dir, 'temp')
        self.data_dir = os.path.join(self.base_dir, 'data')
        self.audio_dir = os.path.join(self.data_dir, 'audio')

        self.engine = 'sqlite'
        self.db_path = os.path.join(self.data_dir, self.corpus_name)

        self.pitch_source = 'reaper'
        self.pitch_algorithm = 'speaker_adjusted'
        self.formant_source = 'praat'
        self.formant_algorithm = 'fave'
        self.intensity_source = 'praat'
        self.time_sampling = 0.01

        for k, v in kwargs.items():
            setattr(self, k, v)

    def temporary_directory(self, name):
        """
        Create a temporary directory for use in the corpus, and return the
        path name.

        All temporary directories deleted upon successful exit of the
        context manager.

        Returns
        -------
        str:
            Full path to temporary directory
        """
        temp = os.path.join(self.temp_dir, name)
        os.makedirs(temp, exist_ok=True)
        return temp

    def init(self):
        if self.corpus_name:
            os.makedirs(self.log_dir, exist_ok=True)
            os.makedirs(self.temp_dir, exist_ok=True)
            os.makedirs(self.audio_dir, exist_ok=True)

    @property
    def acoustic_conncetion_kwargs(self):
        kwargs = {'host': self.host,
                  'port': self.acoustic_http_port,
                  'database': self.corpus_name}
        if self.acoustic_user is not None:
            kwargs['username'] = self.acoustic_user
        if self.acoustic_password is not None:
            kwargs['password'] = self.acoustic_password
        return kwargs
        # old version (add acoustic_host='localhost' above):
        # kwargs = {'host': self.acoustic_host,
        #           'port': self.acoustic_http_port,
        #           'database': self.corpus_name}
        # if self.acoustic_user is not None:
        #     kwargs['username'] = self.acoustic_user
        # if self.acoustic_password is not None:
        #     kwargs['password'] = self.acoustic_password
        # return kwargs


    @property
    def graph_connection_string(self):
        return "bolt://{}:{}".format(self.host, self.graph_bolt_port)

