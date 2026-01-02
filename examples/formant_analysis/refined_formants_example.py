import os
import sys

# =============== USER CONFIGURATION ===============
polyglotdb_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
corpus_name = "small_raleigh"
corpus_dir = r"/mnt/e/temp/raleigh/small_raleigh"
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
stressed_vowels = [x for x in vowel_inventory if x.endswith("1")]
output_dir = os.path.join(polyglotdb_path, "examples", "formant_analysis")
reset = True  # Setting to True will cause the corpus to re-import

duration_threshold = 0.05
nIterations = 1
# ==================================================


sys.path.insert(0, polyglotdb_path)

import re
import time

import polyglotdb.io as pgio
from polyglotdb import CorpusContext
from polyglotdb.acoustics.formants.refined import analyze_formant_points_refinement
from polyglotdb.utils import ensure_local_database_running


def call_back(*args):
    args = [x for x in args if isinstance(x, str)]
    if args:
        print(" ".join(args))


def loading(config):  # Initial import of corpus to PolyglotDB
    with CorpusContext(corpus_name, **config) as c:
        print("Loading...")
        c.reset()

        if textgrid_format == "buckeye":
            parser = pgio.inspect_buckeye(corpus_dir)
        elif textgrid_format == "csv":
            parser = pgio.inspect_buckeye(corpus_dir)
        elif textgrid_format == "FAVE":
            parser = pgio.inspect_fave(corpus_dir)
        elif textgrid_format == "ilg":
            parser = pgio.inspect_ilg(corpus_dir)
        elif textgrid_format == "labbcat":
            parser = pgio.inspect_labbcat(corpus_dir)
        elif textgrid_format == "MFA":
            parser = pgio.inspect_mfa(corpus_dir)
        elif textgrid_format == "partitur":
            parser = pgio.inspect_partitur(corpus_dir)
        elif textgrid_format == "timit":
            parser = pgio.inspect_timit(corpus_dir)

        parser.call_back = call_back
        # beg = time.time()
        c.load(parser, corpus_dir)
        # end = time.time()
        # time = end-beg
        # logger.info('Loading took: ' + str(time))


def enrichment(config):  # Add primary stress encoding
    with CorpusContext(corpus_name, **config) as c:
        if "syllable" not in c.annotation_types:
            begin = time.time()
            c.encode_syllabic_segments(vowel_inventory)
            c.encode_syllables("maxonset", call_back=call_back)
            print("Syllable enrichment took: {}".format(time.time() - begin))

        if re.search(r"\d", vowel_inventory[0]):  # If stress is included in the vowels
            print("here")
            c.encode_stress_to_syllables("[0-9]", clean_phone_label=False)
            print("encoded stress")


def formants(config):  # Analyze formants and bandwidths
    with CorpusContext(corpus_name, **config) as c:
        beg = time.time()
        analyze_formant_points_refinement(
            c,
            stressed_vowels,
            duration_threshold=duration_threshold,
            num_iterations=nIterations,
        )
        end = time.time()
        print("Analyzing formants took: {}".format(end - beg))


def analysis(config):  # Gets information into a csv
    with CorpusContext(corpus_name, **config) as c:
        beg = time.time()
        csv_name = "formant_tracks_full.csv"
        csv_path = os.path.join(output_dir, csv_name)
        q = c.query_graph(c.phone).filter(c.phone.label.in_(stressed_vowels))

        # q = c.query_graph(c.phone).filter(c.phone.syllable.stress=="1")	# Only primary stress (not working though, figure this out)

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
            c.phone.F1.column_name("F1"),
            c.phone.F2.column_name("F2"),
            c.phone.F3.column_name("F3"),
            c.phone.B1.column_name("B1"),
            c.phone.B2.column_name("B2"),
            c.phone.B3.column_name("B3"),
        )
        q.to_csv(csv_path)
        end = time.time()
        print("Query took: {}".format(end - beg))


if __name__ == "__main__":
    print("Processing...")
    with ensure_local_database_running("database") as config:
        if reset:
            loading(config)
            enrichment(config)
        formants(config)
        analysis(config)
