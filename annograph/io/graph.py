import csv
import os
from uuid import uuid1

def data_to_graph_csvs(data, directory):
    node_path = os.path.join(directory,'{}_nodes.csv'.format(data.name))
    rel_paths = {x:os.path.join(directory,'{}_{}.csv'.format(data.name,x)) for x in data.types}
    rfs = {k: open(v, 'w') for k,v in rel_paths.items()}
    rel_writers = {k:csv.DictWriter(v, ['from_id', 'to_id','label', 'id'], delimiter = ',')
                        for k,v in rfs.items()}
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
                            rel_writers[base_levels[0]].writerow(dict(from_id=nodes[first_begin_node]['id'],
                                                to_id=node['id'], label=first.label, id = uuid1()))
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
                rel_writers[level].writerow(dict(from_id=begin_node['id'],
                                to_id=end_node['id'], label=d.label, id = uuid1()))
    for x in rfs.values():
        x.close()
