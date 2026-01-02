import os
import re
import subprocess
from datetime import datetime
from decimal import Decimal

import librosa
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

from polyglotdb.acoustics import (
    analyze_formant_points,
    analyze_formant_tracks,
    analyze_intensity,
    analyze_pitch,
    analyze_script,
    analyze_track_script,
    analyze_utterance_pitch,
    analyze_vot,
    update_utterance_pitch_track,
)
from polyglotdb.acoustics.classes import TimePoint, Track
from polyglotdb.acoustics.formants.helper import save_formant_point_data
from polyglotdb.acoustics.utils import generate_spectrogram, load_waveform
from polyglotdb.corpus.syllabic import SyllabicContext
from polyglotdb.io.importer.from_csv import import_track_csv, import_track_csvs


def sanitize_value(value, type):
    """
    Ensure a given value is of the correct type, if the value is in a list or tuple, the first element will be coerced

    Parameters
    ----------
    value : object
        Value to be coerced
    type : Type
        One of ``int``, ``float``, ``str``, ``bool``

    Returns
    -------
    object
        Value coerced to specified type
    """
    if not isinstance(value, type):
        if isinstance(value, (list, tuple)):
            value = value[0]
        try:
            value = type(value)
        except (ValueError, TypeError):
            value = None
    return value


def generate_filter_string(discourse, begin, end, channel, num_points, kwargs):
    """
    Constructs a filter string in InfluxDB query language (i.e., WHERE clause) based on relevant information from
    the Neo4j database

    Parameters
    ----------
    discourse : str
        Name of the audio file
    begin : float
        Beginning of the track in seconds
    end : float
        End of the track in seconds
    channel : int
        Which channel of the audio file
    num_points : int
        Number of points in the track to return, if 0 will return all raw measurements
    kwargs : dict
        Any extra filters

    Returns
    -------
    str
        InfluxDB query language WHERE clause to specify a track
    """
    extra_filters = [""""{}" = '{}' """.format(k, v) for k, v in kwargs.items()]
    filter_string = """WHERE "discourse" = '{}'
                            AND "time" >= {}
                            AND "time" <= {}
                            AND "channel" = '{}'
                            """
    if extra_filters:
        filter_string += "\nAND {}".format("\nAND ".join(extra_filters))
    if num_points:
        duration = end - begin
        time_step = duration / (num_points - 1)
        begin -= time_step / 2
        end += time_step / 2
        time_step *= 1000
        filter_string += "\ngroup by time({}ms) fill(null)".format(int(time_step))
    discourse = discourse.replace("'", r"\'")
    filter_string = filter_string.format(discourse, s_to_nano(begin), s_to_nano(end), channel)
    return filter_string


def s_to_nano(seconds):
    """
    Converts seconds (as a float or Decimal) to nanoseconds (as an int)

    Parameters
    ----------
    seconds : float or Decimal
        Seconds

    Returns
    -------
    int
        Nanoseconds
    """
    if not isinstance(seconds, Decimal):
        seconds = Decimal(seconds).quantize(Decimal("0.001"))
    return int(seconds * Decimal("1e9"))


def s_to_ms(seconds):
    """
    Converts seconds (as a float or Decimal) to milliseconds (as an int)

    Parameters
    ----------
    seconds : float or Decimal
        Seconds

    Returns
    -------
    int
        Milliseconds
    """
    if not isinstance(seconds, Decimal):
        seconds = Decimal(seconds).quantize(Decimal("0.001"))
    return int(seconds * Decimal("1e3"))


def to_seconds(time_string):
    """
    Converts a time string from InfluxDB into number of seconds to generate a time point in an audio file

    Parameters
    ----------
    time_string : str
        Formatted time string (either ``%Y-%m-%dT%H:%M:%S.%fZ`` or ``%Y-%m-%dT%H:%M:%SZ``

    Returns
    -------
    Decimal
        Time stamp quantized to the nearest millisecond
    """
    """Converts a string representing a date and time to a
    decimal representing number of seconds into the day"""
    try:
        d = datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S.%fZ")
        s = 60 * 60 * d.hour + 60 * d.minute + d.second + d.microsecond / 1e6
    except Exception:
        try:
            d = datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%SZ")
            s = 60 * 60 * d.hour + 60 * d.minute + d.second + d.microsecond / 1e6
        except Exception:
            m = re.search(r"T(\d{2}):(\d{2}):(\d+)\.(\d+)?", time_string)
            p = m.groups()

            s = 60 * 60 * int(p[0]) + 60 * int(p[1]) + int(p[2]) + int(p[3][:6]) / 1e6

    s = Decimal(s).quantize(Decimal("0.001"))
    return s


