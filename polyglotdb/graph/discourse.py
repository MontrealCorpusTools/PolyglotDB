import os
import numpy as np
from scipy.io import wavfile
from scipy.signal import lfilter

import librosa

from resampy import resample

class LongSoundFile(object):
    cache_amount = 60
    def __init__(self, sound_file, initial_begin = None, initial_end = None):
        self.path = os.path.expanduser(sound_file.consonant_filepath)
        if not os.path.exists(self.path):
            self.path = os.path.expanduser(sound_file.vowel_filepath)
            if not os.path.exists(self.path):
                self.path = os.path.expanduser(sound_file.low_freq_filepath)

        self.mode = None


        self.duration = sound_file.duration
        self.num_channels = sound_file.n_channels
        if self.duration < self.cache_amount:
            self.mode = 'short'
            self.signal, self.sr = librosa.load(self.path, sr = None)
            if len(self.signal.shape) == 1:
                self.signal = self.signal.reshape((self.signal.shape[0],1))
            else:
                self.signal = self.signal.T
            self.preemph_signal = lfilter([1., -0.95], 1, self.signal, axis = 0)
            self.downsampled_1000 = resample(self.signal, self.sr, 1000, filter = 'kaiser_fast', axis = 0)
            self.downsampled_100 = resample(self.downsampled_1000, 1000, 100, filter = 'kaiser_fast', axis = 0)
            self.cached_begin = 0
            self.cached_end = self.duration
        else:
            self.mode = 'long'
            if initial_begin is not None:
                if initial_end is not None:
                    padding = self.cache_amount - (initial_end - initial_begin)
                    self.cached_begin = initial_begin - padding
                    self.cached_end = initial_end + padding
                else:
                    self.cached_begin = initial_begin - self.cache_amount / 2
                    self.cached_end = initial_begin + self.cache_amount / 2
                if self.cached_begin < 0:
                    self.cached_end -= self.cached_begin
                    self.cached_begin = 0
                if self.cached_end > self.duration:
                    diff = self.cached_end - self.duration
                    self.cached_end = self.duration
                    self.cached_begin -= diff
            else:
                self.cached_begin = 0
                self.cached_end = self.cache_amount
        self.refresh_cache()

    def update_times(self, begin, end):
        if begin < 0:
            begin = 0
        if end > self.duration:
            end = self.duration
        self.cached_begin, self.cached_end = begin, end
        self.refresh_cache()

    def refresh_cache(self):
        if self.mode == 'long':
            dur = self.cached_end - self.cached_begin
            self.signal, self.sr = librosa.load(self.path, sr = None,
                        offset = self.cached_begin, duration = dur, mono = False)
            if len(self.signal.shape) == 1:
                self.signal = self.signal.reshape((self.signal.shape[0],1))
            else:
                self.signal = self.signal.T
            self.preemph_signal = lfilter([1., -0.95], 1, self.signal, axis = 0)
            self.downsampled_1000 = resample(self.signal, self.sr, 1000, filter = 'kaiser_fast', axis = 0)
            self.downsampled_100 = resample(self.downsampled_1000, 1000, 100, filter = 'kaiser_fast', axis = 0)

    def visible_downsampled_1000(self, begin, end, channel = 0):
        if self.downsampled_1000 is None:
            return None
        begin -= self.cached_begin
        end -= self.cached_begin
        min_samp = int(np.floor(begin * 1000))
        max_samp = int(np.ceil(end * 1000))
        return self.downsampled_1000[min_samp:max_samp, channel]

    def visible_downsampled_100(self, begin, end, channel = 0):
        if self.downsampled_100 is None:
            return None
        begin -= self.cached_begin
        end -= self.cached_begin
        min_samp = int(np.floor(begin * 100))
        max_samp = int(np.ceil(end * 100))
        return self.downsampled_100[min_samp:max_samp, channel]

    def visible_signal(self, begin, end, channel = 0):
        if self.signal is None:
            return None
        begin -= self.cached_begin
        end -= self.cached_begin
        min_samp = int(np.floor(begin * self.sr))
        max_samp = int(np.ceil(end * self.sr))
        return self.signal[min_samp:max_samp, channel]

    def visible_preemph_signal(self, begin, end, channel = 0):
        if self.preemph_signal is None:
            return None
        begin -= self.cached_begin
        end -= self.cached_begin
        min_samp = int(np.floor(begin * self.sr))
        max_samp = int(np.ceil(end * self.sr))
        return self.preemph_signal[min_samp:max_samp, channel]

