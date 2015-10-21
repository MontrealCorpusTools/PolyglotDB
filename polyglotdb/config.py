
import os
import sys
import logging

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
    def __init__(self, corpus_name, **kwargs):
        self.corpus_name = corpus_name
        self.graph_user = 'neo4j'
        self.graph_password = 'test'
        self.graph_host = 'localhost'
        self.graph_port = 7474

        self.base_dir = os.path.join(os.path.expanduser('~/Documents/SCT'), self.corpus_name)

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

    def init(self):
        os.makedirs(self.log_dir, exist_ok = True)
        setup_logger('{}_loading'.format(self.corpus_name), os.path.join(self.log_dir, 'load.log'), level = self.log_level)
        setup_logger('{}_querying'.format(self.corpus_name), os.path.join(self.log_dir, 'query.log'), level = self.log_level)
        setup_logger('{}_acoustics'.format(self.corpus_name), os.path.join(self.log_dir, 'acoustics.log'), level = self.log_level)

    @property
    def graph_connection_string(self):
        return "http://{}:{}@{}:{}/db/data/".format(self.graph_user, self.graph_password, self.graph_host, self.graph_port)

    @property
    def sql_connection_string(self):
        return '{}:///{}.db'.format(self.engine, self.db_path)
