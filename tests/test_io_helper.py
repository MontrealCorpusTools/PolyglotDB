from polyglotdb.io.helper import (inspect_directory, find_wav_path,
                                  normalize_values_for_neo4j,
                                  guess_type, text_to_lines)


def test_inspect_directory(textgrid_test_dir, buckeye_test_dir, timit_test_dir):
    likely, _ = inspect_directory(textgrid_test_dir)
    assert (likely == 'textgrid')

    likely, _ = inspect_directory(buckeye_test_dir)
    assert (likely == 'buckeye')

    likely, _ = inspect_directory(timit_test_dir)
    assert (likely == 'timit')


def test_find_wav_path():
    pass


def test_normalize_values():
    pass


def test_guess_type():
    pass


def test_text_to_lines():
    pass
