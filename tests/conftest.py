import os
import shutil
import sys
from decimal import Decimal

import pytest

from polyglotdb.config import CorpusConfig
from polyglotdb.corpus import CorpusContext
from polyglotdb.io import inspect_fave, inspect_mfa, inspect_partitur, inspect_textgrid
from polyglotdb.io.parsers.base import BaseParser
from polyglotdb.io.types.parsing import (
    GroupingTier,
    MorphemeTier,
    OrthographyTier,
    SegmentTier,
    TextMorphemeTier,
    TextOrthographyTier,
    TextTranscriptionTier,
    TranscriptionTier,
)
from polyglotdb.structure import Hierarchy


def pytest_addoption(parser):
    parser.addoption("--skipacoustics", action="store_true", help="skip acoustic tests")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--skipacoustics"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="remove --skipacoustics option to run")
    for item in items:
        if "acoustic" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture(scope="session")
def test_dir():
    base = os.path.dirname(os.path.abspath(__file__))
    generated = os.path.join(base, "data", "generated")
    if not os.path.exists(generated):
        os.makedirs(generated)
    return os.path.join(base, "data")  # was tests/data


@pytest.fixture(scope="session")
def buckeye_test_dir(test_dir):
    return os.path.join(test_dir, "buckeye")


@pytest.fixture(scope="session")
def results_test_dir(test_dir):
    results = os.path.join(test_dir, "generated", "results")
    shutil.rmtree(results, ignore_errors=True)
    os.makedirs(results, exist_ok=True)
    return results


@pytest.fixture(scope="session")
def timit_test_dir(test_dir):
    return os.path.join(test_dir, "timit")


@pytest.fixture(scope="session")
def textgrid_test_dir(test_dir):
    return os.path.join(test_dir, "textgrids")


@pytest.fixture(scope="session")
def praatscript_test_dir(test_dir):
    return os.path.join(test_dir, "praat_scripts")


@pytest.fixture(scope="session")
def fave_test_dir(textgrid_test_dir):
    return os.path.join(textgrid_test_dir, "fave")


@pytest.fixture(scope="session")
def mfa_test_dir(textgrid_test_dir):
    return os.path.join(textgrid_test_dir, "mfa")


@pytest.fixture(scope="session")
def maus_test_dir(textgrid_test_dir):
    return os.path.join(textgrid_test_dir, "maus")


@pytest.fixture(scope="session")
def labbcat_test_dir(textgrid_test_dir):
    return os.path.join(textgrid_test_dir, "labbcat")


@pytest.fixture(scope="session")
def partitur_test_dir(test_dir):
    return os.path.join(test_dir, "partitur")


@pytest.fixture(scope="session")
def text_transcription_test_dir(test_dir):
    return os.path.join(test_dir, "text_transcription")


@pytest.fixture(scope="session")
def text_spelling_test_dir(test_dir):
    return os.path.join(test_dir, "text_spelling")


@pytest.fixture(scope="session")
def ilg_test_dir(test_dir):
    return os.path.join(test_dir, "ilg")


@pytest.fixture(scope="session")
def csv_test_dir(test_dir):
    return os.path.join(test_dir, "csv")


@pytest.fixture(scope="session")
def features_test_dir(test_dir):
    return os.path.join(test_dir, "features")


@pytest.fixture(scope="session")
def export_test_dir(test_dir):
    path = os.path.join(test_dir, "export")
    if not os.path.exists(path):
        os.makedirs(path)
    return path


