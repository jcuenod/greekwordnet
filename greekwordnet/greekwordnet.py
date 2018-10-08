"""
A helper library for accessing and manipulating the Greek WordNet.
"""

import re
from sqlite3 import OperationalError
from typing import List, Generator, Iterable

from greekwordnet.db import connect


class POSError(Exception):
    pass


class Semfield(object):
    """
    Represents a semfield (semantic field) within the MultiWordNet.

    english: A descriptive name of the semfield in English.
    code: A unique identification code.
    synsets: A list of synset identification numbers falling within this semantic field.
    normal: The semfield that represents the basic category to which this semfield belongs.
    hypers: A list of semfields immediately superordinate to this semfield.
    hypons: A list of semfields immediately subordinate to this semfield.
    """

    def __new__(cls, english, code=None, language='common'):
        english = english.replace(' ', '_')
        try:
            common_semfield_hierarchy = connect("common", "semfield_hierarchy")

            if code:
                query = f'english="{english}" AND code="{code}"'
            else:
                query = f'english="{english}"'

            if common_semfield_hierarchy:
                common_semfield_hierarchy.execute(f'SELECT code, english FROM semfield_hierarchy WHERE {query}')
                results = common_semfield_hierarchy.fetchall()
            else:
                results = None
        except OperationalError:
            raise
        else:
            if not results:
                instance = None
            else:
                if len(results) > 1 and code is None:
                        results_codes = list()
                        for result in results:
                            results_codes.append(result[0])
                        raise ValueError(f'cannot disambiguate "{english}" between "{", ".join(results_codes)}"')
                else:
                    instance = super().__new__(cls)
                    instance._code = results[0][0]
                    instance._english = results[0][1]
                    instance._language = language
            return instance

    def __init__(self, english, code=None, language='common'):
        self._english = english
        self._code = code
        self._language = language
        self._synsets = None
        self._normal = None
        self._hypers = None
        self._hypons = None

    @property
    def language(self) -> str:
        return str(self._language)

    @property
    def synsets(self) -> List['Synset']:
        if not self._synsets:
            temp = list()
            try:
                common_semfield = connect("common", "semfield")

                if common_semfield:
                    common_semfield.execute(f'SELECT synset FROM semfield WHERE english LIKE "%{self._english}%"')
                    common_results = common_semfield.fetchall()
                else:
                    common_results = None
            except OperationalError:
                raise
            else:
                if common_results:
                    for result in common_results:
                        temp.append(Synset(result[0], self.language))
            try:
                language_semfield = connect(self.language, "semfield")

                if language_semfield:
                    language_semfield.execute(f'SELECT synset FROM semfield WHERE english LIKE "%{self._english}%"')
                    language_results = language_semfield.fetchall()
                else:
                    language_results = None
            except OperationalError:
                raise
            else:
                if language_results:
                    for result in language_results:
                        temp.append(Synset(result[0], self.language))
            self._synsets = temp
        return list(self._synsets)

    @property
    def hypers(self) -> List['Semfield']:
        if not self._hypers:
            temp = list()
            try:
                semfield_hierarchy = connect("common", "semfield_hierarchy")

                if semfield_hierarchy:
                    semfield_hierarchy.execute(f'SELECT hypers FROM semfield_hierarchy WHERE english="{self._english}" AND code="{self.code}"')
                    result = semfield_hierarchy.fetchone()
                else:
                    result = None
            except OperationalError:
                raise
            else:
                if result:
                    for hyper in result[0].split(' '):
                        if hyper and hyper != '':
                            semfield_hierarchy.execute(f'SELECT code, english FROM semfield_hierarchy WHERE english="{hyper}" AND code LIKE "{self.code[:2]}%"')
                            result = semfield_hierarchy.fetchone()

                            if result:
                                temp.append(Semfield(code=result[0], english=result[1]))
            self._hypers = temp
        return list(self._hypers)

    @property
    def hypons(self) -> List['Semfield']:
        if not self._hypons:
            temp = list()
            try:
                semfield_hierarchy = connect("common", "semfield_hierarchy")

                if semfield_hierarchy:
                    semfield_hierarchy.execute(f'SELECT hypons FROM semfield_hierarchy WHERE english="{self._english}" AND code="{self.code}"')
                    result = semfield_hierarchy.fetchone()
                else:
                    result = None
            except OperationalError:
                raise
            else:
                if result:
                    for hypon in result[0].split(' '):
                        if hypon is not None and hypon != '':
                            semfield_hierarchy.execute(f'SELECT code, english FROM semfield_hierarchy WHERE english="{hypon}" AND code LIKE "{self.code[:3]}%"')
                            result = semfield_hierarchy.fetchone()

                            if result:
                                temp.append(Semfield(code=result[0], english=result[1]))
            self._hypons = temp
        return list(self._hypons)

    @property
    def normal(self) -> 'Semfield':
        if not self._normal:
            try:
                semfield_hierarchy = connect("common", "semfield_hierarchy")

                if semfield_hierarchy:
                    semfield_hierarchy.execute(f'SELECT normal FROM semfield_hierarchy WHERE english="{self._english}" AND code="{self.code}"')
                    result = semfield_hierarchy.fetchone()
                else:
                    result = None
            except OperationalError:
                    raise
            else:
                if result:
                    semfield_hierarchy.execute(f'SELECT code, english FROM semfield_hierarchy WHERE english="{result[0]}" AND code LIKE "{self.code[:2]}%"')
                    result = semfield_hierarchy.fetchone()

                    if result:
                        self._normal = Semfield(code=result[0], english=result[1])
        return self._normal

    @property
    def code(self) -> str:
        if not self._code:
            try:
                semfield_hierarchy = connect("common", "semfield_hierarchy")

                if semfield_hierarchy:
                    semfield_hierarchy.execute(f"SELECT code FROM semfield_hierarchy WHERE english='{self._english}'")
                    result = semfield_hierarchy.fetchone()
                else:
                    result = None
            except OperationalError:
                raise
            else:
                if result and result[0]:
                    self._code = result[0]
        return str(self._code) if self._code else ''

    @property
    def english(self) -> str:
        return str(self._english)

    def __str__(self):
        return self._english.replace('_', ' ').title()

    def __repr__(self):
        return f"Semfield('{self.english}', '{self.code}')"


