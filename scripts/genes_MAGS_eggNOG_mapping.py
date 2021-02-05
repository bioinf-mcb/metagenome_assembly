#! /usr/bin/env python

"""
Script for mapping genes to contigs, MAGS and eggNOG annotations.

Input files required:
1) clustering file with cluster ID and gene ID
2) Non-redundant gene catalogue (fasta)
3) Contig files (fasta)
4) binned contigs (MAGS)
5) taxonomy files (tsv)
6) EggNOG annotation file (tsv)

The script outputs two files:
1) Tsv file that links the non-redundant gene catalogue back to contigs,
and then back to MAGs with eggNOG annotations
2) Tsv file that maps gene families to taxonomy and generate counts

Detailed help:
python scripts/genes_MAGS_eggNOG_mapping.py --help
"""

import os
import glob
import click
import pandas as pd
from skbio import io
import re

pd.options.mode.chained_assignment = None


def tabulate_cluster_info(path):
    """
  transforming raw cluster file
  Reads cluster file from CD-HIT 
  transforms it into two-column format (cluster centroid ID and gene ID)
  Parameters
    ----------
  input_file : str
        clustering file containing cluster centroids and gene IDS

    Returns
    -------
  Pandas dataframe containing cluster IDS and gene IDS
  """
    clusters, genes = [], []
    with open(path, 'r') as file:
        for line in file:
            if line.startswith(">"):
                cluster_id = line.rstrip().replace(">", "")
            else:
                gene_id = line.split(">")[1].split("...")[0]
                clusters.append(cluster_id)
                genes.append(gene_id)
    gene_cluster_df = pd.DataFrame(list(zip(clusters, genes)),
                                   columns=['Cluster ID', 'Gene ID'])
    return gene_cluster_df


def load_fasta_ids(path):
    """
  Reads sequences from a fasta file and extracts identifiers.

    Parameters
    ----------
  input_file : str
        fasta file containing contigs and gene identifiers

    Returns
    -------
  List of fasta identifiers
  """
    fasta_ids = [seq.metadata['id'] for seq in io.read(path, format='fasta')]
    return fasta_ids


def load_checkm_files(file):
    """
  Reads CHECKM txt file and extracts specified columns
  Parameters
  ----------
  input_file : str
      txt file containing CHECKM report

  Returns
  ------
  A CHECKM dataframe
  """
    CHECKM = []
    checkm_f = open(file, 'r')
    for line in checkm_f:
        contents = (re.sub('\-+', '', line.strip()))
        if contents:
            contents = re.sub('\s\s+', '\t', contents)
            CHECKM.append(contents.split('\t'))
    return pd.DataFrame(data=CHECKM[1:], columns=CHECKM[0])[
        ["Bin Id", "Marker lineage", "# genomes", "# markers", "Completeness",
         "Contamination", "Strain heterogeneity"]]


def load_mags_contigs_taxonomies_for_sample(sample_dir, taxonomy_path,
                                            checkm_path):
    """
    Extract MAG, contig, taxonomy and CHECKM information for specific sample.

    Parameters
    ----------
    sample_dir: str
        directory where to look for specific sample
    taxonomy_path: str
        path with taxonomy files
    checkm_path: str
        path to CHECKM files

    Returns
    -------
    Pandas dataframe containing MAGS, contigs, taxonomies
    and CHECKM information
    """
    sample_dir_name = os.path.basename(sample_dir)
    mag_root = sample_dir_name[:sample_dir_name.rfind("_bins")]

    # runs through per-sample Checkm files and creates a dataframe
    colnames = ["Bin Id", "Marker lineage", "# genomes", "# markers",
                "Completeness", "Contamination", "Strain heterogeneity"]
    checkm_df = pd.DataFrame(columns=colnames)
    checkm_file = os.path.join(checkm_path, f"{mag_root}_checkm.txt")
    try:
        f = open(checkm_file, "r")
        checkm_df = checkm_df.append(load_checkm_files(checkm_file)[colnames])
    except:
        print('Missing or empty checkM output file:', checkm_file)

    # Run through all bin .fa files
    mags, bins, contigs = [], [], []
    for bin_file in glob.glob(os.path.join(sample_dir, "*.fa")):
        bin_name = os.path.splitext(os.path.basename(bin_file))[0]
        mag_name = f"{mag_root}_{bin_name}"
        bin_contigs = load_fasta_ids(bin_file)
        mags.extend([mag_name] * len(bin_contigs))
        bins.extend([bin_name] * len(bin_contigs))
        contigs.extend(bin_contigs)

    # Construct dataframe
    raw_df = pd.DataFrame({"MAGS": mags, "bins": bins, "contigs": contigs})

    # Add taxonomy information
    taxonomy_file = os.path.join(taxonomy_path,
                                 f"{mag_root}.bac120.summary.tsv")
    taxonomy_cols = ["user_genome", "classification", "fastani_reference"]
    try:
        f = open(taxonomy_file, "r")
        taxonomies_df = pd.read_csv(f, sep='\t', usecols=taxonomy_cols)
        merged_df = raw_df.join(taxonomies_df.set_index(taxonomy_cols[0]),
                                on='bins', how='left')
    except:
        print(f'Missing or empty taxonomy file: {taxonomy_file}')
        print('Adding empty taxonomy columns...')
        merged_df = raw_df.join(raw_df.reindex(columns=taxonomy_cols[1:]))

    # Add checkM information
    merged_df = merged_df.join(checkm_df.set_index('Bin Id'), on='bins',
                               how='left')

    return merged_df


