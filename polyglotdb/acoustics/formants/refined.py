import math
import os
import numpy as np

from conch import analyze_segments

from ..segments import generate_vowel_segments
from .helper import generate_variable_formants_point_function, get_mahalanobis, get_mean_SD, \
    save_formant_point_data, extract_and_save_formant_tracks


def read_prototypes(vowel_prototypes_path):
    """Reads pre-measured means and covariance matrices from a file.
    """
    # print ('READING PROTOTYPES FROM /phon/SPADE/test_priors.csv')
    # print ('READING PROTOTYPES FROM /phon/SPADE/ral_prototypes.csv')
    means_covar_d = {}

    with open(vowel_prototypes_path) as means_covar_file:
        means_covar_lines = means_covar_file.readlines()
        means_covar_header = means_covar_lines.pop(0)
        prototype_parameters = means_covar_header.strip().split(',')
        prototype_parameters = [p.split('_')[0] for p in prototype_parameters if not p in ['type', 'phone']]
        print(
            'READING PROTOTYPES FROM ' + vowel_prototypes_path + ' with parameters ' + ', '.join(prototype_parameters))
        for line in means_covar_lines:
            splitline = line.strip().split(',')
            means_covar_info_type = splitline[0]
            means_covar_phone = splitline[1]
            means_covar_values = [float(v) for v in splitline[2:]]

            if not means_covar_phone in means_covar_d:
                means_covar_d[means_covar_phone] = [[], []]

            if means_covar_info_type == 'means':
                means_covar_d[means_covar_phone][0] = means_covar_values
            elif means_covar_info_type == 'matrix':
                means_covar_d[means_covar_phone][1].append(means_covar_values)

    return means_covar_d, prototype_parameters


