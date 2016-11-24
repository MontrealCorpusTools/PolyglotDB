import os
from uuid import uuid1

from .sql import get_or_create

from .io.importer import subannotations_data_to_csv, import_subannotation_csv

from .sql.models import (SoundFile, Discourse)

from . import CorpusContext

from .acoustics.io import add_discourse_sound_info

def get_corpora_list(config):
    with CorpusContext(config) as c:
        statement = '''MATCH (n:Corpus) RETURN n.name as name ORDER BY name'''
        results = c.execute_cypher(statement)
    return [x['name'] for x in results]

def add_default_annotations(corpus_context, linguistic_type,
                            defaults, subset = None):
    speaker_query = '''MATCH (speaker:Speaker:{}) return speaker.name as speaker'''
    speakers = corpus_context.execute_cypher(speaker_query.format(corpus_context.corpus_name))
    speakers = [x.speaker for x in speakers]
    atype = getattr(corpus_context, linguistic_type)

    for s in speakers:
        q = corpus_context.query_graph(atype).filter(atype.speaker.name == s)
        if subset is not None:
            q = q.filter(atype.label.in_(subset))
        las = q.all()
        #tx = corpus_context.graph.cypher.begin()
        #try:
        for d in defaults:
            data = []
            t, b, e, props = d
            for a in las:
                if b < 0 or b > 1 or e < 0 or e > 1:
                    raise(ValueError('Beginnings and ends of subannotations must be specified as relative duration (0-1).'))

                dur = a.end - a.begin

                props['begin'] = a.begin + (b * dur)
                props['end'] = a.begin + (e * dur)
                row = dict(id = uuid1(), annotated_id = a.id, **props)
                data.append(row)
            props = sorted(data[0].keys())
            subannotations_data_to_csv(corpus_context, t, data)
            import_subannotation_csv(corpus_context, t, linguistic_type,
                                    props) #,transaction = tx)

    #except Exception:
    #    tx.rollback()
    #    raise
    #tx.commit()
    for d in defaults:
        t, b, e, props = d
        corpus_context.hierarchy.add_subannotation_type(linguistic_type, t)

def update_sound_files(corpus_context, new_directory):
    corpus_context.sql_session.expire_all()
    q = corpus_context.sql_session.query(SoundFile)
    q.delete()
    q = corpus_context.sql_session.query(Discourse)
    if q.first() is None:
        for d in corpus_context.discourses:
            instance = Discourse(name = d)
            corpus_context.sql_session.add(instance)
    for root, subdirs, files in os.walk(new_directory, followlinks = True):
        for f in files:
            if not f.lower().endswith('.wav'):
                continue
            name, _ = os.path.splitext(f)
            q = corpus_context.sql_session.query(Discourse)
            q = q.filter(Discourse.name == name)
            discourse = q.first()
            if discourse is None:
                continue
            add_discourse_sound_info(corpus_context, name, os.path.join(root, f))

gp_language_stops = {'gp_croatian': ['p','t','k', 'b', 'd', 'g'],
                    'gp_french': ['P', 'T', 'K', 'B', 'D', 'G'],
                    'gp_german': ['p','t','k', 'b', 'd', 'g'],
                    'gp_korean': ['B','BB','p', 'Ph','D','DD','t','Th','Kh','k','G','GG'],
                    'gp_polish': ['p','t','k', 'b', 'd', 'g'],
                    'gp_swedish': ['p','t','tr','k', 'b', 'd','dr', 'g'],
                    'gp_thai': ['p','ph','t','th','k','kh','b','d'],
                    'gp_turkish': ['p','t','k', 'b', 'd', 'g']}

gp_speakers = {'gp_croatian': ['CR003', 'CR071', 'CR010', 'CR012', 'CR031', 'CR045', 'CR053','CR083'],
            'gp_french': ['FR013', 'FR015', 'FR016', 'FR023', 'FR030',
                            'FR035', 'FR051', 'FR095'],
            'gp_german': ['GE047', 'GE006', 'GE007', 'GE002', 'GE013', 'GE043', 'GE016', 'GE050'],
            'gp_korean': ['KO004', 'KO014', 'KO015', 'KO023','KO035','KO044','KO075'],
            'gp_swedish': ['SW030', 'SW029','SW089','SW008','SW018','SW037', 'SW015','SW006'],
            'gp_thai': ['TH004', 'TH008', 'TH009', 'TH023', 'TH032',
                        'TH046', 'TH081'],
            'gp_turkish': ['TU005', 'TU014', 'TU015', 'TU025',
                            'TU045', 'TU082', 'TU086', 'TU088']}
