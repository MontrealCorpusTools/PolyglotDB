import os
import numpy as np
from scipy.io import wavfile
from scipy.signal import lfilter

def load_sound_file(path):

    sr, signal = wavfile.read(path)
    signal = signal / 32768
    preemph_signal = lfilter([1., -0.95], 1, signal)
    return signal, preemph_signal, sr

class DiscourseInspecter(object):
    def __init__(self, corpus_context, discourse_name, initial_begin = None, initial_end = None):
        self.corpus = corpus_context
        self.name = discourse_name
        self.sound_file = self.corpus.discourse_sound_file(self.name)

        self.signal = None
        self.preemph_signal = None
        self.sr = None
        if self.sound_file is not None:
            self.corpus.sql_session.expunge(self.sound_file)

            if os.path.exists(self.sound_file.filepath):
                self.signal, self.preemph_signal, self.sr =load_sound_file(self.sound_file.filepath)

        if initial_begin is None:
            self.view_begin = 0
        else:
            self.view_begin = initial_begin
        if initial_end is None:
            self.view_end = 30
        else:
            self.view_end = initial_end

        self.max_time = self.sound_file.duration

        if self.max_time < self.view_end:
            self.view_end = self.max_time
        self._initialize_cache()

    def _initialize_cache(self):
        q = self._base_discourse_query()
        self.cache = [x for x in q.all()]
        if len(self.cache) == 0:
            self.cached_begin = None
            self.cached_end = None
        else:
            self.cached_begin = self.cache[0].begin
            if self.cached_begin > self.view_begin:
                self.cached_begin = self.view_begin
            self.cached_end = self.cache[-1].end
            if self.cached_end > self.view_end:
                self.cached_end = self.view_end

    def update_cache(self):
        h_type = self.corpus.hierarchy.highest
        highest = getattr(self.corpus, h_type)
        if self.cached_begin is None or self.view_begin < self.cached_begin:
            q = self._base_discourse_query()
            if self.cache:
                q = q.filter(highest.precedes(self.cache[0]))
            self.cache = [x for x in q.all()] + self.cache

        if self.cached_end is None or self.view_end > self.cached_end:
            q = self._base_discourse_query()
            if self.cache:
                q = q.filter(highest.follows(self.cache[-1]))

            self.cache += [x for x in q.all()]

        self.update_cached_times()

    def _base_discourse_query(self):
        h_type = self.corpus.hierarchy.highest
        highest = getattr(self.corpus, h_type)
        q = self.corpus.query_graph(highest)
        q = q.filter(highest.discourse.name == self.name)
        q = q.filter(highest.begin < self.view_end)
        q = q.filter(highest.end > self.view_begin)
        preloads = []
        if h_type in self.corpus.hierarchy.subannotations:
            for s in self.corpus.hierarchy.subannotations[h_type]:
                preloads.append(getattr(highest, s))
        for t in self.corpus.hierarchy.get_lower_types(h_type):
            preloads.append(getattr(highest, t))
        q = q.preload(*preloads)
        q = q.order_by(highest.begin)
        return q

    def update_cached_times(self):
        if len(self.cache) == 0:
            self.cached_begin = None
            self.cached_end = None
        else:
            self.cached_begin = self.cache[0].begin
            if self.cached_begin > self.view_begin:
                self.cached_begin = self.view_begin
            self.cached_end = self.cache[-1].end
            if self.cached_end > self.view_end:
                self.cached_end = self.view_end

    def update_times(self, begin, end):
        self.view_begin = begin
        self.view_end = end
        self.update_cache()

    def pan(self, time_delta):
        min_time = self.view_begin + time_delta
        max_time = self.view_end + time_delta
        if max_time > self.max_time:
            new_delta = time_delta - (max_time - self.max_time)
            min_time = self.view_begin + new_delta
            max_time = self.view_end + new_delta
        if min_time < 0:
            new_delta = time_delta - (min_time - self.min_time)
            min_time = self.view_begin + new_delta
            max_time = self.view_end + new_delta
        self.view_begin = min_time
        self.view_end = max_time
        self.update_cache()

    def zoom(self, factor, center_time):
        left_space = center_time - self.view_begin
        right_space = self.view_end - center_time

        min_time = center_time - left_space * factor
        max_time = center_time + right_space * factor

        if max_time > self.max_time:
            max_time = self.max_time
        if min_time < 0:
            min_time = self.min_time
        self.view_begin = min_time
        self.view_end = max_time
        self.update_cache()

    def __iter__(self):
        for a in self.cache:
            if a.end > self.view_begin and a.begin < self.view_end:
                yield a

    def __len__(self):
        return len([x for x in self])

    def formants(self):
        formant_list = self.corpus.get_formants(self.name, self.view_begin, self.view_end)
        formant_dict = {'F1': np.array([[x.time, x.F1] for x in formant_list]),
                        'F2': np.array([[x.time, x.F2] for x in formant_list]),
                        'F3': np.array([[x.time, x.F3] for x in formant_list])}
        return formant_dict

    def formants_from_begin(self):
        formant_list = self.corpus.get_formants(self.name, self.view_begin, self.view_end)
        formant_dict = {'F1': np.array([[x.time - self.view_begin, x.F1] for x in formant_list]),
                        'F2': np.array([[x.time - self.view_begin, x.F2] for x in formant_list]),
                        'F3': np.array([[x.time - self.view_begin, x.F3] for x in formant_list])}
        return formant_dict

    def pitch(self):
        pitch_list = self.corpus.get_pitch(self.name, self.view_begin, self.view_end)
        pitch_list = np.array([[x.time, x.F0] for x in pitch_list])
        return pitch_list

    def pitch_from_begin(self):
        pitch_list = self.corpus.get_pitch(self.name, self.view_begin, self.view_end)
        pitch_list = np.array([[x.time - self.view_begin, x.F0] for x in pitch_list])
        return pitch_list

    def get_acoustics(self, time):
        acoustics = {}
        pitch = self.pitch()
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
        formants = self.formants()
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

    def find_annotation(self, key, time):
        annotation = None
        for a in self:
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

    def visible_signal(self):
        min_samp = np.floor(self.view_begin * self.sr)
        max_samp = np.ceil(self.view_end * self.sr)
        return self.signal[min_samp:max_samp]

    def visible_preemph_signal(self):
        min_samp = np.floor(self.view_begin * self.sr)
        max_samp = np.ceil(self.view_end * self.sr)
        return self.preemph_signal[min_samp:max_samp]
