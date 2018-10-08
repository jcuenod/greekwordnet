""" Contains the WordNet databases  """

import codecs
import os
import sqlite3
import sys
from os import listdir
from sqlite3 import OperationalError

from tqdm import tqdm

module = sys.modules['greekwordnet.db'].__path__[0]


def connect(language, database):
    """ Connects to a database """

    try:
        if os.path.exists(f"{module}/{language}/{language}_{database}.db"):
            cursor = sqlite3.connect(f"{module}/{language}/{language}_{database}.db").cursor()
        else:
            raise OperationalError
    except OperationalError:
        cursor = None
    finally:
        return cursor


def compile(language, *tables):
    if not tables:
        tables = [filename.split('_')[1].replace('.sql', '') for filename in listdir(f"{module}/{language}/") if filename.endswith('.sql')]

    for table in tables:
        f = codecs.open(f"{module}/{language}/{language}_{table}.sql", encoding='utf-8')
        if not f:
            continue
        db = sqlite3.connect(f"{module}/{language}/{language}_{table}.db").cursor()
        if not db:
            continue
        for sql in tqdm(f.readlines(), ncols=80, desc=f"{language}_{table}.sql"):
            if not(sql.startswith('#') or sql == '\n'):
                db.executescript(sql)