@pytest.fixture(scope="session")
def corpus_data_timed():
    levels = [
        SegmentTier("label", "phone"),
        OrthographyTier("label", "word"),
        GroupingTier("line", "line"),
    ]
    phones = [
        ("k", 0.0, 0.1),
        ("ae", 0.1, 0.2),
        ("t", 0.2, 0.3),
        ("s", 0.3, 0.4),
        ("aa", 0.5, 0.6),
        ("r", 0.6, 0.7),
        ("k", 0.8, 0.9),
        ("uw", 0.9, 1.0),
        ("t", 1.0, 1.1),
        ("d", 2.0, 2.1),
        ("aa", 2.1, 2.2),
        ("g", 2.2, 2.3),
        ("z", 2.3, 2.4),
        ("aa", 2.4, 2.5),
        ("r", 2.5, 2.6),
        ("t", 2.6, 2.7),
        ("uw", 2.7, 2.8),
        ("ay", 3.0, 3.1),
        ("g", 3.3, 3.4),
        ("eh", 3.4, 3.5),
        ("s", 3.5, 3.6),
    ]
    words = [
        ("cats", 0.0, 0.4),
        ("are", 0.5, 0.7),
        ("cute", 0.8, 1.1),
        ("dogs", 2.0, 2.4),
        ("are", 2.4, 2.6),
        ("too", 2.6, 2.8),
        ("i", 3.0, 3.1),
        ("guess", 3.3, 3.6),
    ]
    lines = [(0.0, 1.1), (2.0, 2.8), (3.0, 3.6)]

    levels[0].add(phones)
    levels[1].add(words)
    levels[2].add(lines)
    hierarchy = Hierarchy({"phone": "word", "word": "line", "line": None})
    parser = BaseParser(levels, hierarchy)
    data = parser.parse_discourse("test_timed")
    return data


@pytest.fixture(scope="session")
def subannotation_data():
    levels = [
        SegmentTier("label", "phone"),
        OrthographyTier("label", "word"),
        OrthographyTier("stop_information", "phone"),
    ]
    levels[2].subannotation = True
    phones = [
        ("k", 0.0, 0.1),
        ("ae", 0.1, 0.2),
        ("t", 0.2, 0.3),
        ("s", 0.3, 0.4),
        ("aa", 0.5, 0.6),
        ("r", 0.6, 0.7),
        ("k", 0.8, 0.9),
        ("u", 0.9, 1.0),
        ("t", 1.0, 1.1),
        ("d", 2.0, 2.1),
        ("aa", 2.1, 2.2),
        ("g", 2.2, 2.3),
        ("z", 2.3, 2.4),
        ("aa", 2.4, 2.5),
        ("r", 2.5, 2.6),
        ("t", 2.6, 2.7),
        ("uw", 2.7, 2.8),
        ("ay", 3.0, 3.1),
        ("g", 3.3, 3.4),
        ("eh", 3.4, 3.5),
        ("s", 3.5, 3.6),
    ]
    words = [
        ("cats", 0.0, 0.4),
        ("are", 0.5, 0.7),
        ("cute", 0.8, 1.1),
        ("dogs", 2.0, 2.4),
        ("are", 2.4, 2.6),
        ("too", 2.6, 2.8),
        ("i", 3.0, 3.1),
        ("guess", 3.3, 3.6),
    ]
    info = [
        ("burst", 0, 0.05),
        ("vot", 0.05, 0.1),
        ("closure", 0.2, 0.25),
        ("burst", 0.25, 0.26),
        ("vot", 0.26, 0.3),
        ("closure", 2.2, 2.25),
        ("burst", 2.25, 2.26),
        ("vot", 2.26, 2.3),
        ("voicing_during_closure", 2.2, 2.23),
        ("voicing_during_closure", 2.24, 2.25),
    ]
    levels[0].add(phones)
    levels[1].add(words)
    levels[2].add(info)
    hierarchy = Hierarchy({"phone": "word", "word": None})
    parser = BaseParser(levels, hierarchy)
    data = parser.parse_discourse("test_sub")
    return data


@pytest.fixture(scope="session")
def corpus_data_onespeaker(corpus_data_timed):
    for k in corpus_data_timed.data.keys():
        corpus_data_timed.data[k].speaker = "some_speaker"
    return corpus_data_timed


