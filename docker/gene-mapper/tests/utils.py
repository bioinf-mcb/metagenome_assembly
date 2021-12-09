#! /usr/bin/env python

import pandas as pd


def dict2str(dict_):
    """
    Create string from Python dictionary.

    Parameters
    ----------
    dict_ : dict (str : str)

    Returns
    -------
    str
        joined 'key' 'value' pairs separated by space
    """
    return " ".join([f'{k} {v}' for k, v in dict_.items()])


def load_df(file, sep='\t', index_col=0, header=0, squeeze=False):
    """
    Create Pandas DataFrame from a file.

    Parameters
    ----------
    file : str
    squeeze : bool
    header : int
    index_col : int
    sep : str | regex

    Returns
    -------
    Pandas DataFrame
    """
    return pd.read_csv(file, sep=sep, index_col=index_col,
                       header=header, squeeze=squeeze)
