__ver_major__ = 1
__ver_minor__ = 2
__ver_patch__ = 1
__version__ = f"{__ver_major__}.{__ver_minor__}.{__ver_patch__}"

__all__ = ['query', 'io', 'corpus', 'config', 'exceptions', 'CorpusContext', 'CorpusConfig', 'pgdb']

# Inspired by: https://stackoverflow.com/a/43602645
import sys
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

spec = spec_from_loader("pgdb", SourceFileLoader("pgdb", "polyglotdb/command_line/pgdb"))
pgdb = module_from_spec(spec)
spec.loader.exec_module(pgdb)
sys.modules['pgdb'] = pgdb

import polyglotdb.query.annotations as graph

import polyglotdb.io as io

import polyglotdb.corpus as corpus

import polyglotdb.exceptions as exceptions

import polyglotdb.config as config

CorpusConfig = config.CorpusConfig

CorpusContext = corpus.CorpusContext
