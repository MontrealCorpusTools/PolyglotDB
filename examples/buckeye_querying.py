import sys
import os
import time
base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,base)

from annograph.corpus import CorpusContext
from annograph.graph.func import Count, Average

graph_db = {'host':'localhost', 'port': 7474,
            'user': 'neo4j', 'password': 'testtest'}

with CorpusContext(corpus_name = 'buckeye', **graph_db) as g:
    beg = time.time()
    q = g.query_graph(g.surface_transcription).filter(g.surface_transcription.label == 'aa')
    q = q.filter_contained_by(g.spelling.label == 'dog')
    print(q.cypher())
    results = q.count()
    end = time.time()
    print('Duration of \'aa\' before stops (overall):')
    print(results)
    print('Time taken: {}'.format(end - beg))

    beg = time.time()
    q = g.query_graph(g.surface_transcription).filter(g.surface_transcription.label == 'aa')
    q = q.filter(g.surface_transcription.following.label.in_(['p','t','k','b','d','g','dx']))
    q = q.group_by(g.surface_transcription.following.label.column_name('following_consonant'))
    results = q.aggregate(Average(g.surface_transcription.duration), Count())
    end = time.time()
    print('Duration of \'aa\' before stops (overall):')
    print(results)
    print('Time taken: {}'.format(end - beg))

    beg = time.time()
    q = g.query_graph(g.surface_transcription).filter(g.surface_transcription.label == 'aa')
    q = q.filter(g.surface_transcription.following.label.in_(['p','t','k','b','d','g','dx']))
    q = q.filter_right_aligned(g.spelling)
    q = q.group_by(g.surface_transcription.following.label.column_name('following_consonant'))
    results = q.aggregate(Average(g.surface_transcription.duration), Count())
    end = time.time()
    print('Duration of \'aa\' before stops (across words):')
    print(results)
    print('Time taken: {}'.format(end - beg))
    print('This uses right alignment')

    beg = time.time()
    q = g.query_graph(g.surface_transcription).filter(g.surface_transcription.label == 'aa')
    q = q.filter(g.surface_transcription.following.label.in_(['p','t','k','b','d','g','dx']))
    q = q.filter(g.surface_transcription.end == g.spelling.end)
    q = q.group_by(g.surface_transcription.following.label.column_name('following_consonant'))
    results = q.aggregate(Average(g.surface_transcription.duration), Count())
    end = time.time()
    print('Duration of \'aa\' before stops (across words):')
    print(results)
    print('Time taken: {}'.format(end - beg))
    print('This uses filter on end points')

    beg = time.time()
    q = g.query_graph(g.surface_transcription).filter(g.surface_transcription.label == 'aa')
    q = q.filter(g.surface_transcription.following.label.in_(['p','t','k','b','d','g','dx']))
    q = q.filter(g.surface_transcription.end != g.spelling.end)
    q = q.group_by(g.surface_transcription.following.label.column_name('following_consonant'))
    results = q.aggregate(Average(g.surface_transcription.duration), Count())
    end = time.time()
    print('Duration of \'aa\' before stops (within words):')
    print(results)
    print('Time taken: {}'.format(end - beg))
    print('This uses filter on end points')

    beg = time.time()
    q = g.query_graph(g.surface_transcription).filter(g.surface_transcription.label == 'aa')
    q = q.filter(g.surface_transcription.following.label.in_(['p','t','k','b','d','g','dx']))
    results = q.all()

    end = time.time()
    print('Length of all \'aa\'s analyzed:')
    print(len(results))
    print('Time taken: {}'.format(end - beg))

    beg = time.time()
    q = g.query_graph(g.surface_transcription).filter(g.surface_transcription.label == 'iy')
    q = q.filter_left_aligned(g.spelling)
    results = q.all()
    end = time.time()
    print('Number of iy\'s at the left edge of words:')
    print(len(results))
    print('Time taken: {}'.format(end - beg))

