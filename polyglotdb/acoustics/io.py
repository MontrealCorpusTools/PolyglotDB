import os
import subprocess
import shutil
import re
import csv
import librosa
import audioread
import neo4j

from conch.utils import write_wav

from ..io.importer.from_csv import make_path_safe


def resample_audio(file_path, new_file_path, new_sr):
    """
    Resample an audio file using either ``sox`` if available or librosa.  Will not overwrite if file already exists.

    Parameters
    ----------
    file_path : str
        Path to audio file
    new_file_path : str
        Path to save new audio file
    new_sr : int
        Sampling rate of new audio file
    """
    if os.path.exists(new_file_path):
        return
    sox_path = shutil.which('sox')
    if sox_path is not None:
        subprocess.call(['sox', file_path.replace('\\', '/'), new_file_path.replace('\\', '/'),
                         'gain', '-1', 'rate', '-I', str(new_sr)])
    else:
        sig, sr = librosa.load(file_path, sr=new_sr, mono=False)
        if len(sig.shape) > 1:
            sig = sig.T
        write_wav(sig, sr, new_file_path)


def add_discourse_sound_info(corpus_context, discourse, filepath):
    with audioread.audio_open(filepath) as f:
        sample_rate = f.samplerate
        n_channels = f.channels
    try:
        p = subprocess.Popen(['sox', filepath, '-n', 'stat'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        output, err = p.communicate()
        err = err.decode('utf8')
        warnings = re.search(r'(sox WARN.*)', err).groups()
        if warnings:
            for w in warnings:
                print(w)
        duration = float(re.search(r'Length \(seconds\):\s+([0-9.]+)', err).groups()[0])
    except:
        with audioread.audio_open(filepath) as f:
            duration = f.duration
    audio_dir = corpus_context.discourse_audio_directory(discourse)
    os.makedirs(audio_dir, exist_ok=True)
    consonant_rate = 16000
    consonant_path = os.path.join(audio_dir, 'consonant.wav')
    vowel_rate = 11000
    vowel_path = os.path.join(audio_dir, 'vowel.wav')
    low_freq_rate = 2000
    low_freq_path = os.path.join(audio_dir, 'low_freq.wav')
    if sample_rate > consonant_rate:
        resample_audio(filepath, consonant_path, consonant_rate)
    else:
        shutil.copy(filepath, consonant_path)
        consonant_rate = sample_rate
    if sample_rate > vowel_rate:
        resample_audio(consonant_path, vowel_path, vowel_rate)
    else:
        shutil.copy(filepath, vowel_path)
        vowel_rate = sample_rate
    if sample_rate > low_freq_rate:
        resample_audio(vowel_path, low_freq_path, low_freq_rate)
    else:
        shutil.copy(filepath, low_freq_path)
        low_freq_rate = sample_rate
    statement = '''MATCH (d:Discourse:{corpus_name}) where d.name = $discourse_name
                    SET d.file_path = $filepath,
                    d.consonant_file_path = $consonant_filepath,
                    d.vowel_file_path = $vowel_filepath,
                    d.low_freq_file_path = $low_freq_filepath,
                    d.duration = $duration,
                    d.sampling_rate = $sampling_rate,
                    d.num_channels = $n_channels'''.format(corpus_name=corpus_context.cypher_safe_name)
    corpus_context.execute_cypher(statement, filepath=filepath,
                                  consonant_filepath=consonant_path,
                                  vowel_filepath=vowel_path,
                                  low_freq_filepath=low_freq_path,
                                  duration=duration, sampling_rate=sample_rate,
                                  n_channels=n_channels, discourse_name=discourse)


def setup_audio(corpus_context, data):
    if data.wav_path is None or not os.path.exists(data.wav_path):
        return
    add_discourse_sound_info(corpus_context, data.name, data.wav_path)


def point_measures_to_csv(corpus_context, data, header):
    if header[0] != 'id':
        header.insert(0, 'id')
    for s in corpus_context.speakers:
        path = os.path.join(corpus_context.config.temporary_directory('csv'),
                            '{}_point_measures.csv'.format(s))
        with open(path, 'w', newline='', encoding='utf8') as f:
            writer = csv.DictWriter(f, header, delimiter=',')
            writer.writeheader()
    for seg, seg_data in data.items():
        path = os.path.join(corpus_context.config.temporary_directory('csv'),
                            '{}_point_measures.csv'.format(seg['speaker']))
        with open(path, 'a', newline='', encoding='utf8') as f:
            writer = csv.DictWriter(f, header, delimiter=',')
            row = dict(id=seg['id'], **{k: v for k, v in seg_data.items() if k in header and k != 'id'})
            writer.writerow(row)


def point_measures_from_csv(corpus_context, header_info, annotation_type="phone"):
    float_set_template = 'n.{name} = toFloat(csvLine.{name})'
    int_set_template = 'n.{name} = toInt(csvLine.{name})'
    bool_set_template = '''n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)'''
    string_set_template = 'n.{name} = csvLine.{name}'
    properties = []
    for h, t in header_info.items():
        if t == int:
            properties.append(int_set_template.format(name=h))
        elif t == float:
            properties.append(float_set_template.format(name=h))
        elif t == bool:
            properties.append(bool_set_template.format(name=h))
        else:
            properties.append(string_set_template.format(name=h))
    properties = ',\n'.join(properties)

    for s in corpus_context.speakers:
        path = os.path.join(corpus_context.config.temporary_directory('csv'),
                            '{}_point_measures.csv'.format(s))
        # If on the Docker version, the files live in /site/proj
        if os.path.exists('/site/proj') and not path.startswith('/site/proj'):
            import_path = 'file:///site/proj/{}'.format(make_path_safe(path))
        else:
            import_path = 'file:///{}'.format(make_path_safe(path))

        import_statement = '''
                USING PERIODIC COMMIT 2000
                LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
                MATCH (n:{annotation_type}:{corpus_name}) where n.id = csvLine.id
                SET {new_properties}'''

        statement = import_statement.format(path=import_path,
                                            corpus_name=corpus_context.cypher_safe_name,
                                            annotation_type=annotation_type,
                                            new_properties=properties)
        corpus_context.execute_cypher(statement)
    for h in header_info.keys():
        if h == 'id':
            continue
        try:
            corpus_context.execute_cypher('CREATE INDEX ON :%s(%s)' % (annotation_type, h))
        except neo4j.exceptions.ClientError as e:
            if e.code != 'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists':
                raise
    corpus_context.hierarchy.add_token_properties(corpus_context, annotation_type,
                                                  [(h, t) for h, t in header_info.items() if h != 'id'])
    corpus_context.encode_hierarchy()
