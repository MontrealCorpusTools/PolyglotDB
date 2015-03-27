import networkx as nx
import matplotlib.pyplot as plt

def plot_graph(corpus, show=True, output = None):
    edge_labels = corpus.get_edge_labels()
    #print(sorted(edge_labels.items()))
    #t
    G = nx.MultiDiGraph()
    for v in edge_labels.values():
        for k2,v2 in v.items():
            G.add_edge(*k2,label=v2)
    pos=nx.graphviz_layout(G,prog='dot')

    nx.draw_networkx_nodes(G,pos)
    nx.draw_networkx_edges(G,pos)

    edge_labels=dict([((u,v,),d['label'])
                 for u,v,d in G.edges(data=True)])
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    #if output is not None:
    #    nx.write_dot(G,output)
    plt.axis('off')
    if show:
        plt.show()