@pytest.fixture(scope="session")
def corpus_data_untimed():
    levels = [
        TextTranscriptionTier("transcription", "word"),
        TextOrthographyTier("spelling", "word"),
        TextMorphemeTier("morpheme", "word"),
        GroupingTier("line", "line"),
    ]

    transcriptions = [
        ("k.ae.t-s", 0),
        ("aa.r", 1),
        ("k.y.uw.t", 2),
        ("d.aa.g-z", 3),
        ("aa.r", 4),
        ("t.uw", 5),
        ("ay", 6),
        ("g.eh.s", 7),
    ]
    morphemes = [
        ("cat-PL", 0),
        ("are", 1),
        ("cute", 2),
        ("dog-PL", 3),
        ("are", 4),
        ("too", 5),
        ("i", 6),
        ("guess", 7),
    ]
    words = [
        ("cats", 0),
        ("are", 1),
        ("cute", 2),
        ("dogs", 3),
        ("are", 4),
        ("too", 5),
        ("i", 6),
        ("guess", 7),
    ]
    lines = [(0, 2), (3, 5), (6, 7)]

    levels[0].add(transcriptions)
    levels[1].add(words)
    levels[2].add(morphemes)
    levels[3].add(lines)

    hierarchy = Hierarchy({"word": "line", "line": None})
    parser = BaseParser(levels, hierarchy)
    data = parser.parse_discourse("test_untimed")
    return data


@pytest.fixture(scope="session")
def corpus_data_ur_sr():
    levels = [
        SegmentTier("sr", "phone"),
        OrthographyTier("word", "word"),
        TranscriptionTier("ur", "word"),
    ]
    srs = [
        ("k", 0.0, 0.1),
        ("ae", 0.1, 0.2),
        ("s", 0.2, 0.4),
        ("aa", 0.5, 0.6),
        ("r", 0.6, 0.7),
        ("k", 0.8, 0.9),
        ("u", 0.9, 1.1),
        ("d", 2.0, 2.1),
        ("aa", 2.1, 2.2),
        ("g", 2.2, 2.25),
        ("ah", 2.25, 2.3),
        ("z", 2.3, 2.4),
        ("aa", 2.4, 2.5),
        ("r", 2.5, 2.6),
        ("t", 2.6, 2.7),
        ("uw", 2.7, 2.8),
        ("ay", 3.0, 3.1),
        ("g", 3.3, 3.4),
        ("eh", 3.4, 3.5),
        ("s", 3.5, 3.6),
    ]
    words = [
        ("cats", 0.0, 0.4),
        ("are", 0.5, 0.7),
        ("cute", 0.8, 1.1),
        ("dogs", 2.0, 2.4),
        ("are", 2.4, 2.6),
        ("too", 2.6, 2.8),
        ("i", 3.0, 3.1),
        ("guess", 3.3, 3.6),
    ]
    urs = [
        ("k.ae.t.s", 0.0, 0.4),
        ("aa.r", 0.5, 0.7),
        ("k.y.uw.t", 0.8, 1.1),
        ("d.aa.g.z", 2.0, 2.4),
        ("aa.r", 2.4, 2.6),
        ("t.uw", 0.6, 2.8),
        ("ay", 3.0, 3.1),
        ("g.eh.s", 3.3, 3.6),
    ]
    levels[0].add(srs)
    levels[1].add(words)
    levels[2].add(urs)

    hierarchy = Hierarchy({"phone": "word", "word": None})
    parser = BaseParser(levels, hierarchy)
    data = parser.parse_discourse("test_ursr")
    return data


@pytest.fixture(scope="session")
def lexicon_data():
    corpus_data = [
        {
            "spelling": "atema",
            "transcription": ["ɑ", "t", "e", "m", "ɑ"],
            "frequency": 11.0,
        },
        {
            "spelling": "enuta",
            "transcription": ["e", "n", "u", "t", "ɑ"],
            "frequency": 11.0,
        },
        {
            "spelling": "mashomisi",
            "transcription": ["m", "ɑ", "ʃ", "o", "m", "i", "s", "i"],
            "frequency": 5.0,
        },
        {"spelling": "mata", "transcription": ["m", "ɑ", "t", "ɑ"], "frequency": 2.0},
        {"spelling": "nata", "transcription": ["n", "ɑ", "t", "ɑ"], "frequency": 2.0},
        {"spelling": "sasi", "transcription": ["s", "ɑ", "s", "i"], "frequency": 139.0},
        {
            "spelling": "shashi",
            "transcription": ["ʃ", "ɑ", "ʃ", "i"],
            "frequency": 43.0,
        },
        {
            "spelling": "shisata",
            "transcription": ["ʃ", "i", "s", "ɑ", "t", "ɑ"],
            "frequency": 3.0,
        },
        {
            "spelling": "shushoma",
            "transcription": ["ʃ", "u", "ʃ", "o", "m", "ɑ"],
            "frequency": 126.0,
        },
        {"spelling": "ta", "transcription": ["t", "ɑ"], "frequency": 67.0},
        {
            "spelling": "tatomi",
            "transcription": ["t", "ɑ", "t", "o", "m", "i"],
            "frequency": 7.0,
        },
        {
            "spelling": "tishenishu",
            "transcription": ["t", "i", "ʃ", "e", "n", "i", "ʃ", "u"],
            "frequency": 96.0,
        },
        {"spelling": "toni", "transcription": ["t", "o", "n", "i"], "frequency": 33.0},
        {"spelling": "tusa", "transcription": ["t", "u", "s", "ɑ"], "frequency": 32.0},
        {"spelling": "ʃi", "transcription": ["ʃ", "i"], "frequency": 2.0},
    ]
    return corpus_data


