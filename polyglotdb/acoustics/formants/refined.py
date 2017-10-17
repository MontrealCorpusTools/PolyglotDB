import math
import numpy as np

from conch import analyze_segments

from ..segments import generate_vowel_segments
from .helper import generate_variable_formants_point_function, get_mahalanobis, get_mean_SD, save_formant_point_data


def analyze_formant_points_refinement(corpus_context, vowel_inventory, duration_threshold=0, num_iterations=1,
                                      call_back=None,
                                      stop_check=None):
    """Extracts F1, F2, F3 and B1, B2, B3.

    Parameters
    ----------
    corpus_context : :class:`~polyglot.corpus.context.CorpusContext`
        The CorpusContext object of the corpus.
    vowel_inventory : list
        A list of vowels contained in the corpus.
    duration_threshold : float, optional
        Segments with length shorter than this value (in milliseconds) will not be analyzed.
    num_iterations : int, optional
        How many times the algorithm should iterate before returning values.

    Returns
    -------
    prototype_metadata : dict
        Means of F1, F2, F3, B1, B2, B3 and covariance matrices per vowel class.
    """
    if vowel_inventory is not None:
        corpus_context.encode_class(vowel_inventory, 'vowel')
    # ------------- Step 2: Varying formants -------------
    # Encodes vowel inventory into a phone class if it's specified

    # Gets segment mapping of phones that are vowels
    segment_mapping = generate_vowel_segments(corpus_context, duration_threshold=duration_threshold, padding=0.1)
    best_data = {}
    columns = ['F1', 'F2', 'F3', 'B1', 'B2', 'B3']
    # Measure with varying levels of formants
    min_formants = 4  # Off by one error, due to how Praat measures it from F0
    # This really measures with 3 formants: F1, F2, F3. And so on.
    max_formants = 7
    default_formant = 5
    formant_function = generate_variable_formants_point_function(corpus_context, min_formants, max_formants)
    best_prototype_metadata = {}
    # For each vowel token, collect the formant measurements
    # Pick the best track that is closest to the averages gotten from prototypes
    for i, (vowel, seg) in enumerate(segment_mapping.grouped_mapping('label').items()):

        output = analyze_segments(seg, formant_function, stop_check=stop_check)  # Analyze the phone

        if len(seg) < 6:
            print("Not enough observations of vowel {}, at least 6 are needed, only found {}.".format(vowel, len(seg)))
            for s, data in output.items():
                best_track = data[default_formant]
                best_data[s] = {k: best_track[k] for j, k in enumerate(columns)}
            continue
        selected_tracks = {}
        for s, data in output.items():
            selected_tracks[s] = data[default_formant]
        prev_prototype_metadata = get_mean_SD(selected_tracks)

        for _ in range(num_iterations):
            selected_tracks = {}
            prototype_means = prev_prototype_metadata[vowel][0]
            # Get Mahalanobis distance between every new observation and the sample/means
            covariance = np.array(prev_prototype_metadata[vowel][1])
            inverse_covariance = np.linalg.pinv(covariance)
            best_number = 5
            for s, data in output.items():
                best_distance = math.inf
                best_track = 0
                for number, point in data.items():
                    point = [point[x] if point[x] else 0 for x in columns]

                    distance = get_mahalanobis(prototype_means, point, inverse_covariance)
                    if distance < best_distance:  # Update "best" measures when new best distance is found
                        best_distance = distance
                        best_track = point
                        best_number = number
                selected_tracks[s] = {k: best_track[i] for i, k in enumerate(columns)}
                best_data[s] = {k: best_track[i] for i, k in enumerate(columns)}
                best_data[s]['num_formants'] = best_number
            prototype_metadata = get_mean_SD(selected_tracks)
            prev_prototype_metadata = prototype_metadata
            best_prototype_metadata.update(prototype_metadata)

    save_formant_point_data(corpus_context, best_data, num_formants=True)
    corpus_context.cache_hierarchy()
    return best_prototype_metadata
