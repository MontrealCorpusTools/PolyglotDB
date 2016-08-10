import pytest
from PyQt5 import QtCore

from polyglotdb import CorpusContext
def test_stressed(stressed_config, qtbot):
	w