class Synset(object):
    """
    Represents a synset in a WordNet within the MultiWordNet.

    id: A unique identifier consisting of a part-of-speech tag ('n', 'v', 'a', or 'r') followed by # and an
         eight-digit offset number. For synsets of languages other than English, the first digit is typically
         an identifying character, but usage is not consistent across the MultiWordNet.
    language: The language of the WordNet instance to which the synset belongs.
    synset_language: The language for which the synset was originally defined.
    lemmas: A list of lemmas belonging to this synset in the given language.
    phrase: A list of phrases belonging to this synset in the given language.
    gloss: A gloss of the sense in English or in the language for which the synset was originally defined.
    """

    def __new__(cls, id: str, language: str):
        try:
            result = None
            language_synset = connect(cls.get_synset_language(id), "synset")

            if language_synset:
                language_synset.execute(f"SELECT * FROM {cls.get_synset_language(id)}_synset WHERE id='{id}'")
                result = language_synset.fetchone()
            if not result:
                language_synset = connect(language, "synset")
                if language_synset:
                    language_synset.execute(f"SELECT * FROM {language}_synset WHERE id='{id}'")
                    result = language_synset.fetchone()
            if not result:
                english_synset = connect("english", "synset")
                if english_synset:
                    english_synset.execute(f"SELECT * FROM english_synset WHERE id='{id}'")
                    result = english_synset.fetchone()
        except OperationalError:
            raise
        else:
            if result:
                instance = super().__new__(cls)
            else:
                instance = None
        return instance

    def __init__(self, id, language):
        self._id = id
        self._language = language
        self._relations = None
        self._semfield = None
        self._pos = None
        self._word = None
        self._phrase = None
        self._gloss = None

    @property
    def pos(self) -> str:
        if self._pos is None:
            self._pos = self.id[0]
        return str(self._pos)

    @property
    def offset(self) -> str:
        return str(self.id[2:])

    def get_relations(self, type: str) -> Generator['Relation', None, Iterable['Relation']]:
        if type in Relation.types[self.pos]:
            return (relation for relation in self.relations if relation.type == type)
        else:
            raise ValueError(f"No relation type '{type}' for '{self.pos}'!")

    @property
    def relations(self) -> List['Relation']:
        if not self._relations:
            temp = list()
            try:
                common_relation = connect("common", "relation")

                if common_relation:
                    common_relation.execute(f"SELECT * FROM common_relation WHERE id_source='{self.id}' OR id_target='{self.id}'")
                    results = common_relation.fetchall()

                    if results:
                        for result in results:
                            temp.append(Relation(result[0], result[1], result[2], result[3]))

                language_relation = connect(self.language, "relation")

                if language_relation:
                    language_relation.execute(f"SELECT * FROM {self.language}_relation WHERE id_source='{self.id}' OR id_target='{self.id}'")
                    results = language_relation.fetchall()

                    if results:
                        for result in results:
                            temp.append(Relation(result[0], result[1], result[2], result[3]))
            except OperationalError:
                raise
            else:
                self._relations = temp
        return list(self._relations)

    def relation_to(self, target: 'Synset') -> str:
        for relation in self.relations:
                if relation.target == target:
                    return relation.type

    @property
    def id(self) -> str:
        return str(self._id)

    @property
    def language(self) -> str:
        return str(self._language)

    @classmethod
    def get_synset_language(cls, id: str) -> str:
        """Returns the verbose language name for a given synset.

        :param id: A string of the form [pos#offset] identifying the synset.
        :return: The language name as a string.
        """
        _language_names = {
            'P': 'english',  # Portuguese
            'N': 'italian',
            'W': 'italian',  # English
            'Y': 'italian',
            'H': 'hebrew',
            'S': 'spanish',
            'L': 'greek',
            'R': 'romanian',
        }
        if id[2].isdigit():
            return 'english'
        else:
            return _language_names[id[2]]

    @property
    def semfield(self) -> List[Semfield]:
        if not self._semfield:
            temp = list()
            try:
                common_semfield = connect("common", "semfield")

                if common_semfield:
                    common_semfield.execute(f"SELECT english FROM semfield WHERE synset='{self.id}'")
                    result = common_semfield.fetchone()

                    if result:
                        for s in result[0].split(' '):
                            temp.append(Semfield(english=s, language=self.language))
                    else:
                        language_semfield = connect(self.language, "semfield")

                        if language_semfield:
                            language_semfield.execute(f"SELECT english FROM {self.language}_semfield WHERE synset='{self.id}'")
                            result = language_semfield.fetchone()

                            if result:
                                for s in result[0].split(' '):
                                    self._semfield.append(Semfield(english=s, language=self.language))
            except OperationalError:
                raise
            else:
                self._semfield = temp
        return list(self._semfield)

    @property
    def words(self) -> List['Lemma']:
        if not self._word:
            temp = list()
            _DB_COLUMN = {
                'n': 'id_n',
                'v': 'id_v',
                'a': 'id_a',
                'r': 'id_r',
            }

            try:
                language_synset = connect(self.language, "synset")

                if language_synset:
                    language_synset.execute(f"SELECT word FROM {self.language}_synset WHERE id='{self.id}'")
                    result = language_synset.fetchone()

                    if result:
                        if result[0] and result[0] != ' GAP! ':
                            temp = [Lemma(lemma, self.id[0], self.language) for lemma in result[0].strip().split(' ')]
                else:
                    language_index = connect(self.language, "index")

                    if language_index:
                        language_index.execute(f"SELECT lemma FROM {self.language}_index WHERE {_DB_COLUMN[self.pos]} LIKE '%{self.id}%';")
                        results = language_index.fetchall()

                        if results:
                            for result in results:
                                if result[0] != 'gap!':
                                    temp.append(Lemma(result[0], self.id[0], self.language))
            except OperationalError:
                raise
            else:
                self._word = temp
        return list(self._word)

    @property
    def phrases(self) -> List['Phrase']:
        """ Returns a list of phrases belonging to the synset """
        if not self._phrase:
            temp = list()
            try:
                language_synset = connect(self.language, "synset")

                if language_synset:
                    language_synset.execute(f"SELECT phrase FROM {self.language}_synset WHERE id='{self.id}'")
                    result = language_synset.fetchone()
                else:
                    result = None
            except OperationalError:
                raise
            else:
                if result:
                    if result[0] and result[0] != ' GAP! ':
                        temp = [Phrase(r, self.pos, self.language) for r in result[0].strip().split(' ')]
                self._phrase = temp
        return list(self._phrase)

    @property
    def gloss(self) -> str:
        if not self._gloss:
            try:
                language_synset = connect(self.get_synset_language(self.id), "synset")

                if language_synset:
                    language_synset.execute(f"SELECT gloss FROM {self.get_synset_language(self.id)}_synset WHERE id='{self.id}'")
                    result = language_synset.fetchone()
                else:
                    result = None
            except OperationalError:
                raise
            else:
                if result:
                    self._gloss = result[0]
        return str(self._gloss) if self._gloss else ''

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return str(self.gloss)

    def __repr__(self):
        return f"Synset('{self.id}', '{self.get_synset_language(self.id)}')"


