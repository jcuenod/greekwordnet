====================================================================

MultiWordNet 
version: 1.5.0
Updated: August 2012

Copyright: FBK-irst, Via Sommarive 18, I-38050 Povo - Trento,  Italy 

====================================================================

Multiwordnet is a multilingual lexical database in which the Italian WordNet is 
strictly aligned with Princeton WordNet 1.6 (PWN). It has been built following the Expand Model. The Italian synsets are created in correspondence with the PWN synsets, whenever possible, and semantic relations are imported from the corresponding English synsets; i.e., we assume that if there are two synsets in PWN and a relation holding between them, the same relation holds between the corresponding synsets in Italian.

MultiWordNet (version 1.5.0) includes the Italian and English databases and Wordnet Domains version 2.0 (see http://wndomains.fbk.eu/).

MultiWordNet distribution is composed of 11 files, including 10 tables representing a dump of the mySQL database we are using, and 1 text file.

	 -------------------
	|  DB TABLE REPORT  |
	 -------------------

common_relation.sql	124762 records
english_frame.sql	 19543 records
english_index.sql	123786 records
english_relation.sql	 18839 records
english_synset.sql	102389 records
italian_index.sql	 45412 records 
italian_relation.sql	   396 records 
italian_synset.sql	 38741 records 
semfield.sql		 99995 records
semfield_hierarchy.sql	   168 records



	 ----------------------
	|  TABLES DESCRIPTION  |
	 ----------------------

----------------------
(1)COMMON_RELATION.SQL
----------------------

The table "common_relation" lists all the semantic relations that are common to all languages.

Each record contains four fields:
-type: kind of relation (see below the list of MultiWordNet relations and the corresponding symbols used to codify them);
-id_source: identifier of the source synset ("pos#offset", where pos is "n" for nouns, "v" for verbs, "a" for adjectives, and "r" for adverbs);
-id_target: identifier of the target synset ("pos#offset", where pos is "n" for nouns, "v" for verbs, "a" for adjectives and "r" for adverbs);
-status: "new" if the relation involves new synsets, i.e. synsets which are not in Princeton WordNet and have been created in MultiWordNet. When the relation involves synsets which are taken from Princeton WordNet the field is "NULL".

Examples:
INSERT INTO common_relation VALUES ('*','v#00001740','v#00003763',NULL);
INSERT INTO common_relation VALUES ('@','v#00002143','v#00001740',NULL);
 	
---------------------------------------------------
(2)ENGLISH_RELATION.SQL and (3)ITALIAN_RELATION.SQL
---------------------------------------------------

The tables "english_relation" and "italian_relation" contain the relations that are language dependent. These relations are instances of the standard lexical relations used in Princeton WordNet(e.g. antonymy, pertains to, etc.). Moreover, these tables contain a new type of semantic relation created within MultiWordNet, which is called "nearest". The nearest relation holds between an empty synset (a lexical gap) of a certain language and the synset with the most similar meaning in that language. There are only few instances of this relation codified so far. 

Each record contains six fields:
-type: kind of relation (see below the list of MultiWordNet relations and the corresponding symbols used to codify them);
-id_source: identifier of the source synset ("pos#offset");
-id_target: identifier of the target synset ("pos#offset");
-w_source: the source lemma (only for lexical relations);
-w_target: the target lemma (only for lexical relation);
-status: "new" if this relation involves a new synset or "NULL" if it involves synsets taken from Princeton WordNet. 	

Examples:
INSERT INTO english_relation VALUES ('!','v#00009549','v#00009666','rest','be_active',NULL);
INSERT INTO italian_relation VALUES ('|','n#N0002074','n#09593084','','','new');


-----------------------------------------------
(4)ENGLISH_SYNSET.SQL and (5)ITALIAN_SYNSET.SQL
-----------------------------------------------

The tables "english_synset" and "italian_synset" contain the English and Italian synsets (most of them are aligned with the Princeton WordNet but some are new ones). Also lexical gaps are specified in this file (see below).

Each record contains four fields:
-id: synset identifier ("pos#offset"). Either a Princeton WordNet identifier or a new synset identifier (beginning with "N");
-word: lemmas contained in the synset, separated by a space character. The tokens of multiwords are connected by "_". The word "GAP!" and "PSEUDOGAP!" are a special identifiers used to describe a lexical gaps;
-phrase(**): lemmas contained in the phraset, separated by a space character. The tokens of multiwords are connected by "_". 
-gloss: synsets may optionally have a gloss, composed by a definition and sometimes an  example.

Examples:
INSERT INTO english_synset VALUES ('n#00008864',' plant flora plant_life ',NULL,'a living organism lacking the power of locomotion');
INSERT INTO italian_synset VALUES ('n#00043525',' GAP! ',' errore_di_calcolo ',NULL);
INSERT INTO italian_synset VALUES ('a#02078908',' epocale ',' che_fa_epoca ','che caratterizza un\'epoca; \"una svolta epocale\"');


(**) With the term phrase we refer to a free combination of words (as opposed to lexical unit) which is currently used to express a concept. As these kinds of expressions are not lexical units, they cannot be put in the synset together with lexical units. Thus another data structure, called "Phraset", is linked to a synset and contains all the phrases related to that synset. 
As an example, the Italian free combination of words "strofinaccio dei piatti" is synonymous with the words "strofinaccio" and "canovaccio" but it is not a lexical unit. Thus, the English synset {dishrag, dishcloth} has a corresponding Italian synset {canovaccio, canavaccio, strofinaccio} which has also a phraset {strofinaccio_dei_piatti}. As another example, consider: English synset {advancement, progress}, Italian synset {avanzamento, sviluppo, progresso}, Italian phraset {passo_avanti, passo_in_avanti}. 


---------------------------------------------
(6)ENGLISH_INDEX.SQL and (7)ITALIAN_INDEX.SQL
---------------------------------------------

The tables "english_index" and "italian_index" contain the lists of the English and Italian lemmas. The purpose of these tables is to retrive very quickly the synset ids and the possible searches starting from a lemma in all its PoS. 

Each record contains five fields:
-lemma: contains the normalized lemma. Multiwords are connected by "_". The word "GAP!" and "PSEUDOGAP!" are a special identifiers used to describe a lexical gaps;
-id_n: contains the list of the synset ids (separated by a space character) in which the lemma is contained as a noun;
-id_v: contains the list of the synsets ids in which the lemma is present as a verb;
-id_a: contains the list of the synset ids in which the lemma is present as an adjective;
-id_r: contains the list of the synset ids in which the lemma is present as an adverb.

Examples:
INSERT INTO english_index VALUES ('shape','n#03952527 n#00015185 n#04055717 n#04562135 n#03685812 n#10430604 n#04554317','v#00474001 v#01139594 v#00095506','','');
INSERT INTO italian_index VALUES ('parlamentare',' n#07457674',' v#00518082','a#02590962',NULL);

---------------
(8)SEMFIELD.SQL   
---------------

The table "semfield" contains one or more domain labels (version 2.0) for each synset in MultiWordNet. Domain labels are language-independent and apply to both English and Italian synsets. However, for practical reasons, both English words and Italian translations of the domain labels are reported.

Each record of this table contains two fields:
-synset: identifier of the synset ("pos#offset");
-english: contains the list of the domain labels associated to that synset (different domains are separated by a space character) in English;	

Examples:
INSERT INTO semfield VALUES ('r#00078025','Administration Economy Law',);
INSERT INTO semfield VALUES ('n#00031741','Military',);



-------------------------
(9)SEMFIELD_HIERARCHY.SQL   
-------------------------

The table "semfield_hierarchy" contains the hierarchy of the 169 domain labels used to tag MultiWordNet synsets. 

Each record of this table contains five fields:
-code: progressive number associated to each domain, from 1 to 169.
-english: English name of the domain
-normal: the basic domain (second level of the hierarchy) to which the domain in the record refers
-hypers: the direct hypernym of the domain
-hypons: the direct hyponym(s) of the domain

Examples:
INSERT INTO semfield_hierarchy VALUES (25,'Sport','Sport','Free_Time','Badminton Baseball Basketball Cricket Football Golf Rugby Soccer Table_Tennis Tennis Volleyball Cycling Skating Skiing Hockey Mountaineering Rowing Swimming Sub Diving Racing Athletics Wrestling Boxing Fencing Archery Fishing Hunting Bowling');
INSERT INTO semfield_hierarchy VALUES (29,'Folklore','Anthropology','Ethnology','');


---------------------
(10)ENGLISH_FRAME.SQL
---------------------

The table "english_frame" contains the subcategorization frames of the English verbs. Up to now, Italian verbs do not have this kind of information.

Each record of this table contains three fields:
-id: identifier of the synset ("v#offset");
-frame_num: identifier of the subcategorization frame (see file "verb.frametext")
-lemma: the lemma in the synset to which the subcategorization frame applies. If the frame applies to all the lemmas in the synset the field contains a "*".

Examples:
INSERT INTO english_frame VALUES ('v#00182674',2,'*');
INSERT INTO english_frame VALUES ('v#00182674',8,'get_over');


-------------------
(11)VERB.FRAMESTEXT
-------------------

This text file contains the list of the 35 different kinds of subcategorization frames for English verbs, each identified by a progressive number from 1 to 35.

Examples:
1  Something ----s
35 Something ----s INFINITIVE

================================================================================

TABLE OF RELATIONS


Most of the relations are the same as in Wordnet 1.6. Only the "nearest", "has-role", "is-role-of", "composed-of" and "composes" relations have been added.
The complete list of the relations is showed below.


POS 	| type	|	description			| relation	| features | coded into DB
---------------------------------------------------------------------------------------------------------
NOUNS 	| !	| Antonyms				| antonym	| :lexical | YES
 	| @	| Hypernyms				| hypernym	|	   | YES
	| ~	| Hyponyms				| hyponym	|	   | NO (see the reverse rel @)
	| #m	| Holonyms (* is a member of)		| member-of	|	   | NO (see the reverse rel %m)
	| #s	| Holonyms (* is the substance of)	| substance-of	|	   | NO (see the reverse rel %s)
	| #p 	| Holonyms (* is a part of)		| part-of	|	   | NO (see the reverse rel %p)
	| %m	| Meronymys (members of *)		| has-member	|	   | YES
	| %s 	| Meronyms (substances of *)		| has-substance	|	   | YES
	| %p	| Meronymys (parts of *)		| has-part	|	   | YES
	| =	| Attributes (is a value of *)		| attribute	|	   | YES
	| |	| Synset nearest to *			| nearest	|	   | YES
	| +r	| Has role (role of *)			| has-role	| 	   | YES
	| -r	| Is role of (* is role of)		| is-role-of	| 	   | NO (see the reverse rel +r)
        | +c    | Composed-of (is composed of *)        | composed-of   | :lexical | YES
        | -c    | Composes (composes of *)              | composes      | :lexical | NO (see the reverse rel +c)

VERBS	| !	| Antonyms				| antonym	| :lexical | YES
	| @	| Hypernyms				| hypernym	|	   | YES
	| ~ 	| Hyponyms				| hyponym	|	   | NO (see the reverse rel @)
	| *  	| Entails doing				| entailment	|	   | YES
	| >	| Causes				| causes	|	   | YES
	| ^ 	| Also see				| also-see	|	   | YES
	| $  	| senses of * grouped by similarity	| verb-group	| new 1.6  | YES
	| |	| Synset nearest to *			| nearest	|	   | YES
	| +c	| Composed-of (is composed of *)	| composed-of	| :lexical | YES
	| -c	| Composes (composes of *)		| composes	| :lexical | NO (see the reverse rel +c)

ADJ	| !	| Antonyms				| antonym	| :lexical | YES
	| & 	| Similar to				| similar-to	|	   | YES
	| <	| Participle of verb			| participle	| :lexical | YES
 	| \	| Pertains to noun			| pertains-to	| :lexical | YES
	| =	| Value of (* is a value of)		| is-value-of	|	   | YES
	| ^	| Also see				| also-see	|	   | YES
	| |	| Synset nearest to *			| nearest	|	   | YES
	| +c	| Composed-of (is composed of *)	| composed-of	| :lexical | YES
	| -c	| Composes (composes of *)		| composes	| :lexical | NO (see the reverse rel +c)

ADV	| !	| Antonyms				| antonym	| :lexical | YES
	| \     | Derived from adjective		| derived-from	|	   | YES
	| |     | Synset nearest to *			| nearest	|	   | YES
	| +c	| Composed-of (is composed of *)	| composed-of	| :lexical | YES
	| -c	| Composes (composes of *)		| composes	| :lexical | NO (see the reverse rel +c)


=======================
Disk Space Requirements
=======================

The MultiWordNet database requires approximately 60MB of disk space, depending on the database.

