from polyglotdb.utils import get_corpora_list


def test_corpora_list(acoustic_config):
    corpora_list = get_corpora_list(acoustic_config)
    assert "acoustic" in corpora_list
