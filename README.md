# Ancient Greek WordNet
A Python helper library for accessing and manipulating the Ancient Greek WordNet.

## Background
A WordNet is a lexico-conceptual database for a language. In a WordNet, a language's lexemes (nouns, verbs, adjectives, and adverbs) are grouped into sets of semantically related words called synsets (for "synonym sets"), which thus correspond to the senses that are lexicalized in the language. A WordNet also typically includes information about semantic relations (i.e., relations between synsets) and about lexical relations (i.e., relations between words). 

Lemmas have been assigned to synsets using an automated process, which is highly prone to producing 'false positives'. When manual review of the data has been completed, this Ancient Greek WordNet will become an integral component of the University of Exeter's TExtual semantic and syntactic search engine for electronic corpora of ancient languages, the WordNet will deliver the engine's ability to execute queries based on word meanings.

## Installation

After cloning the repository, all you need to do is compile the relevant SQLite databases:
```
>>> from greekwordnet.db import compile
>>> compile('greek')
```
You will need to do the same for the English and Italian synset databases:
```
>>> compile('english', 'synset)
>>> compile('italian', 'synset)
```
To make full use of the semantic data that is included in the MultiWordNet, you will also want to compile the list of common relations and semfield hierarchy:
```
>>> compile('common', 'relations', 'semfield', 'semfield_hierarchy')
```

### Basic usage
```
>>> from greekwordnet.greekwordnet import GreekWordNet
>>> from greekwordnet.transliterate import lat2grk
>>> GWN = GreekWordNet()
>>> GWN.lemmas  # all the lemmas currently in the WordNet

>>> phulattw = GWN.get_lemma('φυλάττω', 'v')
>>> phulattw - GWN.get_lemma(lat2grk("phula'ttw"), 'v')  # this may be easier in some circumstances
>>> phulattw.synonyms  # all lemmas that share a synset with 'abalieno'
>>> phulattw.antonyms
>>> phulattw.synsets
...

>>> synset = GWN.get_synset('n#07462736')  # you can find a synset directly, if you know its offset ID
>>> synset.lemmas
...
```
