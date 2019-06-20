.. _enrichment_subannotations:

************************
Subannotation enrichment
************************

Often there are details which we would like to include on a linguistic annotation (word, syllable, phone, etc.) which are
not a simple measure like a single value or a one value across time.
An example of this would be Voice Onset Time (VOT), where we have two distinct parts (voicing onset and burst) which cannot
just be reduced to a single value.

In PolyglotDB, we refer to these more complicated structures as *sub*-annotations as they provide details that cannot just be a single measure like formants or pitch.
These sub-annotations are always attached to a regular linguistic annotation, but they have all of their own properties.

So for example, a given phone token could have a ``vot`` subannotation on it, which would consist of several different values that are all related.
This would be the onset, burst or confidence (of the prediction) of the VOT in question.
This allows semantically linked measurements to be linked and treated as a single object with multiple values rather than several distinct measurements that happen to be related.

For information on querying subannotations, see :ref:`queries_subannotations`.
