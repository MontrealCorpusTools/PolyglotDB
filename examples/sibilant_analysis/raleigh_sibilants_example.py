import os
import sys

# =============== USER CONFIGURATION ===============
polyglotdb_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
corpus_name = "small_raleigh"
# corpus_name = "VTRSubset"
corpus_dir = "/mnt/e/temp/raleigh/smallest_raleigh"
textgrid_format = "FAVE"
vowel_inventory = [
    "ER0",
    "IH2",
    "EH1",
    "AE0",
    "UH1",
    "AY2",
    "AW2",
    "UW1",
    "OY2",
    "OY1",
    "AO0",
    "AH2",
    "ER1",
    "AW1",
    "OW0",
    "IY1",
    "IY2",
    "UW0",
    "AA1",
    "EY0",
    "AE1",
    "AA0",
    "OW1",
    "AW0",
    "AO1",
    "AO2",
    "IH0",
    "ER2",
    "UW2",
    "IY0",
    "AE2",
    "AH0",
    "AH1",
    "UH2",
    "EH2",
    "UH0",
    "EY1",
    "AY0",
    "AY1",
    "EH0",
    "EY2",
    "AA2",
    "OW2",
    "IH1",
]
sibilant_segments = ["S", "Z", "SH", "ZH"]
output_dir = os.path.join(polyglotdb_path, "examples", "sibilant_analysis")
reset = True  # Setting to True will cause the corpus to re-import

duration_threshold = 0.05
nIterations = 1

# Paths to scripts and praat

# praat_path = 'C:\\Users\\samih\\Documents\\0_SPADE_labwork\\praatcon.exe'
praat_path = "praat"
script_path = os.path.join(polyglotdb_path, "examples", "sibilant_analysis", "sibilant_jane.praat")
output_path = os.path.join(
    polyglotdb_path, "examples", "sibilant_analysis", "all_sibilant_data.csv"
)
output_path_word_initial = os.path.join(
    polyglotdb_path, "examples", "sibilant_analysis", "wi_sibilant_data.csv"
)
# ==================================================


sys.path.insert(0, polyglotdb_path)

import time

import polyglotdb.io as pgio
from polyglotdb import CorpusContext
from polyglotdb.config import CorpusConfig
from polyglotdb.utils import ensure_local_database_running


def call_back(*args):
    args = [x for x in args if isinstance(x, str)]
    if args:
        print(" ".join(args))


def loading(config):
    # Initial import of the corpus to PGDB
    # only needs to be done once. resets the corpus if it was loaded previously.
    with CorpusContext(config) as c:
        c.reset()
        print("reset")
        parser = pgio.inspect_fave(corpus_dir)
        parser.call_back = call_back
        beg = time.time()
        c.load(parser, corpus_dir)
        end = time.time()
        print("Loading took: {}".format(end - beg))


def acoustics(config):
    # Encode sibilant class and analyze sibilants using the praat script
    with CorpusContext(config) as c:
        c.encode_class(sibilant_segments, "sibilant")
        print("sibilants encoded")

        # c.reset_acoustics()

        # analyze all sibilants using the script found at script_path
        beg = time.time()
        c.analyze_script("sibilant", script_path)
        end = time.time()
        print("done sibilant analysis")
        print("Sibilant analysis took: {}".format(end - beg))


def analysis(config):
    with CorpusContext(config) as c:
        # export to CSV all the measures taken by the script, along with a variety of data about each phone
        print("querying")
        qr = c.query_graph(c.phone).filter(c.phone.subset == "sibilant")
        # qr = c.query_graph(c.phone).filter(c.phone.subset == 'sibilant')
        # this exports data for all sibilants
        qr = qr.columns(
            c.phone.speaker.name.column_name("speaker"),
            c.phone.discourse.name.column_name("discourse"),
            c.phone.id.column_name("phone_id"),
            c.phone.label.column_name("phone_label"),
            c.phone.begin.column_name("begin"),
            c.phone.end.column_name("end"),
            c.phone.following.label.column_name("following_phone"),
            c.phone.previous.label.column_name("previous_phone"),
            c.phone.word.label.column_name("word"),
            c.phone.cog.column_name("cog"),
            c.phone.peak.column_name("peak"),
            c.phone.slope.column_name("slope"),
            c.phone.spread.column_name("spread"),
        )
        qr.to_csv(output_path)
        # only export data for word-initial sibilants
        q = c.query_graph(c.phone).filter(c.phone.subset == "sibilant")
        q = q.filter_left_aligned(c.word)
        q = q.columns(
            c.phone.speaker.name.column_name("speaker"),
            c.phone.discourse.name.column_name("discourse"),
            c.phone.id.column_name("phone_id"),
            c.phone.label.column_name("phone_label"),
            c.phone.begin.column_name("begin"),
            c.phone.end.column_name("end"),
            c.phone.following.label.column_name("following_phone"),
            c.phone.previous.label.column_name("previous_phone"),
            c.phone.word.label.column_name("word"),
            c.phone.cog.column_name("cog"),
            c.phone.peak.column_name("peak"),
            c.phone.slope.column_name("slope"),
            c.phone.spread.column_name("spread"),
        )
        q.to_csv(output_path_word_initial)
        print(
            "Results for sibilants written to " + output_path + " and " + output_path_word_initial
        )


if __name__ == "__main__":
    with ensure_local_database_running("database") as config:
        conf = CorpusConfig(corpus_name, **config)
        conf.pitch_source = "praat"
        # config.pitch_algorithm = 'base'
        conf.formant_source = "praat"
        conf.intensity_source = "praat"
        conf.praat_path = praat_path
        if reset:
            loading(conf)
        acoustics(conf)
        analysis(conf)
