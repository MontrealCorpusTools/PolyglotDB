__ver_major__ = 1
__ver_minor__ = 0
__ver_patch__ = 0
__ver_tuple__ = (__ver_major__, __ver_minor__, __ver_patch__)
__version__ = "%d.%d.%d" % __ver_tuple__

__all__ = ['query', 'io', 'corpus', 'config', 'exceptions', 'CorpusContext', 'CorpusConfig']

import polyglotdb.query.annotations as graph

import polyglotdb.io as io

import polyglotdb.corpus as corpus

import polyglotdb.exceptions as exceptions

import polyglotdb.config as config

CorpusConfig = config.CorpusConfig

CorpusContext = corpus.CorpusContext
