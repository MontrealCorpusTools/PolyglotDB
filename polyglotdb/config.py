
import os
import sys
import logging
import socket

BASE_DIR = os.path.expanduser('~/Documents/SCT')

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
    def __init__(self, corpus_name, **kwargs):
        self.corpus_name = corpus_name
        self.graph_user = None
        self.graph_password = None
        self.graph_host = 'localhost'
        self.graph_port = 7474

        self.base_dir = os.path.join(BASE_DIR, self.corpus_name)

        self.log_level = logging.DEBUG

        self.log_dir = os.path.join(self.base_dir, 'logs')

        self.temp_dir = os.path.join(self.base_dir, 'temp')
        os.makedirs(self.temp_dir, exist_ok = True)

        self.data_dir = os.path.join(self.base_dir, 'data')
        os.makedirs(self.data_dir, exist_ok = True)

        self.engine = 'sqlite'
        self.db_path = os.path.join(self.data_dir, self.corpus_name)

        for k,v in kwargs.items():
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
        os.makedirs(temp, exist_ok = True)
        return temp

    def init(self):
        os.makedirs(self.log_dir, exist_ok = True)
        return
        setup_logger('{}_loading'.format(self.corpus_name), os.path.join(self.log_dir, 'load.log'), level = self.log_level)
        setup_logger('{}_querying'.format(self.corpus_name), os.path.join(self.log_dir, 'query.log'), level = self.log_level)
        setup_logger('{}_acoustics'.format(self.corpus_name), os.path.join(self.log_dir, 'acoustics.log'), level = self.log_level)

    @property
    def graph_hostname(self):
        return '{}:{}'.format(self.graph_host, self.graph_port)

    @property
    def graph_connection_string(self):
        user_string = ''
        if self.graph_user is not None and self.graph_password is not None:
            user_string = '{}:{}@'.format(self.graph_user, self.graph_password)
        return "http://{}{}/db/data/".format(user_string, self.graph_hostname)

    @property
    def sql_connection_string(self):
        return '{}:///{}.db'.format(self.engine, self.db_path)

def is_valid_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False

    return True