def load_mags_contigs_taxonomies(bin_path, taxonomy_path, checkm_path):
    """
    # extract MAG, contig, taxonomy and CHECKM information for all samples.

    Parameters
    ----------
    bin_path: str
        path with samples
    taxonomy_path: str
        path with taxonomy files
    checkm_path: str
        path with CHECKM files

    Returns
    -------
    Pandas dataframe containing MAGS, contigs and taxonomies
    """

    # Extract all sample directories
    bin_dirs = [f for f in os.scandir(bin_path) if f.is_dir()]

    # Return concatenated dataframe
    concatenated_df = pd.concat([load_mags_contigs_taxonomies_for_sample(
        bin_dir, taxonomy_path, checkm_path)
        for bin_dir in bin_dirs],
        ignore_index=True)
    return concatenated_df


def load_eggNOG_file(eggnog_ann_file):
    """
    Load EggNOG annotations skipping commented lines i.e. '#\\s'

    Parameters
    ----------
    eggnog_ann_file: str
        path to EggNOG annotation file (tsv)

    Returns
    -------
    Pandas dataframe
    """
    # Fetch header from file (should be somewhere at the beginning)
    header = None
    with open(eggnog_ann_file, 'r') as f:
        for line in f:
            if line.startswith('#query_name'):
                header = line
                break
    header = [el.strip() for el in header.split('\t')]
    # Create & return Pandas DataFrame
    return pd.read_csv(eggnog_ann_file, sep='\t', names=header, comment='#')


@click.command()
@click.option('--cluster_file', '-r', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True),
              help='Input path to raw clustering .clstr file.')
@click.option('--genes_file', '-g', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True),
              help='Input path to genes .fa file.')
@click.option('--contigs_file', '-c', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True),
              help='Input path to merged contigs fasta file.')
@click.option('--bin_fp', '-b', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True),
              help='Input path to bin folder.')
@click.option('--tax_fp', '-t', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True),
              help='Input path to taxonomy folder (can be empty).')
@click.option('--checkm_fp', '-m', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True),
              help='Input path to checkm folder  (can be empty).')
@click.option('--eggnog_ann_file', '-e', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True),
              help='Input path to eggnog .annotations file.')
@click.option('--out_gene_mapping_file', '-o', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=False),
              help='Output .tsv file.')
@click.option('--out_cluster_taxa_file', '-f', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=False),
              help='Output .tsv file.')
def _perform_mapping(cluster_file, genes_file, contigs_file,
                     eggnog_ann_file, bin_fp, tax_fp, checkm_fp,
                     out_gene_mapping_file, out_cluster_taxa_file):

    # load cluster file
    cluster_df = tabulate_cluster_info(cluster_file)

    # Load contig and gene IDs
    contigs = load_fasta_ids(contigs_file)
    genes = load_fasta_ids(genes_file)

    # Create gene catalogue dataframe
    genes_df = pd.DataFrame({'centroid': genes})
    genes_df = genes_df.astype(str)

    # Create contigs dataframe
    contigs_df = pd.DataFrame({'contigs_ID': contigs})
    contigs_df = contigs_df.astype(str)

    # map cluster and NR genes
    mapped_centroid_genes = pd.merge(cluster_df, genes_df,
                                     left_on='Gene ID',
                                     right_on='centroid',
                                     how='inner')[['Cluster ID', 'centroid']]

    # mapped cluster genes
    mapped_cluster_genes = pd.merge(cluster_df, mapped_centroid_genes,
                                    left_on='Cluster ID',
                                    right_on='Cluster ID',
                                    how='outer')

    # Create column with truncated gene ids
    mapped_cluster_genes['Gene_trunc'] = mapped_cluster_genes['Gene ID']. \
        apply(lambda x: x.rsplit('_', 1)[0])

    # Change data type to string
    mapped_cluster_genes = mapped_cluster_genes.astype(str)

    # Map cluster genes to contigs
    mapped_genes_contigs = pd.merge(mapped_cluster_genes, contigs_df,
                                    left_on='Gene_trunc',
                                    right_on='contigs_ID',
                                    how='left')

    # MAGS and Taxonomy mapping
    MAGS_df = load_mags_contigs_taxonomies(bin_fp, tax_fp, checkm_fp)

    # Mapping between genes, contigs and mags
    mapped_genes_contigs_mags = pd.merge(mapped_genes_contigs, MAGS_df,
                                         left_on='contigs_ID',
                                         right_on='contigs',
                                         how='outer')
    # remove partial genes
    mapped_genes_contigs_mags = mapped_genes_contigs_mags[
        mapped_genes_contigs_mags['Gene ID'].notna()]

    # Drop 'Gene_trunc' column
    mapped_genes_contigs_mags = mapped_genes_contigs_mags. \
        drop(columns="Gene_trunc")

    # # Creating eggNOG annotation dataframe
    eggNOG_df = load_eggNOG_file(eggnog_ann_file)

    # Mapping between genes, contigs, mags and eggNOG annotations
    mapped_genes_contigs_mags_eggNOG = pd.merge(mapped_genes_contigs_mags,
                                                eggNOG_df,
                                                left_on='Gene ID',
                                                right_on='#query_name',
                                                how='outer')

    # determine if non-redundant gene clusters are taxon-specific
    cluster_taxa = mapped_genes_contigs_mags_eggNOG.groupby('Cluster ID')[
        'classification'].nunique()

    # Saving gene mapping results to file
    mapped_genes_contigs_mags_eggNOG.to_csv(out_gene_mapping_file, sep='\t',
                                            index=False, na_rep='NaN')
    # saving cluster_taxa mapping to file
    cluster_taxa.to_csv(out_cluster_taxa_file, sep='\t', header=True)


if __name__ == "__main__":
    _perform_mapping()