@pytest.fixture(scope="session")
def corpus_data_syllable_morpheme_srur():
    levels = [
        SegmentTier("sr", "phone", label=True),
        TranscriptionTier("ur", "word"),
        GroupingTier("syllable", "syllable"),
        MorphemeTier("morphemes", "word"),
        OrthographyTier("word", "word"),
        GroupingTier("line", "line"),
    ]

    srs = [
        ("b", 0, 0.1),
        ("aa", 0.1, 0.2),
        ("k", 0.2, 0.3),
        ("s", 0.3, 0.4),
        ("ah", 0.4, 0.5),
        ("s", 0.5, 0.6),
        ("er", 0.7, 0.8),
        ("f", 0.9, 1.0),
        ("er", 1.0, 1.1),
        ("p", 1.2, 1.3),
        ("ae", 1.3, 1.4),
        ("k", 1.4, 1.5),
        ("eng", 1.5, 1.6),
    ]
    urs = [
        ("b.aa.k.s-ah.z", 0, 0.6),
        ("aa.r", 0.7, 0.8),
        ("f.ao.r", 0.9, 1.1),
        ("p.ae.k-ih.ng", 1.2, 1.6),
    ]
    syllables = [(0, 0.3), (0.3, 0.6), (0.7, 0.8), (0.9, 1.1), (1.2, 1.5), (1.5, 1.6)]
    morphemes = [
        ("box-PL", 0, 0.6),
        ("are", 0.7, 0.8),
        ("for", 0.9, 1.1),
        ("pack-PROG", 1.2, 1.6),
    ]
    words = [
        ("boxes", 0, 0.6),
        ("are", 0.7, 0.8),
        ("for", 0.9, 1.1),
        ("packing", 1.2, 1.6),
    ]
    lines = [(0, 1.6)]

    levels[0].add(srs)
    levels[1].add(urs)
    levels[2].add(syllables)
    levels[3].add(morphemes)
    levels[4].add(words)
    levels[5].add(lines)

    hierarchy = Hierarchy({"phone": "syllable", "syllable": "word", "word": "line", "line": None})
    parser = BaseParser(levels, hierarchy)
    data = parser.parse_discourse("test_syllable_morpheme")
    return data


@pytest.fixture(scope="session")
def graph_db():
    config = {
        "graph_http_port": 7474,
        "graph_bolt_port": 7687,
        "acoustic_http_port": 8086,
    }
    config["host"] = "localhost"
    return config


@pytest.fixture(scope="session")
def untimed_config(graph_db, corpus_data_untimed):
    config = CorpusConfig("untimed", **graph_db)
    with CorpusContext(config) as c:
        c.reset()
        c.add_types(*corpus_data_untimed.types("untimed"))
        c.initialize_import(
            corpus_data_untimed.speakers,
            corpus_data_untimed.token_headers,
            corpus_data_untimed.hierarchy.subannotations,
        )
        c.add_discourse(corpus_data_untimed)
        c.finalize_import(
            corpus_data_untimed.speakers,
            corpus_data_untimed.token_headers,
            corpus_data_untimed.hierarchy,
        )
    return config


