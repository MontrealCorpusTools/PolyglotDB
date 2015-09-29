
import pytest
import os

from polyglotdb.io.standards.globalphone import (read_spk_file, read_text_file,
                            inspect_speaker_globalphone,
                            globalphone_to_data,
                            load_speaker_globalphone,
                            load_directory_globalphone)

from polyglotdb.corpus import CorpusContext

def test_read_spk(globalphone_test_dir):
    data = read_spk_file(os.path.join(globalphone_test_dir,'spk','AA001.spk'))
    assert(data['SPEAKER ID'] == '001')
    assert(data['TOPIC ARTICLE a0504.006'] == 'internationalPolitics')

def test_read_trl(globalphone_test_dir):
    data = read_text_file(os.path.join(globalphone_test_dir,'trl','AA001.trl'))
    assert(data['1'] == '日本語で話しています。')
    assert(data['2'] == '日本語は楽しいですよ。')

def test_read_rmn(globalphone_test_dir):
    data = read_text_file(os.path.join(globalphone_test_dir,'rmn','AA001.rmn'))
    assert(data['1'] == 'nihongo de hanashiteimasu')
    assert(data['2'] == 'nihongo wa tanoshii desu yo')

