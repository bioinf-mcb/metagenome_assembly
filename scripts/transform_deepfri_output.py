#! /usr/bin/env python

import click
import pandas as pd

pd.options.mode.chained_assignment = None


def load_DeepFRI_file(path):
    """
    Reads DeepFRI annotation file

    Parameters
    ----------
    path : tsv

    Returns
    -------
    Pandas dataframe
    """
    deepfri_df = pd.read_csv(path, sep=",", header=None,
                             names=['id', 'goterm', 'model', 'score', 'name'])
    return deepfri_df


def load_GO_subset_file(go):
    """
    Loads subset of GO file

    Parameters
    ----------
    go : str
        path to file (tsv)

    Returns
    -------
    Pandas dataframe
    """
    ontology_df = pd.read_csv(go, sep='\t', header=None)
    ontology_df = ontology_df[0].str.split("|", n=4, expand=True). \
        rename(columns={0: 'Goterm', 1: 'ont', 2: 'Score', 3: 'fxn_Name'})
    return ontology_df


def preprocess_data(data):
    """
    Processing DeepFRI file and selecting only CNN_MF functions
    """
    data = data.astype({'score': 'float32'})
    data = data.loc[(data['model'] == 'cnn_mf') & (
                data['score'] >= 0.5)]  # Select CNN_MF functions
    data['Sample'] = data['id'].apply(
        lambda x: x.split("_k")[0])  # extract sample colum
    data = data[["id", "goterm", "name", "Sample"]]  # subset
    return data


@click.command()
@click.option('--deepfri_file', '-i', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True),
              help='Input DeepFRI .tsv file.')
@click.option('--go_subset_file', '-g', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True),
              help='Input GO subset .tsv file.')
@click.option('--out_file', '-o', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=False),
              help='Output .tsv file.')
def _process_deepfri(deepfri_file, go_subset_file, out_file):
    """
    The script takes DeepfRI annotation file, maps the GO terms to
    informative GO terms subset and extracts the CNN-MF functions.

    Input files required:
    1) DeepFRI annotation file
    2) Subset of GO terms
    3) Name of output file

    Output:
    1) DeepFRI .tsv file
    """

    # load deepfri dataframe
    deepfri_df = load_DeepFRI_file(deepfri_file)

    # load informative GO subset
    GO_informative_df = load_GO_subset_file(go_subset_file)

    # map to deepfri dataframe to filter out only informative GO terms
    deepfri_GO_informative = pd.merge(deepfri_df, GO_informative_df,
                                      left_on='goterm', right_on='Goterm',
                                      how='inner')

    # select the cnn_mf functions
    deepfri_cnn_mf = preprocess_data(deepfri_GO_informative)

    # save the file
    deepfri_cnn_mf.to_csv(out_file, sep='\t', index=False)


if __name__ == "__main__":
    _process_deepfri()