@pytest.fixture(scope="session")
def timed_config(graph_db, corpus_data_timed):
    config = CorpusConfig("timed", **graph_db)
    with CorpusContext(config) as c:
        c.reset()
        c.add_types(*corpus_data_timed.types("timed"))
        c.initialize_import(
            corpus_data_timed.speakers,
            corpus_data_timed.token_headers,
            corpus_data_timed.hierarchy.subannotations,
        )
        c.add_discourse(corpus_data_timed)
        c.finalize_import(
            corpus_data_timed.speakers,
            corpus_data_timed.token_headers,
            corpus_data_timed.hierarchy,
        )
    return config


@pytest.fixture(scope="session")
def syllable_morpheme_config(graph_db, corpus_data_syllable_morpheme_srur):
    config = CorpusConfig("syllable_morpheme", **graph_db)
    with CorpusContext(config) as c:
        c.reset()
        c.add_types(*corpus_data_syllable_morpheme_srur.types("syllable_morpheme"))
        c.initialize_import(
            corpus_data_syllable_morpheme_srur.speakers,
            corpus_data_syllable_morpheme_srur.token_headers,
            corpus_data_syllable_morpheme_srur.hierarchy.subannotations,
        )
        c.add_discourse(corpus_data_syllable_morpheme_srur)
        c.finalize_import(
            corpus_data_syllable_morpheme_srur.speakers,
            corpus_data_syllable_morpheme_srur.token_headers,
            corpus_data_syllable_morpheme_srur.hierarchy,
        )
    return config


@pytest.fixture(scope="session")
def ursr_config(graph_db, corpus_data_ur_sr):
    config = CorpusConfig("ur_sr", **graph_db)
    with CorpusContext(config) as c:
        c.reset()
        c.add_types(*corpus_data_ur_sr.types("ur_sr"))
        c.initialize_import(
            corpus_data_ur_sr.speakers,
            corpus_data_ur_sr.token_headers,
            corpus_data_ur_sr.hierarchy.subannotations,
        )
        c.add_discourse(corpus_data_ur_sr)
        c.finalize_import(
            corpus_data_ur_sr.speakers,
            corpus_data_ur_sr.token_headers,
            corpus_data_ur_sr.hierarchy,
        )
    return config


@pytest.fixture(scope="session")
def subannotation_config(graph_db, subannotation_data):
    config = CorpusConfig("subannotations", **graph_db)
    with CorpusContext(config) as c:
        c.reset()
        c.add_types(*subannotation_data.types("subannotations"))
        c.initialize_import(
            subannotation_data.speakers,
            subannotation_data.token_headers,
            subannotation_data.hierarchy.subannotations,
        )
        c.add_discourse(subannotation_data)
        c.finalize_import(
            subannotation_data.speakers,
            subannotation_data.token_headers,
            subannotation_data.hierarchy,
        )
    return config


@pytest.fixture(scope="session")
def lexicon_test_data():
    data = {
        "cats": {"POS": "NNS"},
        "are": {"POS": "VB"},
        "cute": {"POS": "JJ"},
        "dogs": {"POS": "NNS"},
        "too": {"POS": "IN"},
        "i": {"POS": "PRP"},
        "guess": {"POS": "VB"},
    }
    return data


@pytest.fixture(scope="function")
def acoustic_config(graph_db, textgrid_test_dir):
    config = CorpusConfig("acoustic", **graph_db)

    acoustic_path = os.path.join(textgrid_test_dir, "acoustic_corpus.TextGrid")
    with CorpusContext(config) as c:
        c.reset()
        parser = inspect_textgrid(acoustic_path)
        c.load(parser, acoustic_path)
    config.pitch_algorithm = "acousticsim"
    config.formant_source = "acousticsim"
    return config


@pytest.fixture(scope="session")
def acoustic_syllabics():
    return [
        "ae",
        "aa",
        "uw",
        "ay",
        "eh",
        "ih",
        "aw",
        "ey",
        "iy",
        "uh",
        "ah",
        "ao",
        "er",
        "ow",
    ]


