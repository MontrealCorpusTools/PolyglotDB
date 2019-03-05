
.. _EMU-SDMS: https://ips-lmu.github.io/EMU.html

.. _LaBB-CAT: http://labbcat.sourceforge.net/

.. _Bird & Liberman (1999): http://www.aclweb.org/anthology/W99-0301

.. _neo4j_implementation:

********************
Neo4j implementation
********************

This section details how PolyglotDB saves and structures data within Neo4j.

Annotation Graphs
=================

The basic formalism in PolyglotDB for modelling and storing transcripts is that of annotation graphs, originally proposed
by `Bird & Liberman (1999)`_.  In this formalism, transcripts are directed acyclic graphs.  Nodes in the graph represent
time points in the audio file and edges between the nodes represent annotations (such as phones, words, utterances, etc). This
style of graph is illustrated below.



.. figure:: _static/img/annotation_graph.png
    :align: center
    :alt: Image cannot be displayed in your browser

The annotation graph formalism has been implemented in other speech corpus management systems, in either SQL
(`LaBB-CAT`_) or custom file-based storage systems (`EMU-SDMS`_).  One of the principle goals in developing PolyglotDB
was to be scalable to large datasets (potentially hundreds of hours) and still have good performance in querying the database.
Initial implementations in SQL were not as fast as I would have liked, so Neo4j was selected as the storage backend.
Neo4j is a NoSQL graph database where nodes and edges are fundamental elements in both the storage and Cypher query language.
Given its active development and use in enterprise systems, it is the best choice for meeting the scalability and performance
considerations.

However, Neo4j prioritizes nodes far more than edges.  In general, their use case is primarily something like IMDB, for instance.
In such a case, you'll have nodes for movies, shows, actors, directors, crew, etc, each with different labels associated with them.
Edges represent relationships like "acted in", or "directed".  The nodes have the majority of the properties, like names, dates of birth,
gender, etc, and relationships are sparse/empty.  The annotation graph formalism has nodes being relatively sparse (just time point),
and the edges containing the properties (label, token properties, speaker information, etc). Neo4j uses indices to speed up queries,
but these are focused on node properties rather than edge properties (or were at the beginning of development).  As such,
the storage model was modified from the annotation graph formalism into something more node-based, seen below.


.. figure:: _static/img/neo4j_annotations.png
    :align: center
    :alt: Image cannot be displayed in your browser

Rather than time points as nodes, the actual annotations are nodes, and relationships between them are either hierarchical
(i.e., the phone :code:`P` is contained by the syllable :code:`P.AA1`, represented by solid lines in the figure above)
or precedence (the phone :code:`P` precedes the phone :code:`AA1`, represented by dashed lines in the figure above).
Each node has properties for begin and end time points, as well as any arbitrary encoded information
(i.e., part of speech tags).  Each node of a given annotation type (word, syllable, phone) is labelled as such in Neo4j,
speeding up queries.

A full list of node types in a fresh PolyglotDB Neo4j database is as follows:

.. code-block:: text

    :phone
    :phone_type
    :word
    :word_type
    :Speaker
    :Discourse
    :speech

.. note::

    A special tag for the corpus name is added to every node in the corpus, in case multiple corpora are imported in the
    same database

The following node types can further be added to via enrichment:

.. code-block:: text

    :pause
    :utterance
    :utterance_type (never really used)
    :syllable
    :syllable_type

The following is a list of all the relationship types in the Neo4j database:

.. code-block:: text

    :is_a (relation between type and token nodes)
    :precedes (precedence relation)
    :precedes_pause (precedence relation for pauses when encoded)
    :contained_by (hierarchical relation)
    :spoken_by (relation between tokens and speakers)
    :spoken_in (relation between tokens and discourses)
    :speaks_in (relation between speakers and discourses)
    :annotates (relation between annotations and subannotations)



Corpus hierarchy representation
===============================

Metadata about the corpus is stored in a graph hierarchy, which corresponds to a :class:`polyglotdb.structure.Hierarchy` object belonging to
:class:`polyglotdb.corpus.CorpusContext`
objects.  In the Neo4j graph, there is a :code:`Corpus` root node, with all encoded annotations linked as they would be
in an annotation graph for a given discourse (i.e., Utterance -> Word -> Syllable -> Phone in orange below).  These nodes contain
a list of properties that will be found on each node in the annotation graphs (i.e., :code:`label`, :code:`begin`, :code:`end`),
along with what type of data each property is (i.e., string, numeric, boolean, etc).  There will also be a property for :code:`subsets` that
is a list of all the token subsets of that annotation type.
Each of these
annotations are linked to type nodes (in blue below) that has a list of properties that belong to the type (i.e., in the figure below, word types
have :code:`label`, :code:`transcription` and :code:`frequency`).

.. figure:: _static/img/hierarchy.png
    :align: center
    :alt: Image cannot be displayed in your browser

In addition, if subannotations are encoded, they will be represented in the hierarchy graph as well (i.e., :code:`Burst`,
:code:`Closure`, and :code:`Intonation` in yellow above), along with all the properties they contain.  :code:`Speaker`
and :code:`Discourse` properties are encoded in the graph hierarchy object as well as any acoustics that have been encoded
and are stored in the InfluxDB portion of the database.