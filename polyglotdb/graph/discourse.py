import os
import numpy as np
from scipy.io import wavfile
from scipy.signal import lfilter

from resampy import resample

def load_sound_file(path):

    try:
        sr, signal = wavfile.read(path)
    except:
        return None, None, None
    signal = signal / 32768
    preemph_signal = lfilter([1., -0.95], 1, signal, axis = 0)
    downsampled_1000 = resample(signal, sr, 1000, filter = 'kaiser_fast', axis = 0)
    downsampled_100 = resample(downsampled_1000, 100, 100, filter = 'kaiser_fast', axis = 0)
    return signal, preemph_signal, sr, downsampled_1000, downsampled_100

class DiscourseInspecter(object):
    def __init__(self, corpus_context, discourse_name, initial_begin = None, initial_end = None):
        self.corpus = corpus_context
        self.name = discourse_name
        self.sound_file = self.corpus.discourse_sound_file(self.name)
        self.cached_begin = None
        self.cached_end = None
        self.signal = None
        self.preemph_signal = None
        self.sr = None
        if self.sound_file is not None:
            self.corpus.sql_session.expunge(self.sound_file)

            if os.path.exists(self.sound_file.filepath):
                (self.signal, self.preemph_signal, self.sr,
                self.downsampled_1000,
                self.downsampled_100) = load_sound_file(self.sound_file.filepath)

            self.max_time = self.sound_file.duration
            self.num_channels = self.sound_file.n_channels
        else:
            h_type = self.corpus.hierarchy.highest
            highest = getattr(self.corpus, h_type)
            q = self.corpus.query_graph(highest)
            q = q.filter(highest.discourse.name == self.name)
            q = q.order_by(highest.end, descending = True)
            q = q.limit(1)
            self.max_time = q.all()[0].end
            self.num_channels = 1

        self._initialize_cache(initial_begin, initial_end)

    def _initialize_cache(self, begin, end):
        print('initializing discourse cache')
        q = self._base_discourse_query(begin, end)
        self.cache = [x for x in q.all()]
        self.update_cached_times()
        print('done initializing', self.cached_begin, self.cached_end, len(self.cache))

    def add_preceding(self, results):
        self.cache = results + self.cache
        self.update_cached_times()

    def add_following(self, results):
        self.cache += results
        self.update_cached_times()

    def update_cache(self, begin, end):
        print(begin, end, self.cached_begin, self.cached_end)
        if self.cached_begin is None or begin < self.cached_begin:
            print('updating preceding')
            q = self.preceding_cache_query(begin)
            self.add_preceding([x for x in q.all()])

        if self.cached_end is None or end > self.cached_end:
            print('updating following')
            q = self.following_cache_query(end)
            self.add_following([x for x in q.all()])

    def preceding_cache_query(self, begin = None):
        h_type = self.corpus.hierarchy.highest
        highest = getattr(self.corpus, h_type)
        q = self._base_discourse_query(begin = begin)
        if self.cache:
            q = q.filter(highest.precedes(self.cache[0]))
        return q

    def following_cache_query(self, end = None):
        h_type = self.corpus.hierarchy.highest
        highest = getattr(self.corpus, h_type)
        q = self._base_discourse_query(end = end)
        if self.cache:
            q = q.filter(highest.follows(self.cache[-1]))
        return q

    def _base_discourse_query(self, begin = None, end = None):
        h_type = self.corpus.hierarchy.highest
        highest = getattr(self.corpus, h_type)
        q = self.corpus.query_graph(highest)
        q = q.filter(highest.discourse.name == self.name)
        if end is not None:
            q = q.filter(highest.begin < end)
        if begin is not None:
            q = q.filter(highest.end > begin)
        preloads = []
        if h_type in self.corpus.hierarchy.subannotations:
            for s in self.corpus.hierarchy.subannotations[h_type]:
                preloads.append(getattr(highest, s))
        for t in self.corpus.hierarchy.get_lower_types(h_type):
            preloads.append(getattr(highest, t))
        preloads.append(highest.speaker)
        preloads.append(highest.discourse)
        q = q.preload(*preloads)
        q = q.order_by(highest.begin)
        return q

    def update_cached_times(self):
        if len(self.cache) == 0:
            self.cached_begin = None
            self.cached_end = None
        else:
            if self.cached_begin is None or self.cached_begin > self.cache[0].begin:
                self.cached_begin = self.cache[0].begin
            if self.cached_end is None or self.cached_end < self.cache[-1].end:
                self.cached_end = self.cache[-1].end
        print('done updating', self.cached_begin, self.cache[0].begin, self.cached_end, self.cache[-1].end, len(self.cache))


    def update_times(self, begin, end):
        if begin < 0:
            begin = 0
        if end > self.max_time:
            end = self.max_time
        self.update_cache(begin, end)

    def __iter__(self):
        for a in self.cache:
            yield a

    def __len__(self):
        return len([x for x in self])

    def annotations(self, begin = None, end = None, channel = 0):
        for a in self.cache:
            if a.channel != channel:
                continue
            if begin is not None and a.end <= begin:
                continue
            if end is not None and a.begin >= end:
                continue
            yield a

    def formants(self, begin = None, end = None, channel = 0):
        formant_list = self.corpus.get_formants(self.name, begin, end, channel)
        formant_dict = {'F1': np.array([[x.time, x.F1] for x in formant_list]),
                        'F2': np.array([[x.time, x.F2] for x in formant_list]),
                        'F3': np.array([[x.time, x.F3] for x in formant_list])}
        return formant_dict

    def formants_from_begin(self, begin, end, channel = 0):
        formant_list = self.corpus.get_formants(self.name, begin, end, channel)
        formant_dict = {'F1': np.array([[x.time - begin, x.F1] for x in formant_list]),
                        'F2': np.array([[x.time - begin, x.F2] for x in formant_list]),
                        'F3': np.array([[x.time - begin, x.F3] for x in formant_list])}
        return formant_dict

    def pitch(self, begin = None, end = None, channel = 0):
        pitch_list = self.corpus.get_pitch(self.name, begin, end, channel)
        pitch_list = np.array([[x.time, x.F0] for x in pitch_list])
        return pitch_list

    def pitch_from_begin(self, begin, end, channel = 0):
        pitch_list = self.corpus.get_pitch(self.name, begin, end, channel)
        pitch_list = np.array([[x.time - begin, x.F0] for x in pitch_list])
        return pitch_list

    def get_acoustics(self, time, channel = 0):
        acoustics = {}
        pitch = self.pitch(time - 0.5, time + 0.5, channel = channel)
        if not pitch:
            acoustics['F0'] = None
        else:
            for i,p in enumerate(pitch):
                if p[0] > time:
                    if i != 0:
                        prev_time = pitch[i-1][0]
                        prev_pitch = pitch[i-1][1]
                        dur = p[0] - prev_time
                        cur_time = time - prev_time
                        percent = cur_time / dur
                        acoustics['F0'] = prev_pitch * percent + p[1] * (1 - percent)
                    else:
                        acoustics['F0'] = p[1]
                    break
            else:
                acoustics['F0'] = None
        formants = self.formants(time - 0.5, time + 0.5, channel = channel)
        if not formants:
            acoustics['F1'] = None
            acoustics['F2'] = None
            acoustics['F3'] = None
        else:
            for k,v in formants.items():
                for i,f in enumerate(v):
                    if f[0] > time:
                        if i != 0:
                            prev_time = v[i-1][0]
                            prev_formant = v[i-1][1]
                            dur = f[0] - prev_time
                            cur_time = time - prev_time
                            percent = cur_time / dur
                            acoustics[k] = prev_formant * percent + f[1] * (1 - percent)
                        else:
                            acoustics[k] = f[1]
                        break
        return acoustics

    def find_annotation(self, key, time, channel = 0):
        annotation = None
        for a in self:
            if a.channel != channel:
                continue
            if isinstance(key, tuple):
                elements = getattr(a, key[0])
                for e in elements:
                    subs = getattr(e, key[1])
                    for s in subs:
                        if time >= s.begin and time <= s.end:
                            annotation = s
                            break
                    if annotation is not None:
                        break
            elif key != a._type:
                elements = getattr(a, key)
                for e in elements:
                    if time >= e.begin and time <= e.end:
                        annotation = e
                        break
            elif time >= a.begin and time <= a.end:
                annotation = a
            if annotation is not None:
                break
        return annotation

    def visible_downsampled_1000(self, begin, end, channel = 0):
        if self.downsampled_1000 is None:
            return None
        min_samp = int(np.floor(begin * 1000))
        max_samp = int(np.ceil(end * 1000))
        return self.downsampled_1000[min_samp:max_samp, channel]

    def visible_downsampled_100(self, begin, end, channel = 0):
        if self.downsampled_100 is None:
            return None
        min_samp = int(np.floor(begin * 100))
        max_samp = int(np.ceil(end * 100))
        return self.downsampled_100[min_samp:max_samp, channel]

    def visible_signal(self, begin, end, channel = 0):
        if self.signal is None:
            return None
        min_samp = int(np.floor(begin * self.sr))
        max_samp = int(np.ceil(end * self.sr))
        return self.signal[min_samp:max_samp, channel]

    def visible_preemph_signal(self, begin, end, channel = 0):
        if self.preemph_signal is None:
            return None
        min_samp = int(np.floor(begin * self.sr))
        max_samp = int(np.ceil(end * self.sr))
        return self.preemph_signal[min_samp:max_samp, channel]