class Morpho(object):
    """ Represents morphological information for a Lemma in the WordNet """

    def __new__(cls, lemma, pos, language='english'):
        try:
            language_morpho = connect(language, "morpho")

            if language_morpho:
                language_morpho.execute(f"SELECT * FROM {language}_morpho WHERE lemma='{lemma}' AND pos='{pos}';")
                result = language_morpho.fetchone()
            else:
                result = None
        except OperationalError:
            raise
        else:
            if result:
                instance = super(Morpho, cls).__new__(cls)
            else:
                instance = None
        return instance

    def __init__(self, lemma, pos, language):
        self._lemma = lemma
        self._pos = pos
        self._language = language
        self._id = None
        if language == 'greek':
            self._principal_parts = None
        self._irregular_forms = None
        self._alternative_forms = None
        self._pronunciation = None
        if language == 'hebrew':
            self._undotted = None
            self._dotted_without_dots = None
            self._variants = None
            self._translit_dotted = None
            self._translit_undotted = None
        self._miscellanea = None

    @property
    def language(self) -> str:
        return str(self._language)

    @property
    def lemma(self) -> str:
        return str(self._lemma)

    @property
    def lemma_verbose(self) -> str:
        if self.language == 'greek':
            i = self._lemma
            if self.pos == 'v':
                if len(self.principal_parts) == 3:
                    if self.group == '1': thematic_vowel = 'a'
                    elif self.group == '2': thematic_vowel = 'e'
                    elif self.group == '3': thematic_vowel = 'e'
                    else: thematic_vowel = 'i'
                    if self.voice == 'a':
                        ii = f"{self.principal_parts[0]}{thematic_vowel}re"
                        iii = f"{self.principal_parts[1]}isse"
                        iv = f"{self.principal_parts[2]}um"
                        _lemma = list((i, ii, iii, iv, self.group))
                    else:
                        ii = f"{self.principal_parts[0]}{thematic_vowel}ri"
                        iii = f"{self.principal_parts[2]}us sum"
                        _lemma = list((i, ii, iii, self.group))
                elif len(self.principal_parts) == 2:
                    ii = f"{self.principal_parts[0]}isse"
                    iii = f"{self.principal_parts[1]}"
                    _lemma = list((i, ii, iii, self.group))
            elif self.pos == 'n':
                if self.group == '1': genitive = 'ae' if self.number == 's' else "arum"
                elif self.group == '2': genitive = 'i' if self.number == 's' else "orum"
                elif self.group == '3': genitive = 'is' if self.number == 's' else "um"
                elif self.group == '4': genitive = 'us' if self.number == 's' else "uum"
                else: genitive = 'ēi' if self.number == 's' else "erum"
                ii = f"{self.principal_parts[0]}{genitive}"
                _lemma = list((i, ii, f"{self.gender}."))
            elif self.pos == 'a':
                if self.group == '1':
                    ii = f"{self.principal_parts[0]}a"
                    iii = f"{self.principal_parts[0]}um"
                    _lemma = list((i, ii, iii))
                elif self.group == '3':
                    if self.gender == 'm': # 3-termination
                        ii = f"{self.principal_parts[0]}is"
                        iii = f"{self.principal_parts[0]}e"
                        _lemma = list((i, ii, iii, 'm.f.n.'))
                    elif self.gender == 'c': # 2-termination
                        ii = f"{self.principal_parts[0]}e"
                        _lemma = list((i, ii, 'mf.n.'))
                    elif self.gender == 'a': # 1-termination
                        _lemma = list((i, 'mfn.'))
                elif self.pos == 'r':
                    if self.principal_parts:
                        _lemma = list((self._lemma, self.principal_parts[0], self.principal_parts[1]))
        else:
            _lemma = self._lemma
        return _lemma

    @property
    def id(self) -> str:
        if not self._id:
            try:
                language_morpho = connect(self.language, "morpho")

                if language_morpho:
                    language_morpho.execute(f"SELECT id FROM {self.language}_morpho WHERE lemma='{self.lemma}' and pos='{self.pos}';")
                    result = language_morpho.fetchone()
                else:
                    result = None
            except OperationalError:
                raise
            else:
                if result:
                    self._id = result[0]
        return str(self._id) if self._id else ''

    @property
    def irregular_forms(self) -> dict:
        if not self._irregular_forms:
            try:
                language_morpho = connect(self.language, "morpho")

                if language_morpho:
                    language_morpho.execute(f"SELECT irregular_forms FROM {self.language}_morpho WHERE lemma='{self.lemma}' and pos='{self.pos}';")
                    result = language_morpho.fetchone()
                else:
                    result = None
            except OperationalError:
                raise
            else:
                if result and result[0]:
                    self._irregular_forms = result[0]
        return [tuple(irregular_form.split('=')) for irregular_form in self._irregular_forms.strip().split(' ')] if self._irregular_forms else []

    @property
    def alternative_forms(self) -> dict:
        if not self._alternative_forms:
            try:
                language_morpho = connect(self.language, "morpho")

                if language_morpho:
                    language_morpho.execute(f"SELECT alternative_forms FROM {self.language}_morpho WHERE lemma='{self.lemma}' and pos='{self.pos}';")
                    result = language_morpho.fetchone()
                else:
                    result = None
            except OperationalError:
                raise
            else:
                if result and result[0]:
                    self._alternative_forms = result[0]
        return [tuple(alternative_form.split('=')) for alternative_form in self._alternative_forms.strip().split(' ')] if self._alternative_forms else []

    @property
    def principal_parts(self) -> List[str]:
        if not self._principal_parts:
            try:
                language_morpho = connect(self.language, "morpho")

                if language_morpho:
                    language_morpho.execute(f"SELECT principal_parts FROM {self.language}_morpho WHERE lemma='{self.lemma}' and pos='{self.pos}';")
                    result = language_morpho.fetchone()
                else:
                    result = None
            except OperationalError:
                raise
            else:
                if result and result[0]:
                    self._principal_parts = result[0]
        return self._principal_parts.strip().split(' ') if self._principal_parts else []

    @property
    def pronunciation(self) -> str:
        if not self._pronunciation:
            try:
                language_morpho = connect(self.language, "morpho")

                if language_morpho:
                    language_morpho.execute(f"SELECT pronunciation FROM {self.language}_morpho WHERE lemma='{self.lemma}' and pos='{self.pos}';")
                    result = language_morpho.fetchone()
                else:
                    result = None
            except OperationalError:
                raise
            else:
                if result:
                    self._pronunciation = result[0]
        return str(self._pronunciation) if self._pronunciation else ''


    @property
    def miscellanea(self) -> str:
        if not self._miscellanea:
            temp = ''
            try:
                language_morpho = connect(self.language, "morpho")

                if language_morpho:
                    language_morpho.execute(f"SELECT miscellanea FROM {self._language}_morpho WHERE lemma='{self._lemma}' and pos='{self._pos}';")
                    result = language_morpho.fetchone()
                else:
                    result = None
            except OperationalError:
                raise
            else:
                if result:
                    temp = result[0]
            self._miscellanea = temp
        return str(self._miscellanea)

    @property
    def pos(self) -> str:
        if not self._pos:
            groups = re.search(r'^([nvarpusct])[\S][\S][\S][\S][\S][\S][\S][\S][\S]$', self.miscellanea)
            self._pos = groups.group(1) if groups else ''
        return str(self._pos) if self._pos else ''

    @property
    def pos_verbose(self) -> str:
        _pos_types = {
            'n': 'noun',
            'v': 'verb',
            'a': 'adjective',
            'r': 'adverb',
            'p': 'pronoun',
            'u': 'punctuation',
            's': 'preposition',
            'c': 'conjunction',
            't': 'participle',
        }
        return str(_pos_types[self.pos])

    @property
    def person(self) -> str:
        if self.pos == 'v':
            groups = re.search(r'^[\S]([123])[\S][\S][\S][\S][\S][\S][\S][\S]$', self.miscellanea)
            return groups.group(1) if groups else ''
        else:
            return None

    @property
    def person_verbose(self) -> str:
        if self.pos == 'v':
            _person_types = {
                '1': '1st person',
                '2': '2nd person',
                '3': '3rd person',
            }
            return str(_person_types[self.person])
        else:
            return None

    @property
    def degree(self) -> str:
        if self.pos == 'a' or self.pos == 'r':
            groups = re.search(r'^[\S]([pcs])[\S][\S][\S][\S][\S][\S][\S][\S]$', self.miscellanea)
            return groups.group(1) if groups else ''
        else:
            return None

    @property
    def degree_verbose(self) -> str:
        if self.pos == 'a' or self.pos == 'r':
            _degree_types = {
                'p': 'positive',
                'c': 'comparative',
                's': 'superlative',
            }
            return str(_degree_types[self.degree])
        else:
            return None

    @property
    def number(self) -> str:
        groups = re.search(r'^[\S][\S]([sdp])[\S][\S][\S][\S][\S][\S][\S]$', self.miscellanea)
        return groups.group(1) if groups else ''

    @property
    def number_verbose(self) -> str:
        _number_types = {
            's': 'singular',
            'd': 'dual',
            'p': 'plural',
        }
        return str(_number_types[self.number])

    @property
    def tense(self) -> str:
        groups = re.search(r'^[\S][\S][\S]([pfiarlt])[\S][\S][\S][\S][\S][\S]$', self.miscellanea)
        return groups.group(1) if groups else ''

    @property
    def tense_verbose(self) -> str:
        _tense_types = {
            'p': 'present',
            'f': 'future',
            'i': 'imperfect',
            'r': 'perfect',
            'a': 'aorist',
            'l': 'pluperfect',
            't': 'future perfect',
            }
        return str(_tense_types[self.tense])

    @property
    def mood(self) -> str:
        groups = re.search(r'^[\S][\S][\S][\S]([nimsopgd])[\S][\S][\S][\S][\S]$', self.miscellanea)
        return groups.group(1) if groups else ''

    @property
    def mood_verbose(self) -> str:
        _mood_types = {
            'n': 'infinitive',
            'i': 'indicative',
            'm': 'imperative',  # ?
            's': 'subjunctive',
            'o': 'optative',
            'p': 'participle',   # ?
            'g': 'gerund',
            'd': 'gerundive',   # ?
        }
        return str(_mood_types[self.mood])

    @property
    def voice(self) -> str:
        groups = re.search(r'^[\S][\S][\S][\S][\S]([apmds])[\S][\S][\S][\S]$', self.miscellanea)
        return groups.group(1) if groups else ''

    @property
    def voice_verbose(self) -> str:
        _voice_types = {
            'a': 'active',
            'p': 'passive',  # ?
            'm': 'middle',  # ?
            'd': 'deponent',
            's': 'semideponent'
        }
        return str(_voice_types[self.voice])

    @property
    def gender(self) -> str:
        groups = re.search(r'^[\S][\S][\S][\S][\S][\S]([mfnca])[\S][\S][\S]$', self.miscellanea)
        return groups.group(1) if groups else ''

    @property
    def gender_verbose(self) -> str:
        _gender_types = {
            'm': 'masculine',
            'f': 'feminine',
            'n': 'neuter',
            'c': 'masculine or feminine',
            'a': 'masculine or feminine or neuter',
        }
        return str(_gender_types[self.gender])

    @property
    def case(self) -> str:
        groups = re.search(r'^[\S][\S][\S][\S][\S][\S][\S]([ngdabvl])[\S][\S]$', self.miscellanea)
        return groups.group(1) if groups else ''

    @property
    def case_verbose(self) -> str:
        _case_types = {
            'n': 'nominative',
            'g': 'genitive',
            'd': 'dative',
            'a': 'accusative',
            'b': 'ablative',
            'v': 'vocative',  # ?
            'l': 'locative',  # ?
        }
        return str(_case_types[self.case])

    @property
    def group(self) -> str:
        groups = re.search(r'^[\S][\S][\S][\S][\S][\S][\S][\S]([\d-])[\S]$', self.miscellanea)
        return groups.group(1) if groups else ''

    @property
    def group_verbose(self) -> str:
        _group_types = {
            'n': {
                    '1': '1st declension',
                    '2': '2nd declension',
                    '3': '3rd declension',
                    '4': '4th declension',
                    '5': '5th declension',
                    '-': 'indeclinable',
                    },
            'v': {
                    '1': '1st conjugation',  # thematic
                    '2': '2nd conjugation',  # thematic, contract
                    '3': '3rd conjugation',  # athematic
                    '4': '4th conjugation',
                    },
            'a': {
                    '1': '1st/2nd declension',
                    '3': '3rd declension',
                    },
        }
        return str(_group_types[self.pos][self.group])

    @property
    def is_istem(self) -> bool:
        groups = re.search(r'^[\S][\S][\S][\S][\S][\S][\S][\S][\S]([i])$', self.miscellanea)
        return True if groups else False

    @property
    def istem(self) -> str:
        groups = re.search(r'^[\S][\S][\S][\S][\S][\S][\S][\S][\S]([i-])$', self.miscellanea)
        return groups.group(1) if groups else ''

    def __repr__(self):
        return f"Morpho('{self.lemma}', '{self.pos}')"

    def __str__(self):
        if self.pos == 'v':
            return f"{self.group_verbose}: {self.person_verbose} {self.number_verbose} {self.tense_verbose} {self.mood_verbose} {self.voice_verbose}"
        elif self.pos == 'n':
            return f"{self.group_verbose}: {self.gender_verbose} {self.case_verbose} {self.number_verbose}"
        elif self.pos == 'a':
            return f"{self.group_verbose}"
        else:
            return f"{self.pos_verbose}"


