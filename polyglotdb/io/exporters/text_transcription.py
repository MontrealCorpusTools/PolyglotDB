def export_discourse_transcription(discourse, path, trans_delim='.', single_line=False):
    """
    Export an transcribed discourse to a text file

    Parameters
    ----------
    discourse : Discourse
        Discourse object to export
    path : str
        Path to export to
    trans_delim : str, optional
        Delimiter for segments, defaults to ``.``
    single_line : bool, optional
        Flag to enforce all text to be on a single line, defaults to False.
        If False, lines are 10 words long.
    """
    with open(path, encoding='utf-8', mode='w') as f:
        count = 0
        for i, wt in enumerate(discourse):
            count += 1
            f.write(trans_delim.join(wt.transcription))
            if i != len(discourse) - 1:
                if not single_line and count <= 10:
                    f.write(' ')
                else:
                    count = 0
                    f.write('\n')
