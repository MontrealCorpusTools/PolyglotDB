import csv
import os
from uuid import uuid1

def data_to_graph_csvs(data, directory):
    """
    Convert a DiscourseData object into CSV files for efficient loading
    of graph nodes and relationships

    Parameters
    ----------
    data : DiscourseData
        Data to load into a graph
    directory: str
        Full path to a directory to store CSV files
    """
    node_path = os.path.join(directory,'{}_nodes.csv'.format(data.name))
    contains_path = os.path.join(directory,'{}_contians.csv'.format(data.name))
    rel_paths = {}
    for x in data.types:
        level = x
        if data[level].anchor:
            level = 'word'
        rel_paths[level] = os.path.join(directory,'{}_{}.csv'.format(data.name,level))
    rfs = {k: open(v, 'w') for k,v in rel_paths.items()}
    rel_writers = {}
    for k,v in rfs.items():
        header = ['from_id', 'to_id','label', 'id']
        if k == 'word':
            header += data.token_properties
            if 'transcription' in data.types and not data['transcription'].base:
                header.append('transcription')
            supertype = data[data.word_levels[0]].supertype
            if supertype is not None:
                header.append(supertype)
        else:
            supertype = data[k].supertype
            if supertype is not None:
                if data[supertype].anchor:
                    supertype = 'word'
                #header.append(supertype)
        rel_writers[k] = csv.DictWriter(v, header, delimiter = ',')
    for x in rel_writers.values():
        x.writeheader()
    with open(node_path,'w') as nf:
        node_writer = csv.DictWriter(nf, ['id','label','time','corpus','discourse'], delimiter = ',')

        node_writer.writeheader()
        nodes = []
        node_ind = 0
        begin_node = dict(id = node_ind, label = uuid1(), time = 0, corpus = data.corpus_name, discourse = data.name)
        node_writer.writerow(begin_node)
        base_ind_to_node = {}
        base_levels = data.base_levels
        nodes.append(begin_node)
        for b in base_levels:
            base_ind_to_node[b] = {0: begin_node}
        for i, level in enumerate(data.process_order):
            annotations = []
            for d in data[level]:

                if i == 0: #Anchor level, should have all base levels in it
                    begin_node = nodes[-1]

                    to_align = []
                    endpoints = []
                    if len(base_levels) == 1:

                        b = base_levels[0]
                        begin, end = d[b]
                        base_sequence = data[b][begin:end]

                        if len(base_sequence) == 0:
                            print(d)
                            print(to_align)
                            print(begin_node)
                            raise(ValueError)
                        for j, first in enumerate(base_sequence):
                            time = None
                            time = first.end
                            node_ind += 1
                            node = dict(id = node_ind, label = uuid1(),
                                            time = time, corpus = data.corpus_name,
                                            discourse = data.name)
                            node_writer.writerow(node)
                            nodes.append(node)
                            first_begin_node = -2
                            row = dict(from_id=nodes[first_begin_node]['id'],
                                                to_id=node['id'], label=first.label, id = first.id)
                            supertype = data[b].supertype
                            if data[supertype].anchor:
                                supertype = 'word'

                            #row[supertype] = first.super_id
                            rel_writers[base_levels[0]].writerow(row)
                        end_node = nodes[-1]
                    elif len(base_levels) == 0:
                        node_ind += 1
                        node = dict(id = node_ind, label = uuid1(),
                                        time = None, corpus = data.corpus_name,
                                        discourse = data.name)
                        node_writer.writerow(node)
                        nodes.append(node)
                        end_node = nodes[-1]
                    else:
                        print(data.name)
                        print(base_levels)
                        raise(ValueError)
                else:
                    for b in base_levels:
                        if b in d.references:

                            begin, end = d[b]
                            begin_node = nodes[begin]
                            end_node = nodes[end]
                if data[level].anchor:
                    label = 'word'
                    additional = d.token_properties
                    if 'transcription' in d.type_properties:
                        t = d.type_properties['transcription']
                        if isinstance(t, list):
                            t = '.'.join(map(str,t))

                        additional['transcription'] = t
                    for k,v in additional.items():
                        if not v:
                            additional[k] = 'NULL'
                else:
                    label = level
                    additional = {}
                if d.label == '':
                    d.label = label
                #if d.super_id is not None:
                #    additional[data[level].supertype] = d.super_id
                rel_writers[label].writerow(dict(from_id=begin_node['id'],
                                to_id=end_node['id'], label=d.label, id = d.id,
                                **additional))
    for x in rfs.values():
        x.close()
