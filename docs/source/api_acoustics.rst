.. _acoustics_api:

*************
Acoustics API
*************

Classes
=======

.. autoclass:: polyglotdb.acoustics.classes.Track
   :members:

.. autoclass:: polyglotdb.acoustics.classes.TimePoint
   :members:



Segments
========

.. autofunction:: polyglotdb.acoustics.segments.generate_segments

.. autofunction:: polyglotdb.acoustics.segments.generate_vowel_segments

.. autofunction:: polyglotdb.acoustics.segments.generate_utterance_segments


Formants
========

.. autofunction:: polyglotdb.acoustics.formants.base.analyze_formant_tracks

.. autofunction:: polyglotdb.acoustics.formants.base.analyze_formant_points

.. autofunction:: polyglotdb.acoustics.formants.refined.analyze_formant_points_refinement

Conch function generators
-------------------------


.. autofunction:: polyglotdb.acoustics.formants.helper.generate_base_formants_function
.. autofunction:: polyglotdb.acoustics.formants.helper.generate_formants_point_function
.. autofunction:: polyglotdb.acoustics.formants.helper.generate_variable_formants_point_function

Intensity
=========

.. autofunction:: polyglotdb.acoustics.intensity.analyze_intensity


Conch function generators
-------------------------

.. autofunction:: polyglotdb.acoustics.intensity.generate_base_intensity_function

Pitch
=====

.. autofunction:: polyglotdb.acoustics.pitch.base.analyze_pitch


Conch function generators
-------------------------

.. autofunction:: polyglotdb.acoustics.pitch.helper.generate_pitch_function


VOT
===

.. autofunction:: polyglotdb.acoustics.vot.base.analyze_vot


Other
=====

.. autofunction:: polyglotdb.acoustics.other.analyze_track_script
.. autofunction:: polyglotdb.acoustics.other.analyze_script


Conch function generators
-------------------------

.. autofunction:: polyglotdb.acoustics.other.generate_praat_script_function
