

def inspect_discourse(discourse):
    """
    Inspect an initial discourse data structure to extract relevant information

    Parameters
    ----------
    discourse : dict
        Initial discourse data structure

    Returns
    -------
    list
        List of base levels to form nodes the annotation graph
    bool
        Whether the discourse has a 'name' key
    dict
        Whether each annotation type has a 'label' key associated with them
    """
    has_name = 'name' in discourse.keys()

    keys = discourse['data'].keys()
    annotation_types = [x for x in keys]

    base_levels = []
    has_label = {}
    hierarchy = {}
    for k in annotation_types:
        v = discourse['data'][k]
        print(v)
        example = v[0]
        has_label[k] = 'label' in example.keys()
        found = list()
        for a in annotation_types:
            if a in example.keys():
                found.append(a)
        if not found:
            base_levels.append(k)
        else:
            hierarchy[k] = found
    return base_levels, has_name, has_label, hierarchy
