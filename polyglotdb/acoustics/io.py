import os
import subprocess
import shutil
import csv
import librosa
import audioread

from conch.utils import write_wav

from ..io.importer.from_csv import make_path_safe


def resample_audio(filepath, new_filepath, new_sr):
    if os.path.exists(new_filepath):
        return
    sox_path = shutil.which('sox')
    if sox_path is not None:
        subprocess.call(['sox', filepath.replace('\\', '/'), new_filepath.replace('\\', '/'),
                         'gain', '-1', 'rate', '-I', str(new_sr)])
    else:
        sig, sr = librosa.load(filepath, sr=new_sr, mono=False)
        if len(sig.shape) > 1:
            sig = sig.T
        write_wav(sig, sr, new_filepath)


def add_discourse_sound_info(corpus_context, discourse, filepath):
    with audioread.audio_open(filepath) as f:
        sample_rate = f.samplerate
        n_channels = f.channels
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
    user_path = os.path.expanduser('~')
    statement = '''MATCH (d:Discourse:{corpus_name}) where d.name = {{discourse_name}}
                    SET d.file_path = {{filepath}},
                    d.consonant_file_path = {{consonant_filepath}},
                    d.vowel_file_path = {{vowel_filepath}},
                    d.low_freq_file_path = {{low_freq_filepath}},
                    d.duration = {{duration}},
                    d.sampling_rate = {{sampling_rate}},
                    d.num_channels = {{n_channels}}'''.format(corpus_name=corpus_context.cypher_safe_name)
    corpus_context.execute_cypher(statement, filepath=filepath,
                                  consonant_filepath=consonant_path.replace(user_path, '~'),
                                  vowel_filepath=vowel_path.replace(user_path, '~'),
                                  low_freq_filepath=low_freq_path.replace(user_path, '~'),
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


def point_measures_from_csv(corpus_context, header_info):
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
        import_path = 'file:///{}'.format(make_path_safe(path))
        import_statement = '''
                USING PERIODIC COMMIT 2000
                LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
                MATCH (n:{phone_type}:{corpus_name}) where n.id = csvLine.id
                SET {new_properties}'''

        statement = import_statement.format(path=import_path,
                                            corpus_name=corpus_context.cypher_safe_name,
                                            phone_type=corpus_context.phone_name,
                                            new_properties=properties)
        corpus_context.execute_cypher(statement)
    for h in header_info.keys():
        if h == 'id':
            continue
        corpus_context.execute_cypher('CREATE INDEX ON :%s(%s)' % (corpus_context.phone_name, h))
    corpus_context.hierarchy.add_token_properties(corpus_context, corpus_context.phone_name,
                                                  [(h, t) for h, t in header_info.items() if h != 'id'])
    corpus_context.encode_hierarchy()
