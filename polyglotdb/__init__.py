__ver_major__ = 0
__ver_minor__ = 1
__ver_patch__ = 13
__ver_tuple__ = (__ver_major__, __ver_minor__, __ver_patch__)
__version__ = "%d.%d.%d" % __ver_tuple__

__all__ = ['query', 'io', 'corpus', 'config', 'exceptions']

import polyglotdb.query.annotations as graph

import polyglotdb.io as io

import polyglotdb.corpus as corpus

CorpusContext = corpus.CorpusContext

import polyglotdb.exceptions as exceptions

import polyglotdb.config as config

CorpusConfig = config.CorpusConfig
