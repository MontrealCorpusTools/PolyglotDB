import pytest
import os

from polyglotdb.io.parsers.speaker import FilenameSpeakerParser, DirectorySpeakerParser

def test_directory_parsing(buckeye_test_dir):
    path = os.path.join(buckeye_test_dir, 'test.words')
    parser = DirectorySpeakerParser()
    name = parser.parse_path(path)
    assert(name == 'buckeye')

def test_filename_parsing(buckeye_test_dir):
    path = os.path.join(buckeye_test_dir, 'test.words')
    parser = FilenameSpeakerParser(3)
    name = parser.parse_path(path)
    assert(name == 'tes')