class DiscourseInspecter(object):
    def __init__(self, corpus_context, discourse_name, initial_begin = None, initial_end = None):
        self.corpus = corpus_context
        self.name = discourse_name
        self.sound_file = self.corpus.discourse_sound_file(self.name)
        self.cached_begin = None
        self.cached_end = None
        self.fully_cached = False

        if self.sound_file is not None and os.path.exists(self.sound_file.filepath):
            self.max_time = self.sound_file.duration
        else:
            h_type = self.corpus.hierarchy.highest
            highest = getattr(self.corpus, h_type)
            q = self.corpus.query_graph(highest)
            q = q.filter(highest.discourse.name == self.name)
            q = q.order_by(highest.end, descending = True)
            q = q.limit(1)
            self.max_time = q.all()[0].end
        self.speech_begin = None
        self.speech_end = None
        if self.sound_file is not None:
            self.speech_begin = self.sound_file.discourse.get('speech_begin')
            self.speech_end = self.sound_file.discourse.get('speech_end')

        if self.speech_begin is None:
            self.speech_begin = 0
        else:
            self.speech_begin = float(self.speech_begin)
        if self.speech_end is None:
            self.speech_end = self.max_time
        else:
            self.speech_end = float(self.speech_end)

        self._initialize_cache(initial_begin, initial_end)

    @property
    def cached_to_begin(self):
        if self.cached_begin <= self.speech_begin:
            return True
        return False

    @property
    def cached_to_end(self):
        if self.cached_end >= self.speech_end:
            return True
        return False

    def _initialize_cache(self, begin, end):
        q = self._base_discourse_query(begin, end)
        self.cache = [x for x in q.all()]
        if begin < 0:
            begin = 0
        if end > self.max_time:
            end = self.max_time
        self.cached_begin = begin
        self.cached_end = end

    def add_preceding(self, results):
        for r in results:
            r.corpus_context = self.corpus
        self.cache = results + self.cache
        self.update_cached_times()

    def add_following(self, results):
        for r in results:
            r.corpus_context = self.corpus
        self.cache += results
        self.update_cached_times()

    def update_cache(self, begin, end):
        if self.cached_begin is None or begin < self.cached_begin:
            q = self.preceding_cache_query(begin)
            self.add_preceding([x for x in q.all()])

        if self.cached_end is None or end > self.cached_end:
            q = self.following_cache_query(end)
            self.add_following([x for x in q.all()])

    def preceding_cache_query(self, begin = None):
        h_type = self.corpus.hierarchy.highest
        highest = getattr(self.corpus, h_type)
        if self.cache:
            q = self._base_discourse_query(begin = begin, end = self.cache[0].begin)
        else:
            q = self._base_discourse_query(begin = begin)
        return q

    def following_cache_query(self, end = None):
        h_type = self.corpus.hierarchy.highest
        highest = getattr(self.corpus, h_type)
        if self.cache:
            q = self._base_discourse_query(end = end, begin = self.cache[-1].end)
        else:
            q = self._base_discourse_query(end = end)
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
            if self.cached_begin <= self.speech_begin and self.cached_end >= self.speech_end:
                self.fully_cached = True

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
        if len(formant_list) == 0:
            return None
        formant_dict = {'F1': np.array([[x.time, x.F1] for x in formant_list]),
                        'F2': np.array([[x.time, x.F2] for x in formant_list]),
                        'F3': np.array([[x.time, x.F3] for x in formant_list])}
        return formant_dict

    def formants_from_begin(self, begin, end, channel = 0):
        formant_list = self.corpus.get_formants(self.name, begin, end, channel)
        if len(formant_list) == 0:
            return None
        formant_dict = {'F1': np.array([[x.time - begin, x.F1] for x in formant_list]),
                        'F2': np.array([[x.time - begin, x.F2] for x in formant_list]),
                        'F3': np.array([[x.time - begin, x.F3] for x in formant_list])}
        return formant_dict

    def pitch(self, begin = None, end = None, channel = 0):
        pitch_list = self.corpus.get_pitch(self.name, begin, end, channel)
        if len(pitch_list) == 0:
            return None
        pitch_list = np.array([[x.time, x.F0] for x in pitch_list])
        return pitch_list

    def pitch_from_begin(self, begin, end, channel = 0):
        pitch_list = self.corpus.get_pitch(self.name, begin, end, channel)
        if len(pitch_list) == 0:
            return None
        pitch_list = np.array([[x.time - begin, x.F0] for x in pitch_list])
        return pitch_list

    def get_acoustics(self, time, channel = 0):
        acoustics = {}
        pitch = self.pitch(time - 0.5, time + 0.5, channel = channel)
        if pitch is None:
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
        if formants is None:
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