@pytest.fixture(scope="function")
def acoustic_utt_config(graph_db, textgrid_test_dir, acoustic_syllabics):
    config = CorpusConfig("acoustic_utt", **graph_db)

    acoustic_path = os.path.join(textgrid_test_dir, "acoustic_corpus.TextGrid")
    with CorpusContext(config) as c:
        c.reset()
        parser = inspect_textgrid(acoustic_path)
        c.load(parser, acoustic_path)

        c.encode_pauses(["sil"])
        c.encode_utterances(min_pause_length=0)
        c.encode_syllabic_segments(acoustic_syllabics)
        c.encode_syllables()

    config.pitch_algorithm = "acousticsim"
    config.formant_source = "acousticsim"
    return config


@pytest.fixture(scope="function")
def acoustic_utt_config_basic_pitch(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == "ow")
        q = q.order_by(g.phone.begin.column_name("begin"))
        q = q.columns(g.phone.utterance.id.column_name("id"))
        utt_id = q.all()[0]["id"]

        g.reset_acoustics()
        expected_pitch = {
            Decimal("4.23"): {"F0": 98},
            Decimal("4.24"): {"F0": 100},
            Decimal("4.25"): {"F0": 99},
            Decimal("4.26"): {"F0": 95.8},
            Decimal("4.27"): {"F0": 95.8},
        }
        properties = [("F0", float)]
        if "pitch" not in g.hierarchy.acoustics:
            g.hierarchy.add_acoustic_properties(g, "pitch", properties)
            g.encode_hierarchy()
        g.save_acoustic_track("pitch", "acoustic_corpus", expected_pitch, utterance_id=utt_id)
    return acoustic_utt_config


@pytest.fixture(scope="function")
def acoustic_utt_config_praat_pitch(acoustic_utt_config, praat_path):
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.config.praat_path = praat_path
        g.analyze_pitch()
    return acoustic_utt_config


@pytest.fixture(scope="session")
def overlapped_config(graph_db, textgrid_test_dir, acoustic_syllabics):
    config = CorpusConfig("overlapped", **graph_db)

    acoustic_path = os.path.join(textgrid_test_dir, "overlapped_speech")
    with CorpusContext(config) as c:
        c.reset()
        parser = inspect_mfa(acoustic_path)
        c.load(parser, acoustic_path)

        c.encode_pauses(["sil"])
        c.encode_utterances(min_pause_length=0)
        c.encode_syllabic_segments(acoustic_syllabics)
        c.encode_syllables()

    config.pitch_algorithm = "acousticsim"
    config.formant_source = "acousticsim"
    return config


@pytest.fixture(scope="session")
def french_config(graph_db, textgrid_test_dir):
    config = CorpusConfig("french", **graph_db)

    french_path = os.path.join(textgrid_test_dir, "FR001_5.TextGrid")
    with CorpusContext(config) as c:
        c.reset()
        parser = inspect_textgrid(french_path)
        c.load(parser, french_path)

        c.encode_pauses(["sil", "<SIL>"])
        c.encode_utterances(min_pause_length=0.15)

    return config


@pytest.fixture(scope="session")
def fave_corpus_config(graph_db, fave_test_dir):
    config = CorpusConfig("fave_test_corpus", **graph_db)

    with CorpusContext(config) as c:
        c.reset()
        parser = inspect_fave(fave_test_dir)
        c.load(parser, fave_test_dir)
    return config


@pytest.fixture(scope="function")
def summarized_config(graph_db, textgrid_test_dir):
    config = CorpusConfig("summarized", **graph_db)

    acoustic_path = os.path.join(textgrid_test_dir, "acoustic_corpus.TextGrid")
    with CorpusContext(config) as c:
        c.reset()
        parser = inspect_textgrid(acoustic_path)
        c.load(parser, acoustic_path)

    return config


@pytest.fixture(scope="function")
def stressed_config(graph_db, textgrid_test_dir):
    config = CorpusConfig("stressed", **graph_db)

    stressed_path = os.path.join(textgrid_test_dir, "stressed_corpus.TextGrid")
    with CorpusContext(config) as c:
        c.reset()
        parser = inspect_mfa(stressed_path)
        c.load(parser, stressed_path)
    return config


@pytest.fixture(scope="session")
def partitur_corpus_config(graph_db, partitur_test_dir):
    config = CorpusConfig("partitur", **graph_db)

    partitur_path = os.path.join(partitur_test_dir, "partitur_test.par,2")
    with CorpusContext(config) as c:
        c.reset()
        parser = inspect_partitur(partitur_path)
        c.load(parser, partitur_path)
    return config


