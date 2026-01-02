from polyglotdb import CorpusContext

corpus_name = "tutorial-subset"
with CorpusContext(corpus_name) as c:
    c.reset()