class Phrase(object):
    """
    Represents a phrase in a WordNet within the MultiWordNet.

    _phrase: The dictionary form of the multi-word phrasal lexical unit.
    _language: The language of the WordNet to which the word belongs.
    _pos: The part of speech of the phrasal lexical unit.
    _synset: A Synset object representing a synonym set to which the phrase belongs.
    _synonyms: A list of Lemma or Phrase objects corresponding to the other members of the phrase's synsets.
    """

    def __new__(cls, phrase, pos, language):
        try:
            db_column = {
                'n': 'id_n',
                'v': 'id_v',
                'a': 'id_a',
                'r': 'id_r',
                '*': 'id_n, id_v, id_a, id_r',
            }
            phrase = phrase.replace(' ', '_')
            if "''" in phrase:
                pass
            elif "'" in phrase:
                phrase = phrase.replace("'", "''")

            language_index = connect(language, "index")

            if language_index:
                language_index.execute(f"SELECT {db_column[pos]} FROM {language}_index WHERE lemma='{phrase}'")
                result = language_index.fetchone()
            else:
                result = None
        except OperationalError:
            raise
        else:
            if not result or (pos in ('n', 'v', 'a', 'r') and not result[0]):
                instance = None
            else:
                if pos == '*':
                    resolved_pos = ''
                    if result[0]:
                        resolved_pos += 'n'
                    if result[1]:
                        resolved_pos += 'v'
                    if result[2]:
                        resolved_pos += 'a'
                    if result[3]:
                        resolved_pos += 'r'
                    if len(resolved_pos) > 1:
                        raise POSError(f"cannot disambiguate '{phrase}' between '{', '.join(resolved_pos)}'")
                    else:
                        pos = resolved_pos

                is_phrase = True
                language_lemma = connect(language, "lemma")
                if language_lemma:
                    language_lemma.execute(f"SELECT is_phrase FROM {language}_lemma WHERE lemma='{phrase}' AND pos='{pos}';")
                    result = language_lemma.fetchone()

                    if result[0] == 'N':
                        is_phrase = False
                else:
                    language_synset = connect(language, "synset")
                    language_synset.execute(f"SELECT * FROM {language}_synset WHERE word LIKE '% {phrase} %';")
                    results = language_synset.fetchall()

                    if results:
                        is_phrase = False
                if not is_phrase:
                    raise TypeError(f"'{phrase}' is a lemma, not a phrase: try get_word()")
                else:
                    instance = super().__new__(cls)
            return instance

    def __init__(self, phrase, pos, language):
        self._phrase = phrase
        self._pos = pos
        self._language = language
        self._synsets = None
        self._synonyms = None

    @property
    def synsets(self) -> List[Synset]:
        if not self._synsets:
            temp = list()
            _DB_COLUMN = {
                    'n': 'id_n',
                    'v': 'id_v',
                    'a': 'id_a',
                    'r': 'id_r',
                    '*': 'id_n, id_v, id_a, id_r',
                }
            try:
                language_index = connect(self.language, "index")

                if language_index:
                    language_index.execute(f"SELECT {_DB_COLUMN[self.pos]} FROM {self.language}_index WHERE lemma='{self.phrase}'")
                    result = language_index.fetchone()
                else:
                    result = None
            except OperationalError:
                raise
            else:
                if result:
                    if self.pos == '*' and result[0]:
                        if not result[0]:  # n
                            if not result[1]:  # v
                                if not result[2]:  # a
                                    temp = [Synset(syn, self.language) for syn in result[3].split(' ')]  # r
                                else:
                                    temp = [Synset(syn, self.language) for syn in result[2].split(' ')]
                            else:
                                temp = [Synset(syn, self.language) for syn in result[1].split(' ')]
                        else:
                            temp = [Synset(syn, self.language) for syn in result[0].split(' ')]
                    else:
                        temp = [Synset(syn, self.language) for syn in result[0].split(' ')]
                self._synsets = temp
        return list(self._synsets)

    @property
    def synonyms(self) -> list:
        if not self._synonyms:
            temp = set()
            try:
                language_synonyms = connect(self.language, "synonyms")

                if language_synonyms:
                    for synset in self.synsets:
                        language_synonyms.execute(f"SELECT lemma FROM {self.language}_synonyms WHERE pos='{self.pos}' AND syn='{synset.offset}'")
                        results = language_synonyms.fetchall()
                else:
                    results = None

                if results:
                    for result in results:
                        if result[0] != self.phrase:
                            temp.add(Lemma(result[0], self.pos, self.language))

                if not temp:
                    language_synset = connect(self.language, "synset")

                    if language_synset:
                        for synset in self.synsets:
                            language_synset.execute(f"SELECT word, phrase FROM {self.language}_synset WHERE id='{synset.id}'")
                            result = language_synset.fetchone()
                    else:
                        result = None

                    if result:
                        if result[0]:
                            for word in result[0].strip().split(' '):
                                temp.add(Lemma(word, self.pos, self.language))
                        if result[1]:
                            for phrase in result[1].strip().split(' '):
                                if phrase != self.phrase:
                                    temp.add(Phrase(phrase, self.pos, self.language))
            except OperationalError:
                raise
            else:
                self._synonyms = list(temp)
        return list(self._synonyms)

    @property
    def phrase(self) -> str:
        return str(self._phrase)

    @property
    def language(self) -> str:
        return str(self._language)

    @property
    def pos(self) -> str:
        return str(self._pos)

    @property
    def antonyms(self) -> list:
        """ Returns all Lemmas or Phrases with Relation of type '!' (antonym) to the Phrase """
        try:
            language_relation = connect(self.language, "relation")

            if language_relation:
                language_relation.execute(f"SELECT id_target, w_target FROM {self.language}_relation WHERE w_source='{self.phrase}' AND type='!';")
                results = language_relation.fetchall()
            else:
                results = None
        except OperationalError:
            raise
        else:
            if results:
                _antonyms = set()
                for result in results:
                    _antonyms.add((result[1], result[0][0],))
            else:
                _antonyms = None

            temp = list()
            if _antonyms:
                for _antonym in _antonyms:
                    if Lemma(*_antonym, self.language):
                        temp.append(Lemma(*_antonym, self.language))
                    else:
                        temp.append(Phrase(*_antonym, self.language))
            return temp

    def __str__(self):
        return self._phrase.replace('_', ' ')

    def __repr__(self):
        return f"Phrase('{self.phrase}', '{self.pos}', '{self.language}')"


