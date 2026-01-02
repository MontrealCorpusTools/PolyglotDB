import polyglotdb.io as pgio
from polyglotdb import CorpusContext

# corpus_root = './data/LibriSpeech-aligned/'
# corpus_name = 'tutorial'
corpus_root = "./data/LibriSpeech-aligned-subset/"
corpus_name = "tutorial-subset"

parser = pgio.inspect_mfa(corpus_root)
parser.call_back = print

# Note: a corpus only needs to be loaded (imported) to pgdb once.
# If you get the error "The discourse ... already exists in this corpus"
# then you can comment out/delete the following two lines:
with CorpusContext(corpus_name) as c:
    c.load(parser, corpus_root)

# Simple queries
with CorpusContext(corpus_name) as c:
    print("Speakers:", c.speakers)
    print("Discourses:", c.discourses)

    q = c.query_lexicon(c.lexicon_phone)
    q = q.order_by(c.lexicon_phone.label)
    q = q.columns(c.lexicon_phone.label.column_name("phone"))
    results = q.all()
    print(results)

from polyglotdb.query.base.func import Average, Count

with CorpusContext(corpus_name) as c:
    # Optional: Use order_by to enforce ordering on the output for easier comparison with the sample output.
    q = c.query_graph(c.phone).order_by(c.phone.label).group_by(c.phone.label.column_name("phone"))
    results = q.aggregate(
        Count().column_name("count"),
        Average(c.phone.duration).column_name("average_duration"),
    )
    for r in results:
        print(
            "The phone {} had {} occurrences and an average duration of {}.".format(
                r["phone"], r["count"], r["average_duration"]
            )
        )
