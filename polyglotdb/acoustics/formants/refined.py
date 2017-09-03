
import math
import numpy as np

from acousticsim.main import analyze_file_segments

from ..segments import generate_vowel_segments
from .helper import generate_variable_formants_point_function, get_mahalanobis, get_mean_SD, save_formant_point_data

from .base import analyze_formants_initial_pass


def refine_formants(corpus_context, prototype_metadata, vowel_inventory, call_back=None,
                    stop_check=None, duration_threshold=None):
    """Second pass of the algorithm; gets measurement with lowest Mahalanobis distance from prototype using variable
    numbers of formants and saves the best point into PolyglotDB.

    Parameters
    ----------
    corpus_context : :class:`~polyglot.corpus.context.CorpusContext`
        The CorpusContext object of the corpus.
    prototype_metadata : dict
        Means of F1, F2, F3, B1, B2, B3 and covariance matrices per vowel class.
    vowel_inventory : list
        A list of all the vowels (in strings) used in the corpus.
    call_back : callable
        Information about callback.
    stop_check : callable
        Information about stop check.
    duration_threshold : float, optional
        Segments with length shorter than this value (in milliseconds) will not be analyzed.

    Returns
    -------
    dict
        The best tracks (closest in Mahalanobis distance to per phone prototypes).
    """
    # ------------- Step 2: Varying formants -------------
    # Encodes vowel inventory into a phone class if it's specified
    if vowel_inventory is not None:
        corpus_context.encode_class(vowel_inventory, 'vowel')

    # Gets segment mapping of phones that are vowels
    segment_mapping = generate_vowel_segments(corpus_context, duration_threshold=duration_threshold)

    # Debugging
    # segment_mapping = segment_mapping[:300]

    if call_back is not None:
        call_back('Analyzing files...')

    best_data = {}
    columns = ['F1', 'F2', 'F3', 'B1', 'B2', 'B3']

    # For each vowel token, collect the formant measurements
    # Pick the best track that is closest to the averages gotten from prototypes
    for i, (vowel, seg) in enumerate(segment_mapping.grouped_mapping('label').items()):

        if len(seg) < 6:
            print("Not enough observations of vowel {}, at least 6 are needed, only found {}.".format(vowel, len(seg)))
            best_distance = "too short"
            continue

        # Make sure the vowel in question is in the data, otherwise it's a pointless iteration
        if vowel in prototype_metadata:
            prototype_means = prototype_metadata[vowel][0]
        else:
            print("Continuing. Vowel for this segment, while in inventory, is not in the data.")
            best_distance = "not in data"
            continue

        # Measure with varying levels of formants
        min_formants = 4  # Off by one error, due to how Praat measures it from F0
        # This really measures with 3 formants: F1, F2, F3. And so on.
        max_formants = 7

        formant_function = generate_variable_formants_point_function(corpus_context, min_formants, max_formants,
                                                                   signal=True)  # Make formant function (VARIABLE)
        output = analyze_file_segments(seg, formant_function, padding=0.25,
                                       stop_check=stop_check)  # Analyze the phone

        # Get Mahalanobis distance between every new observation and the sample/means
        covariance = np.array(prototype_metadata[vowel][1])
        try:
            inverse_covariance = np.linalg.pinv(covariance)
        except:
            print(
                "There's only one observation of this phone, so Mahalanobis distance isn't useful here.")  # Also shouldn't happen
            continue

        for seg, data in output.items():

            best_distance = math.inf
            best_track = 0
            for number, point in data.items():
                point = [point[x] for x in columns]
                distance = get_mahalanobis(prototype_means, point, inverse_covariance)
                if distance < best_distance:  # Update "best" measures when new best distance is found
                    best_distance = distance
                    best_track = point
                    best_number = number

            best_data[seg] = {k:best_track[i] for i, k in enumerate(columns)}
    return best_data


def analyze_formants_refinement(corpus_context, vowel_inventory, duration_threshold=0, num_iterations=1):
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
    # Step 1: Get prototypes
    print("Generating prototypes...")
    prototype_data = analyze_formants_initial_pass(corpus_context, vowel_inventory=vowel_inventory,
                                                         duration_threshold=duration_threshold)
    prev_prototype_metadata = get_mean_SD(prototype_data)

    # Step 3: first pass data = new prototypes, and run again
    print("Regenerating prototypes and running again...")
    if num_iterations < 1:
        raise NotImplementedError
    for i in range(num_iterations):
        print("iteration:", i)
        refined_data = refine_formants(corpus_context, prev_prototype_metadata, vowel_inventory,
                                       duration_threshold=duration_threshold)
        prototype_data = refined_data
        prototype_metadata = get_mean_SD(refined_data)
        prev_prototype_metadata = prototype_metadata

    save_formant_point_data(corpus_context, refined_data)
    return prototype_metadata