class Lemma(object):
    """Represents a lemma in a WordNet within the MultiWordNet.

    _lemma: The dictionary form of the word.
    _language: The language of the WordNet to which the word belongs.
    _pos: The part of speech of the word.
    _synset: A Synset object representing a synonym set to which the word belongs.
    _synonyms: A list of Lemma or Phrase objects corresponding to the other members of the word's synsets.
    """

    def __new__(cls, lemma, pos, language):
        try:
            db_column = {
                'n': 'id_n',
                'v': 'id_v',
                'a': 'id_a',
                'r': 'id_r',
                '*': 'id_n, id_v, id_a, id_r',
            }
            if "''" in lemma:
                pass
            elif "'" in lemma:
                lemma = lemma.replace("'", "''")
            if ' ' in lemma:
                lemma = lemma.replace(' ', '_')

            language_index = connect(language, "index")
            if language_index:
                language_index.execute(f'SELECT {db_column[pos]} FROM {language}_index WHERE lemma="{lemma}"')
                result = language_index.fetchone()
            else:
                result = None
        except OperationalError:
            raise
        else:
            if not result or (pos in ('n', 'v', 'a', 'r') and not result[0]):
                instance = None
            else:
                if pos == '*':
                    resolved_pos = ''
                    if result[0]:
                        resolved_pos += 'n'
                    if result[1]:
                        resolved_pos += 'v'
                    if result[2]:
                        resolved_pos += 'a'
                    if result[3]:
                        resolved_pos += 'r'
                    if len(resolved_pos) > 1:
                        raise POSError(f"cannot disambiguate '{lemma}' between '{', '.join(resolved_pos)}'")
                    else:
                        pos = resolved_pos
                _is_phrase = False
                language_lemma = connect(language, "lemma")
                if language_lemma:
                    language_lemma.execute(f"SELECT is_phrase FROM {language}_lemma WHERE lemma='{lemma}' AND pos='{pos}';")
                    result = language_lemma.fetchone()
                    if result and result[0] == 'Y':
                        _is_phrase = True
                else:
                    language_index = connect(language, "synset")
                    if language_index:
                        language_index.execute(f"SELECT * FROM {language}_synset WHERE phrase LIKE '% {lemma} %';")
                        results = language_index.fetchall()
                        if results:
                            _is_phrase = True
                if _is_phrase:
                    raise TypeError(f"'{lemma}' is a phrase, not a word: try get_phrase()")
                instance = super().__new__(cls)
                instance._pos = pos
                instance._lemma = lemma
                instance._language = language
                instance._is_phrase = _is_phrase
            return instance

    def __init__(self, lemma, pos, language):
        self._synsets = None
        self._synonyms = None
        self._morpho = None

    def __eq__(self, other):
        return self.lemma == other.lemma

    def __lt__(self, other):
        return self.lemma < other.lemma

    @property
    def is_phrase(self) -> bool:
        return bool(self._is_phrase)

    @property
    def morpho(self) -> Morpho:
        if not self._morpho:
            self._morpho = Morpho(self.lemma, self.pos, self.language)
        return self._morpho if self._morpho else None

    @property
    def synsets(self) -> List['Synset']:
        if not self._synsets:
            temp = list()
            _DB_COLUMN = {
                    'n': 'id_n',
                    'v': 'id_v',
                    'a': 'id_a',
                    'r': 'id_r',
                    '*': 'id_n, id_v, id_a, id_r',
                }
            try:
                language_index = connect(self.language, "index")

                if language_index:
                    language_index.execute(f"SELECT {_DB_COLUMN[self.pos]} FROM {self.language}_index WHERE lemma='{self.lemma}'")
                    result = language_index.fetchone()

                    if result:
                        if self.pos == '*' and result[0]:
                            if not result[0]:  # n
                                if not result[1]:  # v
                                    if not result[2]:  # a
                                        temp = [Synset(syn, self.language) for syn in result[3].split(' ')]  # r
                                    else:
                                        temp = [Synset(syn, self.language) for syn in result[2].split(' ')]
                                else:
                                    temp = [Synset(syn, self.language) for syn in result[1].split(' ')]
                            else:
                                temp = [Synset(syn, self.language) for syn in result[0].split(' ')]
                        else:
                            temp = [Synset(syn, self.language) for syn in result[0].split(' ')]
            except OperationalError:
                raise
            else:
                self._synsets = temp
        return list(self._synsets)

    @property
    def synonyms(self) -> list:
        if not self._synonyms:
            temp = set()
            try:
                language_synonyms = connect(self.language, "synonyms")

                if language_synonyms:
                    for synset in self.synsets:
                        language_synonyms.execute(f"SELECT lemma FROM {self.language}_synonyms WHERE pos='{self.pos}' AND syn='{synset.offset}'")
                        results = language_synonyms.fetchall()

                        if results:
                            for result in results:
                                if result[0] != self.lemma:
                                    temp.add(Lemma(result[0], self.pos, self.language))

                if not temp:
                    language_synset = connect(self.language, "synset")

                    if language_synset:
                        for synset in self.synsets:
                            language_synset.execute(f"SELECT word, phrase FROM {self.language}_synset WHERE id='{synset.id}'")
                            result = language_synset.fetchone()

                            if result[0]:
                                for word in result[0].strip().split(' '):
                                    if word != self.lemma:
                                        temp.add(Lemma(word, self.pos, self.language))
                            if result[1]:
                                for phrase in result[1].strip().split(' '):
                                    temp.add(Phrase(phrase, self.pos, self.language))

            except OperationalError:
                raise
            else:
                self._synonyms = list(temp)
        return list(self._synonyms)

    def __eq__(self, other):
        return self.lemma == other.lemma and self.pos == other.pos

    def __hash__(self):
        return hash((self.lemma, self.pos))

    @property
    def lemma(self) -> str:
        return str(self._lemma)

    @property
    def language(self) -> str:
        return str(self._language)

    @property
    def pos(self) -> str:
        return str(self._pos)

    def get_derivates(self, pos: str='nvar') -> List['Lemma']:
        """ Returns all Lemmas with Relation of type '\' (derived-from) to the Lemma matching part of speech 'pos' """

        _derived_words = [derivate for derivate in self.derivates if derivate.pos in pos]
        return _derived_words

    @property
    def derivates(self) -> List['Lemma']:
        """ Returns all Lemmas with Relation of type '\' (derived-from) to the Lemma """
        _derived_words = list()
        try:
            language_relation = connect(self.language, "relation")
            language_relation.execute(f"SELECT id_source, w_source FROM {self.language}_relation WHERE w_target='{self.lemma}' AND type='\\';")
            results = language_relation.fetchall()
        except OperationalError:
            raise
        else:
            if results:
                for result in results:
                    _derived_words.append(Lemma(result[1], result[0][0], self.language))
            return _derived_words

    def get_relatives(self, pos: str='nvar') -> List['Lemma']:
        """ Returns all Lemmas with Relation of type '/' (related-to) to the Lemma matching part of speech 'pos' """

        _related_words = [relative for relative in self.relatives if relative.pos in pos]
        return _related_words

    @property
    def relatives(self) -> List['Lemma']:
        """ Returns all Lemmas with Relation of type '/' (related-to) to the Lemma """
        _related_words = list()
        try:
            language_relation = connect(self.language, "relation")
            language_relation.execute(f"SELECT id_target, w_target FROM {self.language}_relation WHERE w_source='{self.lemma}' AND type='/';")
            results = language_relation.fetchall()
        except OperationalError:
            raise
        else:
            if results:
                for result in results:
                    _related_words.append(Lemma(result[1], result[0][0], self.language))

        return _related_words

    @property
    def antonyms(self) -> list:
        """ Returns all Lemmas or Phrases with Relation of type '!' (antonym) to the Phrase """

        temp = set()
        try:
            language_relation = connect(self.language, "relation")
            if language_relation:
                language_relation.execute(f"SELECT id_target, w_target FROM {self.language}_relation WHERE w_source='{self.lemma}' AND type='!';")
                results = language_relation.fetchall()
            else:
                results = None
        except OperationalError:
            raise
        else:
            if results:
                for result in results:
                    temp.add((result[1], result[0][0],))

        _antonyms = list()
        if temp:
            for antonym in temp:
                if Lemma(*antonym, self.language):
                    _antonyms.append(Lemma(*antonym, self.language))
                else:
                    _antonyms.append(Phrase(*antonym, self.language))
        return _antonyms

    def __str__(self):
        return self._lemma.replace('_', ' ')

    def __repr__(self):
        return f"Lemma('{self.lemma}', '{self.pos}', '{self.language}')"


