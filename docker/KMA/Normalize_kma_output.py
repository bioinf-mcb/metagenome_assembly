#! /usr/bin/env python


import click
import pandas as pd


"""
Script for normalizing KMA depth into Counts Per Million (CPM)
This script takes KMA output file and generates normalized depths                                                                  

"""

pd.options.mode.chained_assignment = None
 

def load_kma_file(path):

	"""
	Reads KMA output 

    Parameters
    ----------
	input_file : tsv
        tsv file kma output

    Returns
    -------
	Pandas dataframe
	"""
	kma_results_df = pd.read_csv(path, usecols=['#Template', 'Depth'], sep="\t")
	return kma_results_df


def add_normalized_depth(kma_file):
	"""
	Reads KMA dataframe
	Performs normalization of depth to CPM

	"""
	Total_depth = kma_file['Depth'].to_numpy().sum()
	kma_file['Depth/Total_depth'] = kma_file['Depth'].to_numpy() / Total_depth
	kma_file['CPM'] = kma_file['Depth/Total_depth'].to_numpy() * 1_000_000
    

@click.command()
@click.option('--input_file', '-i', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True),
              help='Input kma results file .res file.')
@click.option('--out_file', '-o', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=False),
              help='Output .tsv file.')

def _perform_normalization(input_file, out_file):

	# load kma dataframe
	kma_df = load_kma_file(input_file)

	# adds normalized column
	add_normalized_depth(kma_df)

	# subset the data to obtain Gene ID and normalized depth
	normalized_genes = kma_df[["#Template", "CPM"]]
	normalized_genes.rename(columns={'#Template':'Gene ID'}, inplace=True)
	
	# saving output to file
	normalized_genes.to_csv(out_file, sep = '\t', index=False)


if __name__ == "__main__":
	_perform_normalization()