def analyze_formant_points_refinement(corpus_context, vowel_label='vowel', duration_threshold=0, num_iterations=1,
                                      call_back=None,
                                      stop_check=None,
                                      vowel_prototypes_path='',
                                      drop_formant=False,
                                      multiprocessing=True,
                                      output_tracks=False
                                      ):
    """Extracts F1, F2, F3 and B1, B2, B3.

    Parameters
    ----------
    corpus_context : :class:`~polyglot.corpus.context.CorpusContext`
        The CorpusContext object of the corpus.
    vowel_label : str
        The subset of phones to analyze.
    duration_threshold : float, optional
        Segments with length shorter than this value (in milliseconds) will not be analyzed.
    num_iterations : int, optional
        How many times the algorithm should iterate before returning values.
    output_tracks : bool, optional
        Whether to save only the formant values as a point at 0.33 if false or have a track over the entire
        vowel duration if true.

    Returns
    -------
    prototype_metadata : dict
        Means of F1, F2, F3, B1, B2, B3 and covariance matrices per vowel class.
    """
    if not corpus_context.hierarchy.has_type_subset('phone', vowel_label) and not corpus_context.hierarchy.has_token_subset('phone', vowel_label):
        raise Exception('Phones do not have a "{}" subset.'.format(vowel_label))
    # ------------- Step 2: Varying formants -------------
    # Encodes vowel inventory into a phone class if it's specified

    use_vowel_prototypes = vowel_prototypes_path and os.path.exists(vowel_prototypes_path)
    base_formant_columns = ['F1', 'F2', 'F3', 'B1', 'B2', 'B3']
    if use_vowel_prototypes:
        vowel_prototype_metadata, prototype_parameters = read_prototypes(vowel_prototypes_path)
    else:
        prototype_parameters = base_formant_columns

    # Gets segment mapping of phones that are vowels
    segment_mapping = generate_vowel_segments(corpus_context, duration_threshold=duration_threshold, padding=0.1,
                                              vowel_label=vowel_label)
    best_data = {}

    # we used to have just columns, a list of output columns and prototype columns. Now these are not the same thing
    # so we have extra_columns (a list of columns in the output but not the prototypes) and prototype_parameters (a list of columns in the prototypes)
    # columns = ['F1', 'F2', 'F3', 'B1', 'B2', 'B3']
    # extra_columns = ['A1', 'A2', 'A3', 'Ax']
    output_columns = ['F1', 'F2', 'F3', 'B1', 'B2', 'B3', 'A1', 'A2', 'A3', 'Ax', 'A1A2diff', 'A2A3diff']

    # print ('columns:', columns)
    # print ('extra_columns:', extra_columns)
    # print('output_columns:', output_columns)

    log_output = []
    # Measure with varying levels of formants
    min_formants = 4  # Off by one error, due to how Praat measures it from F0
    # This really measures with 3 formants: F1, F2, F3. And so on.
    if drop_formant:
        max_formants = 8
    else:
        max_formants = 7
    default_formant = 5
    formant_function = generate_variable_formants_point_function(corpus_context, min_formants, max_formants)
    best_prototype_metadata = {}

    # For each vowel token, collect the formant measurements
    # Pick the best track that is closest to the averages gotten from prototypes

    total_speaker_vowel_pairs = len(segment_mapping.grouped_mapping('speaker', 'label').items())
    for i, ((speaker, vowel), seg) in enumerate(segment_mapping.grouped_mapping('speaker', 'label').items()):
        if len(seg) == 0:
            continue
        print(speaker + ' ' + vowel + ': ' + str(i + 1) + ' of ' + str(total_speaker_vowel_pairs) + ': ' + str(
            len(seg)) + ' tokens')
        output = analyze_segments(seg, formant_function, stop_check=stop_check,
                                  multiprocessing=multiprocessing)  # Analyze the phone

        if len(seg) < 6:
            print("Not enough observations of vowel {}, at least 6 are needed, only found {}.".format(vowel, len(seg)))
            for s, data in output.items():
                best_track = data[default_formant]
                best_data[s] = {k: best_track[k] for j, k in enumerate(base_formant_columns)}
            continue

        if drop_formant:
            # ADD ALL THE LEAVE-ONE-OUT CANDIDATES
            for s, data in output.items():
                new_data = {}
                ignored_candidates = []
                for candidate, measurements in data.items():

                    try:
                        As = [measurements['A1'], measurements['A2'], measurements['A3'], measurements['A4']]
                        Fs = [math.log2(measurements['F1']), math.log2(measurements['F2']),
                              math.log2(measurements['F3']), math.log2(measurements['F4'])]
                        Farray = np.array([Fs, np.ones(len(Fs))])
                        [slope, intercept] = np.linalg.lstsq(Farray.T, As)[0]

                    except:
                        try:
                            As = [measurements['A1'], measurements['A2'], measurements['A3']]
                            Fs = [math.log2(measurements['F1']), math.log2(measurements['F2']),
                                  math.log2(measurements['F3'])]
                            Farray = np.array([Fs, np.ones(len(Fs))])
                            [slope, intercept] = np.linalg.lstsq(Farray.T, As)[0]

                        except:
                            try:
                                As = [measurements['A1'], measurements['A2']]
                                Fs = [math.log2(measurements['F1']), math.log2(measurements['F2'])]
                                [slope, intercept] = [0, 0]
                            except:
                                # Lack of formants for these settings
                                ignored_candidates.append(candidate)
                                continue

                    for leave_out in range(1, 1 + min(3, candidate)):
                        new_measurements = {}
                        new_measurements['Ax'] = measurements['A' + str(leave_out)]
                        candidate_name = str(candidate) + 'x' + str(leave_out)

                        if leave_out < len(As) and As[leave_out - 1] < intercept + slope * Fs[leave_out - 1]:
                            this_is_droppable = True
                        else:
                            this_is_droppable = False
                        if this_is_droppable:
                            for parameter in measurements.keys():
                                if int(parameter[-1]) < leave_out:
                                    new_measurements[parameter] = measurements[parameter]
                                elif int(parameter[-1]) > leave_out:
                                    new_measurements[parameter[0] + str(int(parameter[-1]) - 1)] = measurements[
                                        parameter]
                            new_data[candidate_name] = new_measurements

                    data[candidate]['Ax'] = data[candidate]['A4']
                data = {k: v for k,v in data.items() if k not in ignored_candidates}
                output[s] = {**data, **new_data}
        else:
            for s, data in output.items():
                for candidate, measurements in data.items():
                    output[s][candidate]['Ax'] = output[s][candidate]['A4']
        output = {k: v for k,v in output.items() if v}
        for s, data in output.items():
            for candidate, measurements in data.items():
                try:
                    output[s][candidate]['A1A2diff'] = data[candidate]['A1'] - data[candidate]['A2']
                    try:
                        output[s][candidate]['A2A3diff'] = data[candidate]['A2'] - data[candidate]['A3']
                    except:
                        try:
                            output[s][candidate]['A2A3diff'] = data[candidate]['A2']
                        except:
                            output[s][candidate]['A2A3diff'] = 0
                except:
                    try:
                        output[s][candidate]['A1A2diff'] = data[candidate]['A1']
                    except:
                        output[s][candidate]['A1A2diff'] = 0
                    output[s][candidate]['A2A3diff'] = 0
        selected_tracks = {}
        for s, data in output.items():

            try:
                selected_tracks[s] = data[default_formant]
            except:
                print(s)
                print(data)
                raise
        if not use_vowel_prototypes:
            print('no prototypes, using get_mean_SD()')
            prev_prototype_metadata = get_mean_SD(selected_tracks, prototype_parameters)
        elif not vowel in vowel_prototype_metadata:
            print('no prototype for', vowel, 'so using get_mean_SD()')
            prev_prototype_metadata = get_mean_SD(selected_tracks, prototype_parameters)
        else:
            prev_prototype_metadata = vowel_prototype_metadata

        if num_iterations > 1 and len(seg) < 6:
            print("Skipping iterations for vowel {}, at least 6 tokens are needed, only found {}.".format(vowel,
                                                                                                          len(seg)))
            my_iterations = [0]
        else:
            my_iterations = range(num_iterations)
        for _ in my_iterations:
            best_numbers = []
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
                    point = [point[x] if point[x] else 0 for x in prototype_parameters]
                    distance = get_mahalanobis(prototype_means, point, inverse_covariance)
                    if distance < best_distance:  # Update "best" measures when new best distance is found
                        best_distance = distance
                        best_track = point
                        best_number = number
                # selected_tracks[s] = {k: best_track[i] for i, k in enumerate(columns)}
                selected_tracks[s] = {k: best_track[i] for i, k in enumerate(prototype_parameters)}
                # best_data[s] = {k: best_track[i] for i, k in enumerate(output_columns)}
                # best_data[s] = {k: best_track[i] for i, k in enumerate(columns)}
                best_data[s] = {}
                for output_column in output_columns:
                    best_data[s][output_column] = output[s][best_number][output_column]

                best_data[s]['num_formants'] = float(str(best_number).split('x')[0])
                best_data[s]['Fx'] = int(str(best_number)[0])
                if 'x' in str(best_number):
                    best_data[s]['drop_formant'] = int(str(best_number).split('x')[-1])
                else:
                        best_data[s]['drop_formant'] = 0

                best_numbers.append(best_number)

            if len(seg) >= 6:
                prototype_metadata = get_mean_SD(selected_tracks, prototype_parameters)
                prev_prototype_metadata = prototype_metadata
                best_prototype_metadata.update(prototype_metadata)

            if _ > 0:
                changed_numbers = 0
                for i, bn in enumerate(best_numbers):
                    if bn != last_iteration_best_numbers[i]:
                        changed_numbers += 1
                if changed_numbers == 0:
                    break
            last_iteration_best_numbers = best_numbers
        log_output.append([speaker, vowel, str(len(output)), str(_ + 1)])
    for i in log_output:
        print('Speaker {} for vowel {} had {} tokens and completed refinement in {} iterations'.format(*i))
    if output_tracks:
        extract_and_save_formant_tracks(corpus_context, best_data, num_formants=True, multiprocessing=multiprocessing, stop_check=stop_check)
    else:
        save_formant_point_data(corpus_context, best_data, num_formants=True)
    return best_prototype_metadata
