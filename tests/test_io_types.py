import re

from polyglotdb.io.types.content import TranscriptionAnnotationType


def test_parse_transcription():
    delimited_at = TranscriptionAnnotationType("transcription", "word")
    delimited_at.trans_delimiter = "."

    assert delimited_at._parse_transcription("a.t")[0] == ["a", "t"]
    assert delimited_at._parse_transcription("ae.t")[0] == ["ae", "t"]
    assert delimited_at._parse_transcription("a1.t")[0] == ["a1", "t"]

    delimited_at.morph_delimiters = set("-")

    assert delimited_at._parse_transcription("a.t-a.t") == (
        ["a", "t", "a", "t"],
        [2, 4],
    )
    assert delimited_at._parse_transcription("a1.t-a.t") == (
        ["a1", "t", "a", "t"],
        [2, 4],
    )

    delimited_at.number_behavior = "stress"

    assert delimited_at._parse_transcription("a.t-a.t") == (
        ["a", "t", "a", "t"],
        [2, 4],
    )
    assert delimited_at._parse_transcription("a1.t-a.t") == (
        ["a1", "t", "a", "t"],
        [2, 4],
    )

    assert delimited_at._parse_numbers(["a1", "t", "a", "t"]) == (
        ["a", "t", "a", "t"],
        {0: "1"},
    )

    digraph_at = TranscriptionAnnotationType("transcription", "word")

    digraph_at.digraphs = {"ae"}
    assert digraph_at._parse_transcription("aet")[0] == ["ae", "t"]
    assert digraph_at._parse_transcription("ae")[0] == ["ae"]
    assert digraph_at._parse_transcription("et")[0] == ["e", "t"]

    regular = TranscriptionAnnotationType("transcription", "word")
    assert regular._parse_transcription("aet")[0] == ["a", "e", "t"]
    assert regular._parse_transcription("a.et")[0] == ["a", ".", "e", "t"]

    regular.morph_delimiters = set("-")
    assert regular._parse_transcription("a1t-at") == (["a", "1", "t", "a", "t"], [3, 5])

    regular.number_behavior = "stress"
    assert regular._parse_transcription("a1t-at") == (["a", "1", "t", "a", "t"], [2, 4])

    assert regular._parse_numbers(["a", "1", "t", "a", "t"]) == (
        ["a", "t", "a", "t"],
        {0: "1"},
    )

    ignored = TranscriptionAnnotationType("transcription", "word")
    ignored.ignored_characters = set(".")
    assert ignored._parse_transcription("aet")[0] == ["a", "e", "t"]
    assert ignored._parse_transcription("a.et")[0] == ["a", "e", "t"]


def test_compile_digraphs():
    digraph_at = TranscriptionAnnotationType("transcription", "word")

    digraph_at.digraphs = {"aa", "aab"}
    assert digraph_at.digraph_pattern == re.compile(r"aab|aa|\d+|\S")