class Relation(object):
    """

    """

    types = {
        'n':
            {
                '!': 'antonym (lexical)',
                '@': 'hypernym',
                '~': 'hyponym',
                '#m': 'member-of',
                '#s': 'substance-of',
                '#p': 'part-of',
                '%m': 'has-member',
                '%s': 'has-substance',
                '%p': 'has-part',
                '=': 'attribute',
                '|': 'nearest',
                '+r': 'has-role',
                '-r': 'is-role-of',
                '+c': 'composed-of (lexical)',
                '-c': 'composes (lexical)',
                r'\\': 'derived-from (lexical)',  # NEW
                '/': 'related-to (lexical)',  # NEW
            },
        'v':
            {
                '!': 'antonym (lexical)',
                '@': 'hypernym',
                '~': 'hyponym',
                '*': 'entailment',
                '>': 'causes',
                '^': 'also-see',
                '$': 'verb-group',
                '|': 'nearest',
                '+c': 'composed-of (lexical)',
                '-c': 'composes (lexical)',
                r'\\': 'derived-from (lexical)',  # NEW
                '/': 'related-to (lexical)',  # NEW
            },
        'a':
            {
                '!': 'antonym (lexical)',
                '@': 'hypernym',
                '~': 'hyponym',
                '&': 'similar-to',
                '<': 'participle (lexical)',  # of a verb
                r'\\': 'pertains-to (lexical)',  # to a noun, equivalent to 'derived-from'
                '=': 'is-value-of',
                '^': 'also-see',
                '|': 'nearest',
                '+c': 'composed-of (lexical)',
                '-c': 'composes (lexical)',
                '/': 'related-to (lexical)',  # NEW
            },
        'r':
            {
                '!': 'antonym (lexical)',
                '@': 'hypernym',
                '~': 'hyponym',
                r'\\': 'derived-from (lexical)',
                '|': 'nearest',
                '+c': 'composed-of (lexical)',
                '-c': 'composes (lexical)',
                '/': 'related-to (lexical)',  # NEW
            },
    }

    def __init__(self, type: str, id_source: str, id_target: str, w_source: str=None, w_target: str=None, status: str=None, language: str='english'):
        self._type = type

        self._id_source = id_source
        self._id_target = id_target

        self._w_source = w_source
        self._w_target = w_target
        self._language = language

        if status in ('new', 'NEW'):
            self._status = status.lower()
        else:
            self._status = ''

    @property
    def language(self) -> str:
        return str(self._language)

    @property
    def type(self) -> str:
        return str(self._type)

    @property
    def type_verbose(self) -> str:
        if self._id_source[0] != 'n':
            if self._id_source[0] != 'v':
                if self._id_source[0] != 'a':
                    return self.types['r'][self._type]
                else:
                    return self.types['a'][self._type]
            else:
                return self.types['v'][self._type]
        else:
            return self.types['n'][self._type]

    @property
    def id_target(self) -> str:
        return str(self._id_target)

    @property
    def id_source(self) -> str:
        return str(self._id_source)

    @property
    def w_target(self) -> Lemma:
        return Lemma(self._w_target, self.target.pos, self.target.language) if self._w_target else None

    @property
    def w_source(self) -> Lemma:
        return Lemma(self._w_source, self.source.pos, self.source.language) if self._w_source else None

    @property
    def is_lexical(self) -> bool:
        return bool(isinstance(self.w_source, Lemma) and isinstance(self.w_target, Lemma))

    @property
    def status(self) -> str:
        return str(self._status)

    @property
    def source(self) -> Synset:
        return Synset(self.id_source, Synset.get_synset_language(self.id_target))

    @property
    def target(self) -> Synset:
        return Synset(self.id_target, Synset.get_synset_language(self.id_target))

    def __repr__(self):
        if self.is_lexical:
            return f"Relation('{self.type}', '{str(self.w_source)}', '{str(self.w_target)}')"
        else:
            return f"Relation('{self.type}', '{self.id_source}', '{self.id_target}')"

    def __str__(self):
        if self.is_lexical:
            return f"{str(self.w_source)} {self.type_verbose} {str(self.w_target)}"
        else:
            return f"{self.id_source} {self.type_verbose} {self.id_target}"


