import sys
import os
import time
base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,base)

from annograph.graph.util import CorpusContext, Count, Average
from annograph.graph.models import Anchor, Annotation

graph_db = {'host':'localhost', 'port': 7474,
            'user': 'neo4j', 'password': 'testtest'}

with CorpusContext(corpus_name = 'buckeye', **graph_db) as g:
    beg = time.time()
    q = g.query('surface_transcription').filter(Annotation.label == 'aa')
    q = q.filter(Annotation.following.label.in_(['p','t','k','b','d','g','dx']))
    results = q.group_by(Annotation.following.label).aggregate(Average('duration'), Count('*'))
    end = time.time()
    print('Duration of \'aa\' before stops (overall):')
    print(results)
    print('Time taken: {}'.format(end - beg))

    beg = time.time()
    q = g.query('surface_transcription').filter(Annotation.label == 'aa')
    q = q.filter(Annotation.following.label.in_(['p','t','k','b','d','g','dx']))
    q = q.filter_right_aligned('spelling')
    results = q.group_by(Annotation.following.label).aggregate(Average('duration'), Count('*'))
    end = time.time()
    print('Duration of \'aa\' before stops (within words):')
    print(results)
    print('Time taken: {}'.format(end - beg))

    beg = time.time()
    q = g.query('surface_transcription').filter(Annotation.label == 'aa')
    q = q.filter(Annotation.following.label.in_(['p','t','k','b','d','g','dx']))
    results = q.all()

    end = time.time()
    print('Duration of \'aa\' before stops:')
    print(len(results))
    print('Time taken: {}'.format(end - beg))

    beg = time.time()
    q = g.query('surface_transcription').filter(Annotation.label == 'iy')
    q = q.filter_left_aligned('spelling')
    results = q.all()
    end = time.time()
    print('Number of iy\'s at the left edge of words:')
    print(len(results))
    print('Time taken: {}'.format(end - beg))

