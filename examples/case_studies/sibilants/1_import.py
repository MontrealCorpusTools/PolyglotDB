import polyglotdb.io as pgio
from polyglotdb import CorpusContext


def main():
    # Set the path to the corpus (change this if you've put the corpus in a different location)
    corpus_root = "../ParlBleu-subset/"

    # Set the name of the PolyglotDB database that will be created for the corpus (can be anything)
    corpus_name = "ParlBleu-subset"

    # This tells PolyglotDB that the TextGrids are in the *Montreal Forced Aligner* format
    parser = pgio.inspect_mfa(corpus_root)
    parser.call_back = print

    with CorpusContext(corpus_name) as c:
        c.load(parser, corpus_root)


if __name__ == "__main__":
    main()
