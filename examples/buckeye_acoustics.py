import sys
import os
import time
base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,base)

import polyglotdb.io as aio
from polyglotdb.config import CorpusConfig

from polyglotdb import CorpusContext
from polyglotdb.io import enrich_speakers_from_csv


graph_db = {'graph_host':'localhost', 'graph_port': 7474,
            'graph_user': 'neo4j', 'graph_password': 'test'}

praat = r'C:\Users\michael\Documents\Praat\praatcon.exe'

reaper = r'D:\Dev\Tools\REAPER-master\reaper.exe'

speaker_info_path = r'D:\Data\VIC\SpeakerInfo.txt'

config = CorpusConfig('buckeye', **graph_db)

config.reaper_path = reaper
config.praat_path = praat
config.pitch_algorithm = 'praat'

def call_back(*args):
    args = [x for x in args if isinstance(x, str)]
    if args:
        print(' '.join(args))

if __name__ == '__main__':
    with CorpusContext(config) as g:
        g.reset_acoustics()
        if not 'utterance' in g.annotation_types:
            g.encode_pauses('^[{<].*', call_back = call_back)
            g.encode_utterances(min_pause_length = 0.15, call_back = call_back)
        if not g.hierarchy.has_speaker_property('gender'):
            enrich_speakers_from_csv(g, speaker_info_path)
        g.analyze_acoustics(call_back = call_back)
