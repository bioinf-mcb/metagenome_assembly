#! /usr/bin/env python

import click
import numpy as np
import pandas as pd

pd.options.mode.chained_assignment = None


def load_normalized_kma_file(path):
    """
    Reads KMA normalized depth file

    Parameters
    ----------
    input_file : tsv
    tsv file of kma normalized depths
    Returns
    -------
    Pandas dataframe
    """
    kma_df = pd.read_csv(path, sep="\t", skiprows=1, names=['Gene_ID', 'CPM'])
    return kma_df


def load_genemapper_table(path):
    """
    Reads gene mapping table
    Parameters
    ----------
    input_file : tsv

    Returns
    -------
    Pandas dataframe

    """

    mapping_table_df = pd.read_csv(path, sep="\t")
    return mapping_table_df


@click.command()
@click.option('--kma_file', '-k', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True),
              help='Input normalized KMA depth file .tsv file.')
@click.option('--gene_mapper_file', '-g', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True),
              help='Input gene mapping table .tsv file.')
@click.option('--out_file', '-o', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=False),
              help='Output .tsv file.')
def _perform_summing_up_CPM(kma_file, gene_mapper_file, out_file):
    """
    Script for summing up CPMs per Go term
    This script takes normalized KMA depths, gene mapper table and sums up
    CPMs per GO terms.
    Input files required:
    1) Normalized KMA depths
    2) gene mapper table
    This script outputs:
    TSV file of CPMs per GO term
    """

    # load kma dataframe
    kma_df = load_normalized_kma_file(kma_file)

    # load gene mapper table
    mapped_genes = load_genemapper_table(gene_mapper_file)

    # subset data to obtain genes and GO terms
    genes_GO_mapping = mapped_genes[["Gene ID", "GOs", ]]

    # transforming dataframe
    gene_go = genes_GO_mapping.set_index('Gene ID') \
        .GOs.str.split(',', expand=True) \
        .stack() \
        .reset_index('Gene ID') \
        .rename(columns={0: 'GOs'}) \
        .reset_index(drop=True)

    # mapping kma dataframe to GO mapping df
    cpm_gene_go = pd.merge(gene_go, kma_df,
                           left_on='Gene ID', right_on='Gene_ID',
                           how='outer')

    # sum up CPMs per GO term
    CPM_per_GO = cpm_gene_go.groupby(['GOs'])['CPM'].agg(np.sum).reset_index()

    # saving to file
    CPM_per_GO.to_csv(out_file, sep='\t', index=False)


if __name__ == "__main__":
    _perform_summing_up_CPM()