@pytest.fixture(scope="session")
def praat_path():
    if sys.platform == "win32":
        return "praat.exe"
    elif sys.platform == "darwin":
        return "/Applications/Praat.app/Contents/MacOS/Praat"
    else:
        return os.environ.get("praat")


@pytest.fixture(scope="session")
def reaper_path():
    if os.environ.get("TRAVIS", False):
        return os.path.join(os.environ.get("HOME"), "tools", "reaper")
    else:
        return "reaper"


@pytest.fixture(scope="session")
def vot_classifier_path(test_dir):
    return os.path.join(test_dir, "classifier", "sotc_classifiers", "sotc_voiceless.classifier")


@pytest.fixture(scope="session")
def localhost():
    return "http://localhost:8080"


@pytest.fixture(scope="session")
def stress_pattern_file(test_dir):
    return os.path.join(test_dir, "lexicons", "stress_pattern_lex.txt")


@pytest.fixture(scope="session")
def timed_lexicon_enrich_file(test_dir):
    return os.path.join(test_dir, "csv", "timed_enrichment.txt")


@pytest.fixture(scope="session")
def acoustic_speaker_enrich_file(test_dir):
    return os.path.join(test_dir, "csv", "acoustic_speaker_enrichment.txt")


@pytest.fixture(scope="session")
def acoustic_discourse_enrich_file(test_dir):
    return os.path.join(test_dir, "csv", "acoustic_discourse_enrichment.txt")


@pytest.fixture(scope="session")
def acoustic_inventory_enrich_file(test_dir):
    return os.path.join(test_dir, "features", "basic.txt")


@pytest.fixture(scope="session")
def timed_csv_enrich_file(test_dir):
    return os.path.join(test_dir, "csv", "timed_token_enrichment.txt")


@pytest.fixture(scope="session")
def track_import_file(test_dir):
    return os.path.join(test_dir, "csv", "acoustic_corpus.txt")


@pytest.fixture(scope="session")
def corpus_data_syllabification():
    levels = [
        SegmentTier("label", "phone"),
        OrthographyTier("label", "word"),
        GroupingTier("line", "line"),
    ]

    # Add phones: "extra" = EH1 K S T R AH0 (0.0 - 0.6)
    levels[0].add(
        [
            ("EH1", 0.0, 0.1),
            ("K", 0.1, 0.2),
            ("S", 0.2, 0.3),
            ("T", 0.3, 0.4),
            ("R", 0.4, 0.5),
            ("AH0", 0.5, 0.55),
        ]
    )

    # Add phones: "astronaut" = AE1 S T R AH0 N AO2 T (0.6 - 1.4)
    levels[0].add(
        [
            ("AE1", 0.6, 0.7),
            ("S", 0.7, 0.8),
            ("T", 0.8, 0.9),
            ("R", 0.9, 1.0),
            ("AH0", 1.0, 1.1),
            ("N", 1.1, 1.2),
            ("AO2", 1.2, 1.3),
            ("T", 1.3, 1.4),
        ]
    )

    # Word tiers
    levels[1].add([("extra", 0.0, 0.55), ("astronaut", 0.6, 1.4)])

    # Line tier (single line containing both words)
    levels[2].add([(0.0, 1.4)])

    hierarchy = Hierarchy({"phone": "word", "word": "line", "line": None})
    parser = BaseParser(levels, hierarchy)
    data = parser.parse_discourse("test_syllabification")
    return data


@pytest.fixture(scope="session")
def syllabification_config(graph_db, corpus_data_syllabification):
    config = CorpusConfig("syllabification", **graph_db)
    with CorpusContext(config) as c:
        c.reset()
        c.add_types(*corpus_data_syllabification.types("syllabification"))
        c.initialize_import(
            corpus_data_syllabification.speakers,
            corpus_data_syllabification.token_headers,
            corpus_data_syllabification.hierarchy.subannotations,
        )
        c.add_discourse(corpus_data_syllabification)
        c.finalize_import(
            corpus_data_syllabification.speakers,
            corpus_data_syllabification.token_headers,
            corpus_data_syllabification.hierarchy,
        )
    return config
