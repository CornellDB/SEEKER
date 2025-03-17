import pandas as pd
from collections import defaultdict
import config as C
import heapq

# Cache reading and transformation of DFs
cache = dict()

data_separator = C.separator


def configure_csv_separator(separator):
    global data_separator
    data_separator = separator


def read_relation(relation_path):
    if relation_path in cache:
        df = cache[relation_path]
    else:
        try:
            df = pd.read_csv(relation_path, encoding="utf8", sep=data_separator)
            cache[relation_path] = df
        except pd.errors.EmptyDataError:
            print(relation_path, " is empty and has been skipped.")
            return None
    return df


def read_column(relation_path, col):
    df = pd.read_csv(relation_path, encoding="utf8", sep=data_separator, usecols=[col])
    return df.copy()


def read_column(relation_path, col, offset=0):
    if offset == 0:
        df = pd.read_csv(
            relation_path, encoding="utf8", sep=data_separator, usecols=[col]
        )
    else:
        df = pd.read_csv(
            relation_path,
            encoding="utf8",
            sep=data_separator,
            usecols=[col],
            nrows=offset,
        )
    return df.copy()


def read_columns(relation_path, cols):
    df = pd.read_csv(relation_path, encoding="latin1", sep=data_separator, usecols=cols)
    return df.copy()
