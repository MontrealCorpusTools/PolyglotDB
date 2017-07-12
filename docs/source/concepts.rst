.. _pgdb_concepts:

*******************
PolyglotDB Concepts
*******************

This document is intended to give a high level overview of the concepts
used in PolyglotDB.

Graph structure
===============

PRECEDENCE PICTURE NEEDED

The data in a PolyglotDB corpus is structured as an annotation graph.
Each node in the graph represents a linguistic object (annotation).
These nodes are organized in a precendence relationship in time (in the
above example XXX follows YYY).

HIERARCHICAL PICTURE NEEDED

In addition to precedence relations, hierarchical relationships are also
encoded.  In the above example the word XXX contains the phones Y, Y and Y.


Types versus tokens
-------------------

PICTURE ILLUSTRATING TYPES VERSUS TOKENS

There is a difference in how types and tokens are handled in a PolyglotDB corpus.
Broadly speaking, types refer to the abstract linguistic entities and have
properties that do not change from one production to the next.  For instance,
a word like *cat* has an orthography and an underlying/canonical transcription
that is the same regardless of who produces it.  On the other hand, one
instance of *cat* in one utterance will have timestamps (beginning and
end points in a sound file) that are different from all other productions
of *cat*.  Timestamps, thus, are properties of the token, not the type.

.. note: There is a bit of judgement call in what is a type property
   and what is a token property.  Something like part of speech could
   conceivably be either, with consequences for the data model.  If it is
   a type property, instances of *project* will either be the noun-type
   or the verb-type.  If part of speech is a token property, then all instances
   will have the same type *project*.



You could think of other ways of structuring the data.
The reason for splitting information into type and token is largely a
computational one, where we can save space by encoding type properties once
and not on every instance of that type.  Additionally, we can get some
performance improvements by filtering on types (if possible) rather than tokens,
because the space of type nodes is smaller than the space of token nodes.
For phones, you might have an inventory of 16 phone types, but the number
of phone tokens could be anything from a couple thousand to several hundred
thousand depending on the corpus.
Another approach would be to have single
type instances with many connections.  Querying on such a structure would
be pretty slow in Neo4j, and is less easily visualized, and it's less clear
where token information would go in this one.


PICTURE OF THE TWO ALTERNATIVE APPROACHES
