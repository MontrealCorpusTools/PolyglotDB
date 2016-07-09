import sys
import os
import time
base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,base)

from polyglotdb import CorpusContext
from polyglotdb.graph.func import Count, Average

graph_db = {'host':'localhost', 'port': 7474,
            'user': 'neo4j', 'password': 'test'}

debug = False

with CorpusContext('buckeye', **graph_db) as g:

    q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
    q = q.filter(g.phone.following.label.in_(['p','t','k','b','d','g','dx', 'tq']))

    q = q.filter(g.phone.end == g.word.end)
    if debug:
        print(q.cypher())
    print(q.count())
    q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
    q = q.filter(g.phone.following.label.in_(['p','t','k','b','d','g','dx', 'tq']))

    q = q.filter(g.phone.following.end == g.word.end)

    print(q.count())

    beg = time.time()
    q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
    q = q.filter_contained_by(g.word.label == 'dog')
    if debug:
        print(q.cypher())
    results = q.count()
    end = time.time()
    print('Count of \'aa\' phones in \'dog\':')
    print(results)
    print('Time taken: {}'.format(end - beg))

    beg = time.time()
    q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
    q = q.filter(g.phone.following.label.in_(['p','t','k','b','d','g','dx']))
    q = q.group_by(g.phone.following.label.column_name('following_consonant'))

    results = q.aggregate(Average(g.phone.duration), Count())
    end = time.time()
    print('Duration of \'aa\' before stops (overall):')
    print(results)
    print('Time taken: {}'.format(end - beg))

    beg = time.time()
    q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
    q = q.filter(g.phone.following.label.in_(['p','t','k','b','d','g','dx']))
    q = q.filter_right_aligned(g.word)
    q = q.group_by(g.phone.following.label.column_name('following_consonant'))
    results = q.aggregate(Average(g.phone.duration), Count())
    end = time.time()
    print('Duration of \'aa\' before stops (across words):')
    print(results)
    print('Time taken: {}'.format(end - beg))
    print('This uses right alignment')

    beg = time.time()
    q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
    q = q.filter(g.phone.following.label.in_(['p','t','k','b','d','g','dx']))
    q = q.filter(g.phone.end == g.word.end)
    q = q.group_by(g.phone.following.label.column_name('following_consonant'))
    results = q.aggregate(Average(g.phone.duration), Count())
    end = time.time()
    print('Duration of \'aa\' before stops (across words):')
    print(results)
    print('Time taken: {}'.format(end - beg))
    print('This uses filter on end points')

    beg = time.time()
    q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
    q = q.filter(g.phone.following.label.in_(['p','t','k','b','d','g','dx']))
    q = q.filter(g.phone.end != g.phone.word.end)
    q = q.times().duration().columns(g.phone.word.label, g.phone.word.transcription,
        g.phone.word.phone.label, g.phone.word.following.label, g.phone.word.duration,
        g.phone.following.label.column_name('following_consonant'))

    if debug:
        print(q.cypher())
    q.to_csv('test.csv')
    q = q.group_by(g.phone.following.label.column_name('following_consonant'))

    results = q.aggregate(Average(g.phone.duration), Count())

    end = time.time()
    print('Duration of \'aa\' before stops (within words):')
    print(results)
    print('Time taken: {}'.format(end - beg))
    print('This uses filter on end points')

    beg = time.time()
    q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
    q = q.filter(g.phone.following.label.in_(['p','t','k','b','d','g','dx']))
    results = q.all()

    end = time.time()
    print('Length of all \'aa\'s analyzed:')
    print(len(results))
    print('Time taken: {}'.format(end - beg))

    beg = time.time()
    q = g.query_graph(g.phone).filter(g.phone.label == 'iy')
    q = q.filter_left_aligned(g.word)
    results = q.all()
    end = time.time()
    print('Number of iy\'s at the left edge of words:')
    print(len(results))
    print('Time taken: {}'.format(end - beg))

