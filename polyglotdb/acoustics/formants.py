# =============== USER CONFIGURATION ===============
polyglotdb_path = "/Users/mlml/Documents/GitHub/PolyglotDB"
corpus_name = "smallest_raleigh"
#corpus_name = "VTRSubset"
corpus_dir = "/Users/mlml/Documents/smallest_raleigh"
textgrid_format = "FAVE"
vowel_inventory = ['ER0', 'IH2', 'EH1', 'AE0', 'UH1', 'AY2', 'AW2', 'UW1', 'OY2', 'OY1', 'AO0', 'AH2', 'ER1', 'AW1', 'OW0', 'IY1', 'IY2', 'UW0', 'AA1', 'EY0', 'AE1', 'AA0', 'OW1', 'AW0', 'AO1', 'AO2', 'IH0', 'ER2', 'UW2', 'IY0', 'AE2', 'AH0', 'AH1', 'UH2', 'EH2', 'UH0', 'EY1', 'AY0', 'AY1', 'EH0', 'EY2', 'AA2', 'OW2', 'IH1']
#vowel_inventory = ['iy', 'ih', 'eh', 'ey', 'ae', 'aa', 'aw', 'ay', 'ah', 'ao', 'oy', 'ow', 'uh', 'uw', 'ux', 'er', 'ax', 'ix', 'axr', 'ax-h']
output_dir = "/Users/mlml/Documents/output/smallest_raleigh"
reset = True	# Setting to True will cause the corpus to re-import

remove_short = 0.05
nIterations = 1
# ==================================================


import sys
import time
sys.path.insert(0,polyglotdb_path)
import os

import logging
import re

import polyglotdb.io as pgio

from polyglotdb import CorpusContext
from polyglotdb.config import CorpusConfig
from polyglotdb.io.parsers import FilenameSpeakerParser
from polyglotdb.io.enrichment import enrich_speakers_from_csv, enrich_lexicon_from_csv

from polyglotdb.acoustics.formant import analyze_formants_vowel_segments_new, get_mean_SD, refine_formants, extract_formants_full
from polyglotdb.acoustics.analysis import generate_phone_segments_by_speaker

from acousticsim.analysis.praat import run_script

from polyglotdb.utils import get_corpora_list



# Logging set up

fileh = logging.FileHandler('loading.log', 'a')
logger = logging.getLogger('three-dimensions')
logger.setLevel(logging.DEBUG)
logger.addHandler(fileh)

graph_db = ({'graph_host':'localhost', 'graph_port': 7474,
	'graph_user': 'neo4j', 'graph_password': 'test'})

def call_back(*args):
	args = [x for x in args if isinstance(x, str)]
	if args:
		print(' '.join(args))

def loading():	# Initial import of corpus to PolyglotDB
	with CorpusContext(corpus_name, **graph_db) as c:
		print ("Loading...")
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
		#beg = time.time()
		c.load(parser, corpus_dir)
		#end = time.time()
		#time = end-beg
		#logger.info('Loading took: ' + str(time))


def enrichment(): # Add primary stress encoding
	with CorpusContext(corpus_name) as c:
		if not 'syllable' in c.annotation_types:
			begin = time.time()
			c.encode_syllabic_segments(vowel_inventory)
			c.encode_syllables('maxonset', call_back = call_back)
			logger.info('Syllable enrichment took: {}'.format(time.time() - begin))

		if re.search(r"\d", vowel_inventory[0]):	# If stress is included in the vowels
			print("here")
			c.encode_stresstone_to_syllables("stress", "[0-9]")
			print("encoded stress")

def formants():	# Analyze formants and bandwidths
	with CorpusContext(corpus_name) as c:
		beg = time.time()
		prototype, metadata, data = extract_formants_full(c, vowel_inventory, remove_short=remove_short, nIterations=nIterations)
		end = time.time()
		logger.info('Analyzing formants took: {}'.format(end - beg))

def analysis():	# Gets information into a csv
	with CorpusContext(corpus_name) as c:
		beg = time.time()
		csv_name = "formant_tracks_full.txt"
		csv_path = os.path.join(output_dir, csv_name)
		q = c.query_graph(c.phone)

		#q = c.query_graph(c.phone).filter(c.phone.syllable.stress=="1")	# Only primary stress (not working though, figure this out)

		q = q.columns(c.phone.begin, c.phone.end, c.phone.label, c.phone.formants.track)
		q.to_csv(csv_path)
		end = time.time()
		logger.info('Query took: {}'.format(end - beg))


if __name__ == '__main__':
	logger.info('Begin processing: {}'.format(corpus_name))
	print('Processing...')

if __name__ == '__main__':
	try:
		if reset:
			loading()
			enrichment()
		formants()
		analysis()
	except:
		raise
