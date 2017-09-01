import sys
import os

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,base)

import time
import logging

import polyglotdb.io as pgio
from polyglotdb.io import inspect_textgrid

from polyglotdb import CorpusContext
from polyglotdb.config import CorpusConfig
from polyglotdb.io.parsers import FilenameSpeakerParser
from polyglotdb.corpus import AudioContext
from polyglotdb.io.enrichment import enrich_speakers_from_csv, enrich_lexicon_from_csv

from polyglotdb.utils import get_corpora_list


graph_db = {'graph_host':'localhost', 'graph_port': 7474,
            'graph_user': 'neo4j', 'graph_password': 'test'}

# Paths to scripts and praat

praat_path = 'C:\\Users\\samih\\Documents\\0_SPADE_labwork\\praatcon.exe'
script_path = 'C:\\Users\\samih\\Documents\\0_SPADE_labwork\\PolyglotDB\\examples\\sibilant_jane.praat'
output_path = 'C:\\Users\\samih\\Documents\\0_SPADE_labwork\\PolyglotDB\\examples\\all_sibilant_data.csv'
output_path_word_initial = 'C:\\Users\\samih\\Documents\\0_SPADE_labwork\\PolyglotDB\\examples\\wi_sibilant_data.csv'

# Configuration

name = "small_raleigh"
config = CorpusConfig(name, **graph_db)
config.pitch_source = 'praat'
#config.pitch_algorithm = 'base'
config.formant_source = 'praat'
config.intensity_source = 'praat'
config.praat_path = praat_path

reset = True

# Paths for data files

data_dir = 'C:\\Users\\samih\\Documents\\0_SPADE_labwork\\small_raleigh\\'
#data_dir = 'C:\\Users\\samih\\Documents\\0_SPADE_labwork\\raleigh_test\\'


# Logging set up

# everything was working aug 3 and then I commented this out- uncomment if it creates a problem
# also, should delete the loading.log that this created.
# fileh = logging.FileHandler('loading.log', 'a')
# logger = logging.getLogger('small_raleigh')
# logger.setLevel(logging.DEBUG)
# logger.addHandler(fileh)

# Set up linguistic elements

syllabics = ['AA1', 'AE1', 'IY1', 'IH1', 'EY1', 'EH1', 'AH1', 'AO1',
             'AW1', 'AY1', 'OW1', 'OY1', 'UH1', 'UW1', 'ER1',
             'AA2', 'AE2', 'IY2', 'IH2', 'EY2', 'EH2', 'AH2', 'AO2',
             'AW2', 'AY2', 'OW2', 'OY2', 'UH2', 'UW2', 'ER2',
             'AA0', 'AE0', 'IY0', 'IH0', 'EY0', 'EH0', 'AH0', 'AO0',
             'AW0', 'AY0', 'OW0', 'OY0', 'UH0', 'UW0', 'ER0']

def call_back(*args):
    args = [x for x in args if isinstance(x, str)]
    if args:
        print(' '.join(args))

def loading():
    # Initial import of the corpus to PGDB
    # only needs to be done once. resets the corpus if it was loaded previously.
    with CorpusContext(config) as c:
        c.reset()
        print('reset')
        parser = pgio.inspect_fave(data_dir)
        parser.call_back = call_back
        beg = time.time()
        c.load(parser, data_dir)
        end = time.time()
        print('Loading took: {}'.format(end - beg))


def acoustics():
    # Encode sibilant class and analyze sibilants using the praat script
    with CorpusContext(config) as c:

        c.encode_class(['S', 'Z', 'SH', 'ZH'], 'sibilant')
        print('sibilants encoded')

        c.refresh_hierarchy()
        c.hierarchy.add_type_properties(c, 'word', [('transcription', str)])
        c.encode_hierarchy()
        print('done enrichment')

        #c.reset_acoustics()

        # analyze all sibilants using the script found at script_path
        beg = time.time()
        c.analyze_script('sibilant', script_path)
        end = time.time()
        print("done sibilant analysis")
        print('Sibilant analysis took: {}'.format(end - beg))

def analysis():
    with CorpusContext(config) as c:
        # export to CSV all the measures taken by the script, along with a variety of data about each phone
        print("querying")
        qr = c.query_graph(c.phone).filter(c.phone.type_subset == 'sibilant')
        #qr = c.query_graph(c.phone).filter(c.phone.subset == 'sibilant')
        # this exports data for all sibilants
        qr = qr.columns(c.phone.speaker.name.column_name('speaker'), c.phone.discourse.name.column_name('discourse'),
                      c.phone.id.column_name('phone_id'), c.phone.label.column_name('phone_label'),
                      c.phone.begin.column_name('begin'), c.phone.end.column_name('end'),
                      c.phone.following.label.column_name('following_phone'),
                      c.phone.previous.label.column_name('previous_phone'), c.phone.word.label.column_name('word'),
                      c.phone.cog.column_name('cog'), c.phone.peak.column_name('peak'),
                      c.phone.slope.column_name('slope'), c.phone.spread.column_name('spread'))
        qr.to_csv(output_path)
        # only export data for word-initial sibilants
        q = c.query_graph(c.phone).filter(c.phone.type_subset == 'sibilant')
        q = q.filter_left_aligned(c.word)
        q = q.columns(c.phone.speaker.name.column_name('speaker'), c.phone.discourse.name.column_name('discourse'),
                      c.phone.id.column_name('phone_id'), c.phone.label.column_name('phone_label'),
                      c.phone.begin.column_name('begin'), c.phone.end.column_name('end'),
                      c.phone.following.label.column_name('following_phone'),
                      c.phone.previous.label.column_name('previous_phone'), c.phone.word.label.column_name('word'),
                      c.phone.cog.column_name('cog'), c.phone.peak.column_name('peak'),
                      c.phone.slope.column_name('slope'), c.phone.spread.column_name('spread'))
        q.to_csv(output_path_word_initial)
        print("Results for sibilants written to " + output_path + " and " + output_path_word_initial)


if __name__ == '__main__':
    #logger.info('Begin processing: {}'.format(name))
    print('hello')

if __name__ == '__main__':
    try:
        if reset:
            loading()
        acoustics()
        analysis()
    except:
        raise