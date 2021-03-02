#! /usr/bin/env python

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
                                   columns=['Cluster_ID', 'Gene_ID'])
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


def load_checkm_files(file, colnames):
    """
    Reads CHECKM txt file and extracts specified columns.

    Parameters
    ----------
    input_file : str
      txt file containing CHECKM report
    colnames : list of str
        column names

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
    return pd.DataFrame(data=CHECKM[1:], columns=CHECKM[0])[colnames]


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
        checkm_df = checkm_df.append(load_checkm_files(checkm_file, colnames))
    except:
        print('Missing or empty checkM output file:', checkm_file)
    checkm_df.rename({"Bin Id": "Bin_ID", "# genomes": "n_genomes",
                      "# markers": "n_markers"}, axis=1, inplace=True)

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
    raw_df = pd.DataFrame({"MAG_ID": mags, "Bin_ID": bins, "contigs": contigs})

    # Add taxonomy information
    taxonomy_file = os.path.join(taxonomy_path,
                                 f"{mag_root}.bac120.summary.tsv")
    taxonomy_cols = ["user_genome", "classification", "fastani_reference"]
    try:
        f = open(taxonomy_file, "r")
        taxonomies_df = pd.read_csv(f, sep='\t', usecols=taxonomy_cols)
        merged_df = raw_df.join(taxonomies_df.set_index(taxonomy_cols[0]),
                                on='Bin_ID', how='left')
    except:
        print(f'Missing or empty taxonomy file: {taxonomy_file}')
        print('Adding empty taxonomy columns...')
        merged_df = raw_df.join(raw_df.reindex(columns=taxonomy_cols[1:]))

    # Add checkM information
    merged_df = merged_df.join(checkm_df.set_index('Bin_ID'), on='Bin_ID',
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
@click.option('--out_folder', '-o', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True),
              help='Output folder.')
def _perform_mapping(cluster_file, genes_file, contigs_file,
                     eggnog_ann_file, bin_fp, tax_fp, checkm_fp,
                     out_folder):
    """
    Script for mapping genes to contigs, MAGS and eggNOG annotations

    input files required:
    1) clustering file with cluster ID and gene ID
    2) Non-redundant gene catalogue (fasta)
    3) Contig files (fasta)
    4) binned contigs (MAGS)
    5) taxonomy files (tsv)
    6) taxonomy files (tsv)
    7) EggNOG annotation file (tsv)
    8) Name of output folder with gene mappings

    The script outputs three tsv files:
    1) Gene cluster table
    2) Individual gene table
    3) MAG table
    """

    # load cluster file
    cluster_df = tabulate_cluster_info(cluster_file)

    # load contig and gene IDs
    contigs = load_fasta_ids(contigs_file)
    genes = load_fasta_ids(genes_file)

    # create gene catalogue dataframe
    genes_df = pd.DataFrame({'centroid': genes})
    genes_df = genes_df.astype(str)

    # create contigs dataframe
    contigs_df = pd.DataFrame({'Contig_ID': contigs})
    contigs_df = contigs_df.astype(str)

    # map cluster and NR genes
    mapped_centroid_genes = pd.merge(cluster_df, genes_df,
                                     left_on='Gene_ID',
                                     right_on='centroid',
                                     how='inner')[['Cluster_ID', 'centroid']]

    # mapped cluster genes
    mapped_cluster_genes = pd.merge(cluster_df, mapped_centroid_genes,
                                    left_on='Cluster_ID',
                                    right_on='Cluster_ID',
                                    how='outer')

    # create column with truncated gene ids
    mapped_cluster_genes['Gene_trunc'] = mapped_cluster_genes['Gene_ID']. \
        apply(lambda x: x.rsplit('_', 1)[0])

    # change data type to string
    mapped_cluster_genes = mapped_cluster_genes.astype(str)

    # map cluster genes to contigs
    mapped_genes_contigs = pd.merge(mapped_cluster_genes, contigs_df,
                                    left_on='Gene_trunc',
                                    right_on='Contig_ID',
                                    how='left')

    # MAGS and Taxonomy mapping
    MAGS_df = load_mags_contigs_taxonomies(bin_fp, tax_fp, checkm_fp)

    # mapping between genes, contigs and mags
    mapped_genes_contigs_mags = pd.merge(mapped_genes_contigs, MAGS_df,
                                         left_on='Contig_ID',
                                         right_on='contigs',
                                         how='outer')
    # remove partial genes
    mapped_genes_contigs_mags = mapped_genes_contigs_mags[
        mapped_genes_contigs_mags['Gene_ID'].notna()]

    # create eggNOG annotation dataframe
    eggNOG_df = load_eggNOG_file(eggnog_ann_file)

    # mapping between genes, contigs, mags and eggNOG annotations
    mapped_genes_contigs_mags_eggNOG = pd.merge(mapped_genes_contigs_mags,
                                                eggNOG_df,
                                                left_on='Gene_ID',
                                                right_on='#query_name',
                                                how='outer')

    # drop unused columns and replace spaces with tabs in the rest
    mapped_genes_contigs_mags_eggNOG.\
        drop(columns=["Gene_trunc", "contigs", "#query_name"], inplace=True)
    old_cols = mapped_genes_contigs_mags_eggNOG.columns
    new_cols = ["_".join(col.split(' ')) for col in old_cols]
    mapped_genes_contigs_mags_eggNOG.rename(dict(zip(old_cols, new_cols)),
                                            axis=1, inplace=True)

    # split master table into three and save results
    gene_clust_cols = ['Cluster_ID', 'centroid', 'seed_eggNOG_ortholog',
                       'seed_ortholog_evalue', 'seed_ortholog_score',
                       'best_tax_level', 'Preferred_name', 'GOs', 'EC',
                       'KEGG_ko', 'KEGG_Pathway', 'KEGG_Module',
                       'KEGG_Reaction', 'KEGG_rclass', 'BRITE', 'KEGG_TC',
                       'CAZy', 'BiGG_Reaction', 'taxonomic_scope',
                       'eggNOG_OGs', 'best_eggNOG_OG', 'COG_Functional_cat.',
                       'eggNOG_free_text_desc.']
    gene_table_cols = ['Cluster_ID', 'Gene_ID', 'Contig_ID', 'MAG_ID']
    mags_table_cols = ['MAG_ID', 'classification', 'fastani_reference',
                       'Marker_lineage', 'n_genomes', 'n_markers',
                       'Completeness', 'Contamination', 'Strain_heterogeneity']
    mapped_genes_contigs_mags_eggNOG[gene_clust_cols].to_csv(os.path.join(
        out_folder, 'Mapped_genes_cluster.tsv'), sep='\t', na_rep='NaN')
    mapped_genes_contigs_mags_eggNOG[gene_table_cols].to_csv(os.path.join(
        out_folder, 'Individual_mapped_genes.tsv'), sep='\t', na_rep='NaN')
    mapped_genes_contigs_mags_eggNOG[mags_table_cols].to_csv(os.path.join(
        out_folder, 'MAGS.tsv'), sep='\t', na_rep='NaN')

if __name__ == "__main__":
    _perform_mapping()