class AudioContext(SyllabicContext):
    """
    Class that contains methods for dealing with audio files for corpora
    """

    def load_audio(self, discourse, file_type):
        """
        Loads a given audio file at the specified sampling rate type (``consonant``, ``vowel`` or ``low_freq``).
        Consonant files have a sampling rate of 16 kHz, vowel files a sampling rate of 11 kHz, and low frequency files
        a sampling rate of 1.2 kHz.

        Parameters
        ----------
        discourse : str
            Name of the audio file to load
        file_type : str
            One of ``consonant``, ``vowel`` or ``low_freq``

        Returns
        -------
        numpy.array
            Audio signal
        int
            Sampling rate of the file
        """
        sound_file = self.discourse_sound_file(discourse)
        if file_type == "consonant":
            path = os.path.expanduser(sound_file.consonant_file_path)
        elif file_type == "vowel":
            path = os.path.expanduser(sound_file.vowel_file_path)
        elif file_type == "low_freq":
            path = os.path.expanduser(sound_file.low_freq_file_path)
        else:
            path = os.path.expanduser(sound_file.file_path)
        signal, sr = librosa.load(path, sr=None)
        return signal, sr

    def load_waveform(self, discourse, file_type="consonant", begin=None, end=None):
        """
        Loads a segment of a larger audio file.  If ``begin`` is unspecified, the segment will start at the beginning of
        the audio file, and if ``end`` is unspecified, the segment will end at the end of the audio file.

        Parameters
        ----------
        discourse : str
            Name of the audio file to load
        file_type : str
            One of ``consonant``, ``vowel`` or ``low_freq``
        begin : float, optional
            Timestamp in seconds
        end : float, optional
            Timestamp in seconds

        Returns
        -------
        numpy.array
            Audio signal
        int
            Sampling rate of the file
        """
        sf = self.discourse_sound_file(discourse)
        if file_type == "consonant":
            file_path = sf["consonant_file_path"]
        elif file_type == "vowel":
            file_path = sf["vowel_file_path"]
        elif file_type == "low_freq":
            file_path = sf["low_freq_file_path"]
        else:
            file_path = sf["file_path"]
        return load_waveform(file_path, begin, end)

    def generate_spectrogram(self, discourse, file_type="consonant", begin=None, end=None):
        """
        Generate a spectrogram from an audio file. If ``begin`` is unspecified, the segment will start at the beginning of
        the audio file, and if ``end`` is unspecified, the segment will end at the end of the audio file.

        Parameters
        ----------
        discourse : str
            Name of the audio file to load
        file_type : str
            One of ``consonant``, ``vowel`` or ``low_freq``
        begin : float
            Timestamp in seconds
        end : float
            Timestamp in seconds

        Returns
        -------
        numpy.array
            Spectrogram information
        float
            Time step between each window
        float
            Frequency step between each frequency bin
        """
        signal, sr = self.load_waveform(discourse, file_type, begin, end)
        return generate_spectrogram(signal, sr)

    def analyze_pitch(
        self,
        source="praat",
        algorithm="base",
        absolute_min_pitch=50,
        absolute_max_pitch=500,
        adjusted_octaves=1,
        stop_check=None,
        call_back=None,
        multiprocessing=True,
    ):
        """
        Analyze pitch tracks and save them to the database.

        See :meth:`polyglotdb.acoustics.pitch.base.analyze_pitch` for more details.

        Parameters
        ----------
        source : str
            Program to use for analyzing pitch, either ``praat`` or ``reaper``
        algorithm : str
            Algorithm to use, ``base``, ``gendered``, or ``speaker_adjusted``
        absolute_min_pitch : int
            Absolute pitch floor
        absolute_max_pitch : int
            Absolute pitch ceiling
        adjusted_octaves : int
            How many octaves around the speaker's mean pitch to set the speaker adjusted pitch floor and ceiling
        stop_check : callable
            Function to check whether processing should stop early
        call_back : callable
            Function to report progress
        multiprocessing : bool
            Flag whether to use multiprocessing or threading
        """
        analyze_pitch(
            self,
            source,
            algorithm,
            stop_check=stop_check,
            call_back=call_back,
            multiprocessing=multiprocessing,
            absolute_min_pitch=absolute_min_pitch,
            absolute_max_pitch=absolute_max_pitch,
            adjusted_octaves=adjusted_octaves,
        )

    def analyze_utterance_pitch(self, utterance, source="praat", **kwargs):
        """
        Analyze a single utterance's pitch track.

        See :meth:`polyglotdb.acoustics.pitch.base.analyze_utterance_pitch` for more details.

        Parameters
        ----------
        utterance : str
            Utterance ID from Neo4j
        source : str
            Program to use for analyzing pitch, either ``praat`` or ``reaper``
        kwargs
            Additional settings to use in analyzing pitch

        Returns
        -------
        :class:`~polyglotdb.acoustics.classes.Track`
            Pitch track
        """
        return analyze_utterance_pitch(self, utterance, source, **kwargs)

    def update_utterance_pitch_track(self, utterance, new_track):
        """
        Save a pitch track for the specified utterance.

        See :meth:`polyglotdb.acoustics.pitch.base.update_utterance_pitch_track` for more details.

        Parameters
        ----------
        utterance : str
            Utterance ID from Neo4j
        new_track : list or :class:`~polyglotdb.acoustics.classes.Track`
            Pitch track

        Returns
        -------
        int
            Time stamp of update
        """
        return update_utterance_pitch_track(self, utterance, new_track)

    def analyze_vot(
        self,
        classifier,
        stop_label="stops",
        stop_check=None,
        call_back=None,
        multiprocessing=False,
        overwrite_edited=False,
        vot_min=5,
        vot_max=100,
        window_min=-30,
        window_max=30,
    ):
        """
        Compute VOTs for stops and save them to the database.

        See :meth:`polyglotdb.acoustics.vot.base.analyze_vot` for more details.

        Parameters
        ----------
        classifier : str
            Path to an AutoVOT classifier model
        stop_label : str
            Label of subset to analyze
        vot_min : int
            Minimum VOT in ms
        vot_max : int
            Maximum VOT in ms
        window_min : int
            Window minimum in ms
        window_max : int
            Window maximum in Ms
        overwrite_edited : bool
            Overwrite VOTs with the "edited" property set to true, if this is true
        call_back : callable
            call back function, optional
        stop_check : callable
            stop check function, optional
        multiprocessing : bool
            Flag to use multiprocessing, otherwise will use threading
        """
        analyze_vot(
            self,
            classifier,
            stop_label=stop_label,
            stop_check=stop_check,
            call_back=call_back,
            multiprocessing=multiprocessing,
            overwrite_edited=overwrite_edited,
            vot_min=vot_min,
            vot_max=vot_max,
            window_min=window_min,
            window_max=window_max,
        )

    def analyze_formant_points(
        self, stop_check=None, call_back=None, multiprocessing=True, vowel_label=None
    ):
        """
        Compute formant tracks and save them to the database

        See :meth:`polyglotdb.acoustics.formants.base.analyze_formant_points` for more details.

        Parameters
        ----------
        stop_check : callable
            Function to check whether to terminate early
        call_back : callable
            Function to report progress
        multiprocessing : bool
            Flag to use multiprocessing, defaults to True, if False uses threading
        vowel_label : str, optional
            Optional subset of phones to compute tracks over.  If None, then tracks over utterances are computed.
        """
        data = analyze_formant_points(
            self,
            stop_check=stop_check,
            call_back=call_back,
            multiprocessing=multiprocessing,
            vowel_label=vowel_label,
        )
        save_formant_point_data(self, data)

    def analyze_formant_tracks(
        self,
        source="praat",
        stop_check=None,
        call_back=None,
        multiprocessing=True,
        vowel_label=None,
    ):
        """
        Compute formant tracks and save them to the database

        See :meth:`polyglotdb.acoustics.formants.base.analyze_formant_tracks` for more details.

        Parameters
        ----------
        source : str
            Program to compute formants
        stop_check : callable
            Function to check whether to terminate early
        call_back : callable
            Function to report progress
        multiprocessing : bool
            Flag to use multiprocessing, defaults to True, if False uses threading
        vowel_label : str, optional
            Optional subset of phones to compute tracks over.  If None, then tracks over utterances are computed.
        """
        analyze_formant_tracks(
            self,
            source=source,
            stop_check=stop_check,
            call_back=call_back,
            multiprocessing=multiprocessing,
            vowel_label=vowel_label,
        )

    def analyze_intensity(
        self, source="praat", stop_check=None, call_back=None, multiprocessing=True
    ):
        """
        Compute intensity tracks and save them to the database

        See :meth:`polyglotdb.acoustics.intensity..analyze_intensity` for more details.

        Parameters
        ----------
        source : str
            Program to compute intensity (only ``praat`` is supported)
        stop_check : callable
            Function to check whether to terminate early
        call_back : callable
            Function to report progress
        multiprocessing : bool
            Flag to use multiprocessing, defaults to True, if False uses threading
        """
        analyze_intensity(self, source, stop_check, call_back, multiprocessing=multiprocessing)

    def analyze_script(
        self,
        subset=None,
        annotation_type=None,
        script_path=None,
        duration_threshold=0.01,
        padding=0,
        arguments=None,
        stop_check=None,
        call_back=None,
        multiprocessing=True,
        file_type="consonant",
    ):
        """
        Use a Praat script to analyze annotation types in the corpus.  The Praat script must return properties per phone (i.e.,
        point measures, not a track), and these properties will be saved to the Neo4j database.

        See :meth:`polyglotdb.acoustics.other..analyze_script` for more details.

        Parameters
        ----------
        subset : str, optional
            the name of an already encoded subset of an annotation type, on which the analysis will be run
        annotation_type : str
            the type of annotation that the analysis will go over
        script_path : str
            Path to the Praat script
        duration_threshold : float
            Minimum duration that phones should be to be analyzed
        arguments : list
            Arguments to pass to the Praat script
        stop_check : callable
            Function to check whether to terminate early
        call_back : callable
            Function to report progress
        multiprocessing : bool
            Flag to use multiprocessing, defaults to True, if False uses threading
        file_type : str
            Sampling rate type to use, one of ``consonant``, ``vowel``, or ``low_freq``

        Returns
        -------
        list
            List of the names of newly added properties to the Neo4j database
        """
        return analyze_script(
            self,
            subset=subset,
            annotation_type=annotation_type,
            script_path=script_path,
            duration_threshold=duration_threshold,
            padding=padding,
            arguments=arguments,
            stop_check=stop_check,
            call_back=call_back,
            multiprocessing=multiprocessing,
        )

    def analyze_track_script(
        self,
        acoustic_name,
        properties,
        script_path=None,
        subset=None,
        annotation_type="phone",
        duration_threshold=0.01,
        padding=0,
        arguments=None,
        call_back=None,
        file_type="consonant",
        stop_check=None,
        multiprocessing=True,
    ):
        """
        Use a Praat script to analyze phones in the corpus.  The Praat script must return a track, and these tracks will
        be saved to the InfluxDB database.

        See :meth:`polyglotdb.acoustics.other..analyze_track_script` for more details.

        Parameters
        ----------
        acoustic_name : str
            Name of the acoustic measure
        properties : list
            List of tuples of the form (``property_name``, ``Type``)
        script_path : str
            Path to the Praat script
        duration_threshold : float
            Minimum duration that phones should be to be analyzed
        annotation_type : str
            Name of the annotation to analyze
        subset : str
            Name of the subset of the annotation type to analyze
        arguments : list
            Arguments to pass to the Praat script
        stop_check : callable
            Function to check whether to terminate early
        call_back : callable
            Function to report progress
        multiprocessing : bool
            Flag to use multiprocessing, defaults to True, if False uses threading
        file_type : str
            Sampling rate type to use, one of ``consonant``, ``vowel``, or ``low_freq``
        """
        return analyze_track_script(
            self,
            acoustic_name=acoustic_name,
            properties=properties,
            script_path=script_path,
            subset=subset,
            annotation_type=annotation_type,
            duration_threshold=duration_threshold,
            padding=padding,
            arguments=arguments,
            call_back=call_back,
            file_type=file_type,
            stop_check=stop_check,
            multiprocessing=multiprocessing,
        )

    def reset_formant_points(self):
        """
        Reset formant point measures encoded in the corpus
        """
        encoded_props = []
        for prop in ["F1", "F2", "F3", "B1", "B2", "B3", "A1", "A2", "A3"]:
            if self.hierarchy.has_token_property("phone", prop):
                encoded_props.append(prop)
        self.query_graph(getattr(self, self.phone_name)).set_properties(
            **{x: None for x in encoded_props}
        )

    def genders(self):
        """
        Gets all values of speaker property named ``gender`` in the Neo4j database

        Returns
        -------
        list
            List of gender values
        """
        res = self.execute_cypher(
            """MATCH (s:Speaker:{corpus_name}) RETURN s.gender as gender""".format(
                corpus_name=self.cypher_safe_name
            )
        )
        genders = set()
        for s in res:
            g = s["gender"]
            if g is None:
                g = ""
            genders.add(g)
        return sorted(genders)

    def reset_acoustics(self):
        """
        Reset all acoustic measures currently encoded
        """
        self.acoustic_client().drop_database(self.corpus_name)
        if self.hierarchy.acoustics:
            self.hierarchy.acoustic_properties = {}
            self.encode_hierarchy()

    def reset_acoustic_measure(self, acoustic_type):
        """
        Reset a given acoustic measure

        Parameters
        ----------
        acoustic_type : str
            Name of the acoustic measurement to reset
        """
        self.acoustic_client().query("""DROP MEASUREMENT "{}";""".format(acoustic_type))
        if acoustic_type in self.hierarchy.acoustics:
            self.hierarchy.acoustic_properties = {
                k: v for k, v in self.hierarchy.acoustic_properties.items() if k != acoustic_type
            }
            self.encode_hierarchy()

    def reset_vot(self):
        """
        Reset all VOT measurements in the corpus
        """
        self.execute_cypher(
            """MATCH (v:vot:{corpus_name}) DETACH DELETE v""".format(
                corpus_name=self.cypher_safe_name
            )
        )
        if "phone" in self.hierarchy.subannotations:
            if "vot" in self.hierarchy.subannotations["phone"]:
                self.hierarchy.subannotation_properties.pop("vot")
                self.hierarchy.subannotations["phone"].remove("vot")
                self.encode_hierarchy()

    def acoustic_client(self):
        """
        Generate a client to connect to the InfluxDB for the corpus

        Returns
        -------
        InfluxDBClient
            Client through which to run queries and writes
        """
        client = InfluxDBClient(**self.config.acoustic_connection_kwargs)
        databases = client.get_list_database()
        if self.corpus_name not in databases:
            client.create_database(self.corpus_name)
        return client

    def discourse_audio_directory(self, discourse):
        """
        Return the directory for the stored audio files for a discourse
        """
        return os.path.join(self.config.audio_dir, discourse)

    def discourse_sound_file(self, discourse):
        """
        Get details for the audio file paths for a specified discourse.

        Parameters
        ----------
        discourse : str
            Name of the audio file in the corpus

        Returns
        -------
        dict
            Information for the audio file path
        """
        statement = (
            """MATCH (d:Discourse:{corpus_name}) WHERE d.name = $discourse_name return d""".format(
                corpus_name=self.cypher_safe_name
            )
        )
        results = self.execute_cypher(statement, discourse_name=discourse)
        for r in results:
            d = r["d"]
            break
        else:
            raise Exception("Could not find discourse {}".format(discourse))
        return d

    def utterance_sound_file(self, utterance_id, file_type="consonant"):
        """
        Generate an audio file just for a single utterance in an audio file.

        Parameters
        ----------
        utterance_id : str
            Utterance ID from Neo4j
        file_type : str
            Sampling rate type to use, one of ``consonant``, ``vowel``, or ``low_freq``

        Returns
        -------
        str
            Path to the generated sound file
        """
        q = (
            self.query_graph(self.utterance)
            .filter(self.utterance.id == utterance_id)
            .columns(
                self.utterance.begin.column_name("begin"),
                self.utterance.end.column_name("end"),
                self.utterance.discourse.name.column_name("discourse"),
            )
        )
        utterance_info = q.all()[0]
        path = os.path.join(
            self.discourse_audio_directory(utterance_info["discourse"]),
            "{}_{}.wav".format(utterance_id, file_type),
        )
        if os.path.exists(path):
            return path
        fname = self.discourse_sound_file(utterance_info["discourse"])[
            "{}_file_path".format(file_type)
        ]
        subprocess.call(
            [
                "sox",
                fname,
                path,
                "trim",
                str(utterance_info["begin"]),
                str(utterance_info["end"] - utterance_info["begin"]),
            ]
        )
        return path

    def has_all_sound_files(self):
        """
        Check whether all discourses have a sound file

        Returns
        -------
        bool
            True if a sound file exists for each discourse name in corpus,
            False otherwise
        """
        if self._has_all_sound_files is not None:
            return self._has_all_sound_files
        discourses = self.discourses
        for d in discourses:
            sf = self.discourse_sound_file(d)
            if sf is None:
                break
            if not os.path.exists(sf.file_path):
                break
        else:
            self._has_all_sound_files = True
        self._has_all_sound_files = False
        return self._has_all_sound_files

    @property
    def has_sound_files(self):
        """
        Check whether any discourses have a sound file

        Returns
        -------
        bool
            True if there are any sound files at all, false if there aren't
        """

        if self._has_sound_files is None:
            self._has_sound_files = False
            for d in self.discourses:
                sf = self.discourse_sound_file(d)
                if sf["file_path"] is not None:
                    self._has_sound_files = True
                    break
        return self._has_sound_files

    def execute_influxdb(self, query):
        """
        Execute an InfluxDB query for the corpus

        Parameters
        ----------
        query : str
            Query to run

        Returns
        -------
        :class:`influxdb.resultset.ResultSet`
            Results of the query
        """
        client = self.acoustic_client()
        try:
            result = client.query(query)
        except InfluxDBClientError:
            print("There was an issue with the following query:")
            print(query)
            raise
        return result

    def get_utterance_acoustics(self, acoustic_name, utterance_id, discourse, speaker):
        """
        Get acoustic for a given utterance and time range

        Parameters
        ----------
        acoustic_name : str
            Name of acoustic track
        utterance_id : str
            ID of the utterance from the Neo4j database
        discourse : str
            Name of the discourse
        speaker : str
            Name of the speaker

        Returns
        -------
        :class:`polyglotdb.acoustics.classes.Track`
            Track object
        """
        properties = [x[0] for x in self.hierarchy.acoustic_properties[acoustic_name]]
        property_names = ["{}".format(x) for x in properties]
        columns = '"time", {}'.format(", ".join(property_names))
        speaker = speaker.replace("'", r"\'")  # Escape apostrophes
        discourse = discourse.replace("'", r"\'")  # Escape apostrophes
        if utterance_id is not None:
            query = """select {} from "{}"
                            WHERE "utterance_id" = '{}'
                            AND "discourse" = '{}'
                            AND "speaker" = '{}';""".format(
                columns, acoustic_name, utterance_id, discourse, speaker
            )
        else:
            query = """select {} from "{}"
                            WHERE "discourse" = '{}'
                            AND "speaker" = '{}';""".format(
                columns, acoustic_name, discourse, speaker
            )
        result = self.execute_influxdb(query)
        track = Track()
        for r in result.get_points(acoustic_name):
            s = to_seconds(r["time"])
            p = TimePoint(s)
            for name in properties:
                p.add_value(name, r[name])
            track.add(p)
        return track

    def get_acoustic_measure(
        self,
        acoustic_name,
        discourse,
        begin,
        end,
        channel=0,
        relative_time=False,
        **kwargs,
    ):
        """
        Get acoustic for a given discourse and time range

        Parameters
        ----------
        acoustic_name : str
            Name of acoustic track
        discourse : str
            Name of the discourse
        begin : float
            Beginning of time range
        end : float
            End of time range
        channel : int, defaults to 0
            Channel of the audio file
        relative_time : bool, defaults to False
            Flag for retrieving relative time instead of absolute time
        kwargs : kwargs
            Tags to filter on

        Returns
        -------
        :class:`polyglotdb.acoustics.classes.Track`
            Track object
        """
        begin = Decimal(begin).quantize(Decimal("0.001"))
        end = Decimal(end).quantize(Decimal("0.001"))
        num_points = kwargs.pop("num_points", 0)
        filter_string = generate_filter_string(discourse, begin, end, channel, num_points, kwargs)

        properties = [x[0] for x in self.hierarchy.acoustic_properties[acoustic_name]]
        property_names = ["{}".format(x) for x in properties]
        if num_points:
            columns = ", ".join(["mean({})".format(x) for x in property_names])
        else:
            columns = '"time", {}'.format(", ".join(property_names))
        query = """select {} from "{}"
                        {};""".format(
            columns, acoustic_name, filter_string
        )
        result = self.execute_influxdb(query)
        track = Track()
        for r in result.get_points(acoustic_name):
            s = to_seconds(r["time"])
            if relative_time:
                s = (s - begin) / (end - begin)
            p = TimePoint(s)
            for name in properties:
                p.add_value(name, r[name])
            track.add(p)
        return track

    def _save_measurement_tracks(self, acoustic_name, tracks, speaker):
        data = []

        measures = self.hierarchy.acoustic_properties[acoustic_name]
        for seg, track in tracks.items():
            if not len(track.keys()):
                continue
            file_path, _, _, channel, utterance_id = (
                seg.file_path,
                seg.begin,
                seg.end,
                seg.channel,
                seg["utterance_id"],
            )
            res = self.execute_cypher(
                "MATCH (d:Discourse:{corpus_name}) where d.low_freq_file_path = $file_path OR "
                "d.vowel_file_path = $file_path OR "
                "d.consonant_file_path = $file_path "
                "RETURN d.name as name".format(corpus_name=self.cypher_safe_name),
                file_path=file_path,
            )
            for r in res:
                discourse = r["name"]
            phone_type = getattr(self, self.phone_name)
            min_time = min(track.keys())
            max_time = max(track.keys())
            q = self.query_graph(phone_type).filter(phone_type.discourse.name == discourse)
            q = q.filter(phone_type.utterance.id == utterance_id)
            q = q.filter(phone_type.end >= min_time).filter(phone_type.begin <= max_time)
            columns = [
                phone_type.label.column_name("label"),
                phone_type.begin.column_name("begin"),
                phone_type.end.column_name("end"),
                phone_type.word.label.column_name("word_label"),
            ]
            if "syllable" in self.annotation_types:
                columns.append(phone_type.syllable.label.column_name("syllable_label"))
                q = q.columns(*columns).order_by(phone_type.begin)
                phones = [
                    (
                        x["label"],
                        x["begin"],
                        x["end"],
                        x["word_label"],
                        x["syllable_label"],
                    )
                    for x in q.all()
                ]
            else:
                q = q.columns(*columns).order_by(phone_type.begin)
                phones = [(x["label"], x["begin"], x["end"], x["word_label"]) for x in q.all()]
            for time_point, value in track.items():
                fields = {}
                for name, type in measures:
                    v = sanitize_value(value[name], type)
                    if v is not None:
                        fields[name] = v
                    elif type in [int, float]:
                        fields[name] = type(-1)
                if not fields:
                    continue
                label = None
                for i, p in enumerate(phones):
                    if p[1] > time_point:
                        break
                    label = p[0]
                    if "syllable" in self.annotation_types:
                        syllable_label = p[4]
                    word_label = p[3]
                    if i == len(phones) - 1:
                        break
                else:
                    label = None
                if label is None:
                    continue
                t_dict = {
                    "speaker": speaker,
                    "discourse": discourse,
                    "channel": channel,
                }
                fields["phone"] = label
                fields["word"] = word_label
                fields["utterance_id"] = utterance_id
                if "syllable" in self.annotation_types:
                    fields["syllable"] = syllable_label
                d = {
                    "measurement": acoustic_name,
                    "tags": t_dict,
                    "time": s_to_ms(time_point),
                    "fields": fields,
                }
                data.append(d)
        self.acoustic_client().write_points(data, batch_size=1000, time_precision="ms")

    def _save_measurement(self, sound_file, track, acoustic_name, **kwargs):
        if not len(track.keys()):
            return
        if isinstance(sound_file, str):
            sound_file = self.discourse_sound_file(sound_file)
        if sound_file is None:
            return
        measures = self.hierarchy.acoustic_properties[acoustic_name]
        if kwargs.get("channel", None) is None:
            kwargs["channel"] = 0
        data = []
        tag_dict = {}
        if isinstance(sound_file, str):
            kwargs["discourse"] = sound_file
        else:
            kwargs["discourse"] = sound_file["name"]
        utterance_id = kwargs.pop("utterance_id", None)
        tag_dict.update(kwargs)
        phone_type = getattr(self, self.phone_name)
        min_time = min(track.keys())
        max_time = max(track.keys())
        q = self.query_graph(phone_type).filter(phone_type.discourse.name == kwargs["discourse"])
        q = q.filter(phone_type.end >= min_time).filter(phone_type.begin <= max_time)
        columns = [
            phone_type.label.column_name("label"),
            phone_type.begin.column_name("begin"),
            phone_type.end.column_name("end"),
            phone_type.word.label.column_name("word_label"),
            phone_type.speaker.name.column_name("speaker"),
        ]
        column_labels = ["label", "begin", "end", "word_label", "speaker"]
        if "utterance" in self.annotation_types:
            columns.append(phone_type.syllable.label.column_name("utterance_id"))
            column_labels.append("utterance_id")
        if "syllable" in self.annotation_types:
            columns.append(phone_type.syllable.label.column_name("syllable_label"))
            column_labels.append("syllable_label")
        q = q.columns(*columns).order_by(phone_type.begin)
        phones = [{y: x[y] for y in column_labels} for x in q.all()]
        for time_point, value in track.items():
            fields = {}
            for name, type in measures:
                v = sanitize_value(value[name], type)
                if v is not None:
                    fields[name] = v
            if not fields:
                continue
            label = None
            speaker = None
            word_label = None
            syllable_label = None
            for i, p in enumerate(phones):
                if p["begin"] > time_point:
                    break
                label = p["label"]
                speaker = p["speaker"]
                if "syllable" in self.annotation_types:
                    syllable_label = p["syllable_label"]
                word_label = p["word_label"]
                if utterance_id is None:
                    utterance_id = p.get("utterance_id", None)
                if i == len(phones) - 1:
                    break
            if speaker is None:
                continue
            t_dict = {"speaker": speaker}
            t_dict.update(tag_dict)
            if utterance_id is not None:
                fields["utterance_id"] = utterance_id
            fields["phone"] = label
            fields["word"] = word_label
            if "syllable" in self.annotation_types:
                fields["syllable"] = syllable_label
            d = {
                "measurement": acoustic_name,
                "tags": t_dict,
                "time": s_to_nano(time_point),
                "fields": fields,
            }
            data.append(d)
        self.acoustic_client().write_points(data, batch_size=1000)

    def save_acoustic_track(self, acoustic_name, discourse, track, **kwargs):
        """
        Save an acoustic track for a sound file

        Parameters
        ----------
        acoustic_name : str
            Name of the acoustic type
        discourse : str
            Name of the discourse
        track : :class:`~polyglotdb.acoustics.classes.Track`
            Track to save
        kwargs: kwargs
            Tags to save for acoustic measurements
        """
        self._save_measurement(discourse, track, acoustic_name, **kwargs)

    def save_acoustic_tracks(self, acoustic_name, tracks, speaker):
        """
        Save multiple acoustic tracks for a collection of analyzed segments

        Parameters
        ----------
        acoustic_name : str
            Name of the acoustic type
        tracks : iterable
            Iterable of :class:`~polyglotdb.acoustics.classes.Track` objects to save
        speaker : str
            Name of the speaker of the tracks
        """
        self._save_measurement_tracks(acoustic_name, tracks, speaker)

    def discourse_has_acoustics(self, acoustic_name, discourse):
        """
        Return whether a discourse has any specific acoustic values associated with it

        Parameters
        ----------
        acoustic_name : str
            Name of the acoustic type
        discourse : str
            Name of the discourse

        Returns
        -------
        bool
        """
        if acoustic_name not in self.hierarchy.acoustics:
            return False
        discourse = discourse.replace("'", r"\'")
        query = """select * from "{}" WHERE "discourse" = '{}' LIMIT 1;""".format(
            acoustic_name, discourse
        )
        result = self.execute_influxdb(query)
        if len(result) == 0:
            return False
        return True

    def encode_acoustic_statistic(
        self, acoustic_name, statistic, by_annotation=None, by_speaker=True
    ):
        """
        Computes and saves as type properties summary statistics on a by speaker or by phone basis (or both) for a
        given acoustic measure.


        Parameters
        ----------
        acoustic_name : str
            Name of the acoustic type
        statistic : str
            One of `mean`, `median`, `stddev`, `sum`, `mode`, `count`
        by_speaker : bool, defaults to True
            Flag for calculating summary statistic by speaker
        by_annotation : str, defaults to None
            One of annotation types to calculate summary statistic over


        """
        if not by_speaker and not by_annotation:
            raise (Exception("Please specify either by_annotation, by_speaker or both."))

        valid_annotation_types = [atype for atype in self.annotation_types if atype != "utterance"]

        if by_annotation and by_annotation not in valid_annotation_types:
            raise Exception(
                "Annotation type must be one of: {}.".format(", ".join(valid_annotation_types))
            )

        if acoustic_name not in self.hierarchy.acoustics:
            raise (
                ValueError(
                    "Acoustic measure must be one of: {}.".format(
                        ", ".join(self.hierarchy.acoustics)
                    )
                )
            )
        available_statistics = ["mean", "median", "stddev", "sum", "mode", "count"]
        if statistic not in available_statistics:
            raise ValueError(
                "Statistic name should be one of: {}.".format(", ".join(available_statistics))
            )

        acoustic_name = acoustic_name.lower()
        template = statistic + '("{0}") as "{0}"'
        statistic_template = "n.{statistic}_{measure} = d.{measure}"
        measures = {
            x[0]: template.format(x[0])
            for x in self.hierarchy.acoustic_properties[acoustic_name]
            if x[1] in [int, float]
        }
        if by_speaker and by_annotation:
            results = []
            annotation_map = {
                "phone": {
                    "attr": self.phones,
                    "field": "phone",
                    "neo4j_label": "phone_type",
                },
                "word": {
                    "attr": self.words,
                    "field": "word",
                    "neo4j_label": "word_type",
                },
                "syllable": {
                    "attr": self.syllables,
                    "field": "syllable",
                    "neo4j_label": "syllable_type",
                },
            }

            annotation_data = annotation_map[by_annotation]
            items = annotation_data["attr"]
            db_field = annotation_data["field"]
            neo4j_label = annotation_data["neo4j_label"]

            for item in items:
                query = """select {} from "{}"
                        where "{}" = '{}' group by "speaker";""".format(
                    ", ".join(measures),
                    acoustic_name,
                    db_field,
                    item.replace("'", r"\'"),
                )
                influx_result = self.execute_influxdb(query)

                for k, v in influx_result.items():
                    v_dict = list(v)[0]
                    result = {"speaker": k[1]["speaker"], db_field: item}
                    for measure in measures.keys():
                        result[measure] = v_dict[measure]
                    results.append(result)

            set_statements = [
                statistic_template.format(statistic=statistic, measure=measure)
                for measure in measures.keys()
            ]

            statement = """WITH $data as data
                        UNWIND data as d
                        MATCH (s:Speaker:{corpus_name}), (p:{neo4j_label}:{corpus_name})
                        WHERE p.label = d.{db_field} AND s.name = d.speaker
                        WITH p, s, d
                        MERGE (s)<-[n:spoken_by]-(p)
                        WITH n, d
                        SET {set_statements}""".format(
                corpus_name=self.cypher_safe_name,
                neo4j_label=neo4j_label,
                db_field=db_field,
                set_statements=", ".join(set_statements),
            )

        elif by_annotation:
            annotation_map = {
                "phone": {
                    "list_attr": self.phones,
                    "db_field": "phone",
                    "neo4j_label": "phone_type",
                },
                "word": {
                    "list_attr": self.words,
                    "db_field": "word",
                    "neo4j_label": "word_type",
                },
                "syllable": {
                    "list_attr": self.syllables,
                    "db_field": "syllable",
                    "neo4j_label": "syllable_type",
                },
            }

            annotation_data = annotation_map[by_annotation]
            items = annotation_data["list_attr"]
            db_field = annotation_data["db_field"]
            neo4j_label = annotation_data["neo4j_label"]

            results = []
            for item in items:
                query = """select {} from "{}"
                        where "{}" = '{}';""".format(
                    ", ".join(measures.values()),
                    acoustic_name,
                    db_field,
                    item.replace("'", r"\'"),
                )

                influx_result = self.execute_influxdb(query)

                result = {db_field: item}
                for k, v in influx_result.items():
                    v_dict = list(v)[0]
                    for measure in measures.keys():
                        result[measure] = v_dict[measure]
                results.append(result)

            set_statements = [
                statistic_template.format(statistic=statistic, measure=measure)
                for measure in measures.keys()
            ]

            statement = """WITH $data as data
                        UNWIND data as d
                        MATCH (n:{neo4j_label}:{corpus_name})
                        WHERE n.label = d.{db_field}
                        SET {set_statements}""".format(
                corpus_name=self.cypher_safe_name,
                neo4j_label=neo4j_label,
                db_field=db_field,
                set_statements=", ".join(set_statements),
            )
            self.hierarchy.add_type_properties(
                self,
                by_annotation,
                [("{}_{}".format(statistic, x), float) for x in measures.keys()],
            )

        elif by_speaker:
            query = """select {} from "{}" group by "speaker";""".format(
                ", ".join(measures), acoustic_name
            )
            influx_result = self.execute_influxdb(query)
            results = []

            for k, v in influx_result.items():
                v_dict = list(v)[0]
                result = {"speaker": k[1]["speaker"]}
                for measure in measures.keys():
                    result[measure] = v_dict[measure]
                results.append(result)

            set_statements = []
            for measure in measures.keys():
                set_statements.append(
                    statistic_template.format(statistic=statistic, measure=measure)
                )
            statement = """WITH $data as data
                            UNWIND data as d
                            MATCH (n:Speaker:{corpus_name})
                            WHERE n.name = d.speaker
                            SET {set_statements}""".format(
                corpus_name=self.cypher_safe_name,
                set_statements=", ".join(set_statements),
            )
            self.hierarchy.add_speaker_properties(
                self, [("{}_{}".format(statistic, x), float) for x in measures.keys()]
            )
        self.execute_cypher(statement, data=results)
        self.encode_hierarchy()

    def get_acoustic_statistic(
        self, acoustic_name, statistic, by_annotation=None, by_speaker=True
    ):
        """
        Computes summary statistics on a by speaker or by phone basis (or both) for a given acoustic measure.


        Parameters
        ----------
        acoustic_name : str
            Name of the acoustic type
        statistic : str
            One of `mean`, `median`, `stddev`, `sum`, `mode`, `count`
        by_speaker : bool, defaults to True
            Flag for calculating summary statistic by speaker
        by_annotation : str, defaults to None
            One of annotation types to calculate summary statistic over

        Returns
        -------
        dict
            Dictionary where keys are annotation/speaker/annotation-speaker pairs and values are the summary statistic
            of the acoustic measure

        """
        if acoustic_name not in self.hierarchy.acoustics:
            raise (
                ValueError(
                    "Acoustic measure must be one of: {}.".format(
                        ", ".join(self.hierarchy.acoustics)
                    )
                )
            )
        if not by_speaker and not by_annotation:
            raise (Exception("Please specify either by_annotation, by_speaker or both."))
        available_statistics = ["mean", "median", "stddev", "sum", "mode", "count"]
        if statistic not in available_statistics:
            raise ValueError(
                "Statistic name should be one of: {}.".format(", ".join(available_statistics))
            )

        valid_annotation_types = [atype for atype in self.annotation_types if atype != "utterance"]

        if by_annotation and by_annotation not in valid_annotation_types:
            raise Exception(
                "Annotation type must be one of: {}.".format(", ".join(valid_annotation_types))
            )

        annotation_map = {
            "phone": "phone_type",
            "word": "word_type",
            "syllable": "syllable_type",
        }

        prop_template = "n.{0} as {0}"
        measures = [
            "{}_{}".format(statistic, x[0])
            for x in self.hierarchy.acoustic_properties[acoustic_name]
            if x[1] in [int, float]
        ]
        returns = [prop_template.format(x) for x in measures]

        results = {}

        if by_annotation and by_speaker:
            annotation_label = annotation_map[by_annotation]
            statement = """MATCH (p:{annotation_label}:{corpus_name})-[n:spoken_by]->(s:Speaker:{corpus_name})
                WHERE ALL(prop IN {return_list} WHERE n[prop] is not null)
                RETURN COUNT(p) > 0 AS has_data
                LIMIT 1""".format(
                annotation_label=annotation_label,
                corpus_name=self.cypher_safe_name,
                return_list="[" + ", ".join("'{}'".format(r) for r in measures) + "]",
            )

            results = self.execute_cypher(statement)

            has_data = results[0]["has_data"] if results else False

            if not has_data:
                self.encode_acoustic_statistic(acoustic_name, statistic, by_annotation, by_speaker)

            statement = """MATCH (p:{annotation_label}:{corpus_name})-[n:spoken_by]->(s:Speaker:{corpus_name})
                        RETURN p.label AS annotation, s.name AS speaker, {return_list}""".format(
                annotation_label=annotation_label,
                corpus_name=self.cypher_safe_name,
                return_list=", ".join(returns),
            )

            results = self.execute_cypher(statement)
            results = {
                (x["speaker"], x["annotation"]): [(n, x[n]) for n in measures] for x in results
            }

        elif by_annotation:
            annotation_label = annotation_map[by_annotation]

            if not self.hierarchy.has_type_property(by_annotation, measures[0]):
                self.encode_acoustic_statistic(acoustic_name, statistic, by_annotation, by_speaker)

            statement = """MATCH (n:{annotation_label}:{corpus_name})
                        RETURN n.label AS annotation, {return_list}""".format(
                annotation_label=annotation_label,
                corpus_name=self.cypher_safe_name,
                return_list=", ".join(returns),
            )

            results = self.execute_cypher(statement)
            results = {x["annotation"]: [(n, x[n]) for n in measures] for x in results}

        elif by_speaker:
            if not self.hierarchy.has_speaker_property(measures[0]):
                self.encode_acoustic_statistic(acoustic_name, statistic, by_annotation, by_speaker)

            statement = """MATCH (n:Speaker:{corpus_name})
                        RETURN n.name AS speaker, {return_list}""".format(
                corpus_name=self.cypher_safe_name, return_list=", ".join(returns)
            )
            results = self.execute_cypher(statement)
            results = {x["speaker"]: [(n, x[n]) for n in measures] for x in results}
        return results

    def reset_relativized_acoustic_measure(self, acoustic_name):
        """
        Reset any relativized measures that have been encoded for a specified type of acoustics

        Parameters
        ----------
        acoustic_name : str
            Name of the acoustic type
        """
        if acoustic_name not in self.hierarchy.acoustics:
            raise (
                ValueError(
                    "Acoustic measure must be one of: {}.".format(
                        ", ".join(self.hierarchy.acoustics)
                    )
                )
            )
        measures = ", ".join(
            [
                '"{}"'.format(x[0])
                for x in self.hierarchy.acoustic_properties[acoustic_name]
                if x[1] in [int, float] and not x[0].endswith("relativized")
            ]
        )
        to_remove = [
            x[0]
            for x in self.hierarchy.acoustic_properties[acoustic_name]
            if x[0].endswith("relativized")
        ]
        client = self.acoustic_client()
        if "syllable" in self.annotation_types:
            query = """SELECT "phone", "syllable", "word", {measures}, "utterance_id"
        INTO "{name}_copy" FROM "{name}" GROUP BY *;""".format(
                name=acoustic_name, measures=measures
            )
        else:
            query = """SELECT "phone", "word", {measures}, "utterance_id"
            INTO "{name}_copy" FROM "{name}" GROUP BY *;""".format(
                name=acoustic_name, measures=measures
            )
        client.query(query)
        client.query('DROP MEASUREMENT "{}"'.format(acoustic_name))
        client.query('SELECT * INTO "{0}" FROM "{0}_copy" GROUP BY *'.format(acoustic_name))
        client.query('DROP MEASUREMENT "{}_copy"'.format(acoustic_name))
        self.hierarchy.remove_acoustic_properties(self, acoustic_name, to_remove)
        self.encode_hierarchy()

    def relativize_acoustic_measure(self, acoustic_name, by_annotation=None, by_speaker=True):
        """
        Relativize acoustic tracks by taking the z-score of the points (using by speaker or by annotation means and standard
        deviations, or both by-speaker, by annotation) and save them as separate measures, i.e., F0_relativized from F0.

        Parameters
        ----------
        acoustic_name : str
            Name of the acoustic measure
        by_speaker : bool, defaults to True
            Flag for relativizing by speaker
        by_annotation : str, defaults to None
            Flag for relativizing by annotation
        """
        if acoustic_name not in self.hierarchy.acoustics:
            raise ValueError(
                f'Acoustic measure must be one of: {", ".join(self.hierarchy.acoustics)}.'
            )

        if not by_speaker and not by_annotation:
            raise Exception("Relativization must be by annotation, speaker, or both.")

        valid_annotation_types = [atype for atype in self.annotation_types if atype != "utterance"]
        if by_annotation and by_annotation not in valid_annotation_types:
            raise Exception(
                f'Annotation type must be one of: {", ".join(valid_annotation_types)}.'
            )

        client = self.acoustic_client()

        template = 'mean("{0}") as mean_{0}, stddev("{0}") as sd_{0}'
        props = [
            x
            for x in self.hierarchy.acoustic_properties[acoustic_name]
            if x[1] in [int, float] and not x[0].endswith("relativized")
        ]
        statistics = {x[0]: template.format(x[0]) for x in props}
        aliases = {x[0]: ("mean_{}".format(x[0]), "sd_{}".format(x[0])) for x in props}

        summary_data = {}

        if by_annotation:
            db_field = by_annotation
        else:
            db_field = "phone"
        if by_annotation:
            for item in getattr(self, by_annotation + "s", []):
                if by_speaker:
                    query = """select {} from "{}"
                                where "{}" = '{}' group by "speaker";""".format(
                        ", ".join(statistics.values()),
                        acoustic_name,
                        db_field,
                        item.replace("'", r"\'"),
                    )
                    result = client.query(query)
                    for k, v in result.items():
                        v = list(v)
                        for measure, (mean_name, sd_name) in aliases.items():
                            summary_data[(k[1]["speaker"], item, measure)] = v[0].get(
                                mean_name
                            ), v[0].get(sd_name)
                else:
                    query = """select {} from "{}"
                                where "{}" = '{}';""".format(
                        ", ".join(statistics.values()),
                        acoustic_name,
                        db_field,
                        item.replace("'", r"\'"),
                    )
                    result = client.query(query)
                    for k, v in result.items():
                        v = list(v)
                        for measure, (mean_name, sd_name) in aliases.items():
                            summary_data[(item, measure)] = v[0].get(mean_name), v[0].get(sd_name)
        else:
            query = """select {} from "{}"
                        where "{}" != '' group by "speaker";""".format(
                ", ".join(statistics.values()), acoustic_name, db_field
            )
            result = client.query(query)
            for k, v in result.items():
                v = list(v)
                for measure, (mean_name, sd_name) in aliases.items():
                    summary_data[(k[1]["speaker"], measure)] = v[0].get(mean_name), v[0].get(
                        sd_name
                    )

        for s in self.speakers:
            safe_speaker = s.replace("'", r"\'")
            all_query = """select * from "{}"
                            where '{}' != '' and "speaker" = '{}';""".format(
                acoustic_name, db_field, safe_speaker
            )
            all_results = client.query(all_query)
            data = []
            for _, records in all_results.items():
                for t_dict in records:
                    annotation_value = t_dict.pop(db_field)
                    time_point = t_dict.pop("time")
                    t_dict.pop("utterance_id", "")
                    t_dict.pop("syllable", "")
                    t_dict.pop("word", "")
                    t_dict.pop("phone", "")
                    fields = {}

                    for measure, (mean_name, sd_name) in aliases.items():
                        if by_speaker and by_annotation:
                            mean_value, sd_value = summary_data[
                                (t_dict["speaker"], annotation_value, measure)
                            ]
                        elif by_annotation and not by_speaker:
                            mean_value, sd_value = summary_data[(annotation_value, measure)]
                        elif by_speaker:
                            mean_value, sd_value = summary_data[(t_dict["speaker"], measure)]
                        if sd_value is None:
                            continue
                        value = t_dict.pop(measure)
                        if value is None:
                            continue
                        new_value = t_dict.pop("{}_relativized".format(measure), None)
                        new_value = (value - mean_value) / sd_value
                        fields["{}_relativized".format(measure)] = new_value
                    if not fields:
                        continue
                    time_point = s_to_ms(to_seconds(time_point))
                    data.append(
                        {
                            "measurement": acoustic_name,
                            "tags": t_dict,
                            "time": time_point,
                            "fields": fields,
                        }
                    )

            client.write_points(data, batch_size=1000, time_precision="ms")
        self.hierarchy.add_acoustic_properties(
            self, acoustic_name, [(x[0] + "_relativized", float) for x in props]
        )
        self.encode_hierarchy()

    def reassess_utterances(self, acoustic_name):
        """
        Update utterance IDs in InfluxDB for more efficient querying if utterances have been re-encoded after acoustic
        measures were encoded

        Parameters
        ----------
        acoustic_name : str
            Name of the measure for which to update utterance IDs

        """
        if acoustic_name not in self.hierarchy.acoustics:
            raise (
                ValueError(
                    "Acoustic measure must be one of: {}.".format(
                        ", ".join(self.hierarchy.acoustics)
                    )
                )
            )
        client = self.acoustic_client()
        q = self.query_discourses()
        q = q.columns(
            self.discourse.name.column_name("name"),
            self.discourse.speakers.name.column_name("speakers"),
        )
        discourses = q.all()
        props = [x[0] for x in self.hierarchy.acoustic_properties[acoustic_name]]
        for d in discourses:
            discourse_name = d["name"]
            data = []
            for s in d["speakers"]:
                q = self.query_graph(self.utterance)
                q = q.filter(
                    self.utterance.discourse.name == discourse_name,
                    self.utterance.speaker.name == s,
                )
                q = q.order_by(self.utterance.begin)
                q = q.columns(
                    self.utterance.id.column_name("utterance_id"),
                    self.utterance.begin.column_name("begin"),
                    self.utterance.end.column_name("end"),
                )
                utterances = q.all()
                s = s.replace("'", r"\'")
                discourse_name = discourse_name.replace("'", r"\'")
                all_query = f"""select * from "{acoustic_name}"
                                where "phone" != '' and
                                "discourse" = '{discourse_name}' and
                                "speaker" = '{s}';"""
                all_results = client.query(all_query)
                cur_index = 0
                for _, r in all_results.items():
                    for t_dict in r:
                        _ = t_dict.pop("phone")
                        _ = t_dict.pop("utterance_id", "")
                        t_dict.pop("syllable", "")
                        t_dict.pop("word", "")
                        for m in props:
                            _ = t_dict.pop(m, None)

                        time_point = to_seconds(t_dict.pop("time"))
                        for i in range(cur_index, len(utterances)):
                            if utterances[i]["begin"] <= time_point <= utterances[i]["end"]:
                                cur_index = i
                                break
                        time_point = s_to_ms(time_point)
                        d = {
                            "measurement": acoustic_name,
                            "tags": t_dict,
                            "time": time_point,
                            "fields": {"utterance_id": utterances[cur_index]["utterance_id"]},
                        }
                        data.append(d)
            client.write_points(data, batch_size=1000, time_precision="ms")

    def save_track_from_csv(self, acoustic_name, path, properties):
        """
        Reads a CSV file containing measurement tracks and saves each track using the _save_measurement API.

        Parameters:
        corpus_context : object
            The corpus context for accessing the database and helper methods.
        acoustic_name : str
            The name of the acoustic measure.
        path : str
            Path to the CSV file containing the measurement data.
        properties : list
            list of properties to read from the csv
        discourse : str
            Name of the discourse to store the track.
        time_column : str
            Name of the column in the CSV that contains time.
        """
        import_track_csv(self, acoustic_name=acoustic_name, path=path, properties=properties)

    def save_track_from_csvs(self, acoustic_name, directory_path, properties):
        """
        Reads a directory of CSV files containing measurement tracks, identifies the corresponding utterance,
        and saves each track using the _save_measurement_tracks API.

        Parameters:
        corpus_context : object
            The corpus context for accessing the database and helper methods.
        acoustic_name : str
            The name of the acoustic measure.
        path : str
            Path to the CSV file containing the measurement data.
        properties : list
            list of properties to read from the csv
        discourse : str
            Name of the discourse to store the track.
        time_column : str
            Name of the column in the CSV that contains time.
        """
        import_track_csvs(self, acoustic_name, directory_path, properties)
