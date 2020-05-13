#! /usr/bin/env python

import os
import click
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

"""
Script to determining if gene clusters are taxa specific
This script takes a mapping table (genes-contigs-MAGS-Taxonomy-eggNOG annotations), 
generates statistics on genes missing in MAGS and determines if gene clusters are taxa specific                                                                  

"""

def load_gene_mapping_table(path):

	"""
	Reads mapping table

    Parameters
    ----------
	input_file : tsv
        tsv file containing mappings between genes, contigs, MAGS and eggNOG annotations

    Returns
    -------
	Pandas dataframe
	"""
	table_df = pd.read_csv(path, sep='\t')
	return table_df
	
@click.command()
@click.option('--input_file', '-i', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True),
              help='Input path to mapping table .tsv file.')
@click.option('--out_distribution_plot', '-p', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=False),
              help='Output .png file.')
@click.option('--out_file', '-o', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=False),
              help='Output .tsv file.')

def _perform_stats(input_file, out_distribution_plot, 
	out_file):
	
	# load mapping table
	mapping_table = load_gene_mapping_table(input_file)
	
	#  genes missing in MAGS

	genes_missing_in_MAGS = mapping_table[mapping_table['contigs'].isna()]

	#count on all contigs
	genes_count = genes_missing_in_MAGS.groupby(['contigs_ID'])['Gene ID'].agg(np.ma.count)

	# plot a distribution of genes count
	genes_count.hist(bins=1000).set_xlim((0,8))
	plt.xlabel('count')
	plt.ylabel('genes')
	plt.savefig('genes_count_distribution.png')

	#  determine if non-redundant gene clusters are taxon-specific
	cluster_taxa = mapping_table.groupby('Cluster ID')['classification'].nunique()

	# saving to file
	cluster_taxa.to_csv(out_file, sep = '\t')



if __name__ == "__main__":
	_perform_stats()







