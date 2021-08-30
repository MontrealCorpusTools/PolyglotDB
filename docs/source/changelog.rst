
*********
Changelog
*********

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