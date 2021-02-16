#! /usr/bin/env python

import click
import pandas as pd
import obonet
import networkx as nx


# propagate GO terms
def propagate_go(goterms, go_graph):
    """
    Propagate GO terms based on Graph

    Parameters
    ----------
    goterms : list
    go_graph : networkx.classes.multidigraph.MultiDiGraph

    Returns
    -------
    String with comma-separated GO terms

    """
    all_goterms = set()
    for goterm in list(goterms):
        # dealing with obsolete GO terms
        try:
            parents = nx.descendants(go_graph, goterm)
            all_goterms = all_goterms.union(parents)
        except:
            all_goterms = all_goterms.union(set([goterm]))
    # adding original GOs
    all_goterms = all_goterms.union(set(goterms))
    # root terms
    root_terms = {'GO:0008150', 'GO:0003674', 'GO:0005575'}
    # pruning root terms
    all_goterms = all_goterms.difference(root_terms)
    return ','.join(sorted(all_goterms))


@click.command()
@click.option('--gene_mapper_file', '-g', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True),
              help='Input gene mapping table .tsv file')
@click.option('--tree', '-t', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=True),
              help='obo tree')
@click.option('--out_file', '-o', required=True,
              type=click.Path(resolve_path=True, readable=True, exists=False),
              help='Output .tsv file.')
def _propagate_GO(gene_mapper_file, tree, out_file):
    """
    Script for Propagation of GO terms.

    Input files required:
    1) go graph
    2) EggNOG GO predictions
    3) Name of output file

    Output:
    1) propagated Gene ontologies
    """

    with open(tree, 'r') as f:
        go_graph = obonet.read_obo(f)

    # load gene mapper table
    mapped_genes = pd.read_csv(gene_mapper_file, sep="\t")

    # drop NAN in the Gene ID column
    mapped_genes = mapped_genes[mapped_genes['Gene ID'].notna()]

    # subset data and drop NANs in the GOs column
    genes_GO_df = mapped_genes[["Gene ID", "GOs"]].dropna()

    # propagate GO terms
    genes_GO_df['GOs_propagated'] = genes_GO_df['GOs'].str.split(',').\
        apply(propagate_go, go_graph=go_graph)

    # save the file
    genes_GO_df.to_csv(out_file, sep='\t', index=False)


if __name__ == "__main__":
    _propagate_GO()

