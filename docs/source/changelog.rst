
*********
Changelog
*********

Version 1.3.2
=============

* Removed usage of Python 3.12-only features for compatibility with Python 3.9

Version 1.3.1
=============

* Refined acoustic track related functionalities.
* Upgraded denpencies: praatio to version 6.x, conch to version 0.4.0
* Added import track from csv functionality.

Version 1.3.0
=============

* Updated Neo4j Cypher queries to be compatible with Neo4j 5.x syntax.
* Upgraded Neo4j compatibility to version 5.22 and Java compatibility to Java 21.
* Updated the packaging process for smooth installation across platforms.
* Made Conda a required installation dependency.

Version 1.2.1
=============

* Upgraded compatible praatio package to 5.0
* Restored parsing empty intervals from TextGrids
* Added `CorpusContext.analyze_formant_points` function similar to be comparable to other formant analysis workflows

Version 1.2
===========

* Upgraded Neo4j compatibility to 4.3.3
* Upgraded InfluxDB compatibility to 1.8.9
* Changed Praat TextGrid handling to use praatio 4.1
* Phone parsing no longer includes blank intervals (i.e. silences), so preceding and following phone calculations have changed
* Update speaker adjusted pitch algorithm to use octave based min and max pitch rather than the more permissive standard deviation approach

Version 1.0
===========

* Added functionality to analyze voice-onset-time through AutoVOT
* Added functionality to analyze formant points and tracks using a refinement process based on vowel formant prototypes
* Added ability to enrich tokens from CSV
* Added parser for TextGrids generated from the Web-MAUS aligner
* Optimized loading of corpora for lower-memory computers
* Optimized queries involving acoustic tracks