class GreekWordNet(object):
    """
    Represents a WordNet within the MultiWordNet.

    _language: A string giving the name of the language of the WordNet. Default is 'english'.
    _relations: A list of Relation objects representing the semantic or lexical relations defined for the WordNet.
    _words: A list of Lemma objects representing distinct lemmas within the WordNet.
    _synsets: A list of Synset objects representing the synsets defined for the WordNet.
    _semfields: A list of all semfields defined for the MultiWordNet.
    """

    def __init__(self, language: str='greek'):
        self._language = language
        self._relations = None
        self._lemmas = None
        self._synsets = None
        self._semfields = None

    def get_synset(self, id: str) -> Synset:
        return Synset(id, self.language)

    @property
    def language(self) -> str:
        return str(self._language)

    @property
    def synsets(self) -> Generator[Synset, None, Iterable[Synset]]:
        if not self._synsets:
            temp = list()
            try:
                language_synset = connect(self.language, "synset")

                if language_synset:
                    language_synset.execute(f"SELECT * FROM {self.language}_synset")
                    results = language_synset.fetchall()
                else:
                    results = None
            except OperationalError:
                raise
            else:
                if results:
                    for result in results:
                        temp.append(Synset(result[0], self.language))
            self._synsets = temp
        return (synset for synset in self._synsets)

    def get_lemma(self, lemma, pos='*') -> Lemma:
        return Lemma(lemma, pos, self.language)

    def get_phrase(self, phrase, pos='*') -> Phrase:
        return Phrase(phrase, pos, self.language)

    def get(self, lemma, pos='*', strict=True) -> List[object]:
        try:
            if pos == '*': pos = 'nvar'
            lemma = lemma.replace(' ', '_')
            if "''" in lemma:
                pass
            elif "'" in lemma:
                lemma = lemma.replace("'", "''")

            if strict:
                query = f"lemma='{lemma}'"
            else:
                query = f"lemma LIKE '%{lemma}%'"

            language_lemma = connect(self.language, "lemma")
            if language_lemma:
                language_lemma.execute(f"SELECT lemma, pos, is_phrase FROM {self.language}_lemma WHERE {query}")
                results = language_lemma.fetchall()
            else:
                results = None
        except OperationalError:
            raise
        else:
            if results:
                _list = set()
                for result in results:
                    if result[1] in pos and result[2] == 'Y':
                        _list.add(Phrase(result[0], result[1], self.language))
                    elif result[1] in pos:
                        _list.add(Lemma(result[0], result[1], self.language))
            else:
                _list = None
        return _list if _list else []

    @property
    def semfields(self) -> Generator[Semfield, None, Iterable[Semfield]]:
        if not self._semfields:
            temp = list()
            try:
                common_semfield_hierarchy = connect("common", "semfield_hierarchy")

                if common_semfield_hierarchy:
                    common_semfield_hierarchy.execute("SELECT code, english FROM semfield_hierarchy")
                    results = common_semfield_hierarchy.fetchall()
                else:
                    results = None
            except OperationalError:
                raise
            else:
                if results:
                    for result in results:
                        temp.append(Semfield(code=result[0], english=result[1]))
            self._semfields = temp
        return (semfield for semfield in self._semfields)

    def get_semfield_by_code(self, code: str) -> List[Semfield]:
        try:
            common_semfield_hierarchy = connect("common", "semfield_hierarchy")

            if common_semfield_hierarchy:
                common_semfield_hierarchy.execute(f"SELECT english FROM semfield_hierarchy WHERE code='{code}'")
                results = common_semfield_hierarchy.fetchall()
            else:
                results = None
        except OperationalError:
            raise
        else:
            if results:
                _semfield = [Semfield(result[0], code=code) for result in results]
            else:
                _semfield = None
            return _semfield

    def get_semfield_by_english(self, english: str) -> List[Semfield]:
        try:
            english = english.replace(' ', '_')
            common_semfield_hierarchy = connect("common", "semfield_hierarchy")

            if common_semfield_hierarchy:
                common_semfield_hierarchy.execute(f"SELECT code FROM semfield_hierarchy WHERE english='{english}'")
                results = common_semfield_hierarchy.fetchall()
            else:
                results = None
        except OperationalError:
            raise
        else:
            if results:
                _semfield = [Semfield(english=english, code=result[0]) for result in results]
            else:
                _semfield = None
            return _semfield

    def get_semfield(self, code: str, english: str) -> Semfield:
        return Semfield(code=code, english=english)

    @property
    def lemmas(self) -> Generator[object, None, Iterable[object]]:
        if not self._lemmas:
            temp = list()
            try:
                language_index = connect(self.language, "index")

                if language_index:
                    language_index.execute(f"SELECT * FROM {self.language}_index")
                    results = language_index.fetchall()
                else:
                    results = None
            except OperationalError:
                raise
            else:
                if results:
                    pos = ['*', 'n', 'v', 'a', 'r']
                    for result in results:
                        for i in range(1, 5):
                            if result[i]:
                                try:
                                    temp.append(Lemma(result[0], pos[i], self.language))
                                except TypeError:
                                    temp.append(Phrase(result[0], pos[i], self.language))
            self._lemmas = temp
        return (lemma for lemma in self._lemmas)

    @property
    def relations(self) -> Generator[Relation, None, Iterable[Relation]]:
        if not self._relations:
            temp = list()
            try:
                common_relation = connect("common", "relation")
                if common_relation:
                    common_relation.execute("SELECT * FROM common_relation")
                    results = common_relation.fetchall()
                else:
                    results = None
            except OperationalError:
                raise
            else:
                if results:
                    for result in results:
                        temp.append(Relation(*result, language='common'))
            try:
                language_relation = connect(self.language, "relation")
                if language_relation:
                    language_relation.execute(f"SELECT * FROM {self.language}_relation")
                    results = language_relation.fetchall()
            except OperationalError:
                raise
            else:
                if results:
                    for result in results:
                        temp.append(Relation(*result, language=self.language))
            self._relations = temp
        return (relation for relation in self._relations)

    def get_relations(self, *, source: Synset=None, target: Synset=None, type=None, lexical=True) -> Generator[Relation, None, Iterable[Relation]]:
        temp = list()
        qr = ''
        if source:
            qr = f" WHERE id_source='{source.id}'"
        if target:
            if source:
                qr += f" AND id_target='{target.id}'"
            else:
                qr = f" WHERE id_target='{target.id}'"
        if type:
            if source or target:
                qr += f" AND type='{type}'"
            else:
                qr = f" WHERE type='{type}'"
        try:
            common_relation = connect("common", "relation")
            if common_relation:
                common_relation.execute("SELECT * FROM common_relation" + qr)
                results = common_relation.fetchall()
            else:
                results = None
        except OperationalError:
            raise
        else:
            if results:
                for result in results:
                    temp.append(Relation(*result, language='common'))
        try:
            language_relation = connect(self.language, "relation")

            if language_relation:
                language_relation.execute(f"SELECT * FROM {self.language}_relation" + qr)
                results = language_relation.fetchall()
            else:
                results = None
        except OperationalError:
            raise
        else:
            if results:
                for result in results:
                    if not lexical and result[3] and result[4]:
                        continue
                    else:
                        temp.append(Relation(*result, self.language))
        return (relation for relation in temp)

    def __repr__(self):
        return f"WordNet('{self.language}')"


