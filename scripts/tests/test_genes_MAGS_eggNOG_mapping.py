import os
import glob
import pytest
import pandas.util.testing as pdt

from os.path import join
from click.testing import CliRunner

from scripts.genes_MAGS_eggNOG_mapping import _perform_mapping
from scripts.tests.utils import dict2str, load_df

runner = CliRunner()

INPATH = join(os.getcwd(), "data/input")
EXPPATH = join(os.getcwd(), "data/expected")
OUTPATH = join(os.getcwd(), "data/generated/genes_mags_eggnog")


@pytest.fixture(scope="session", autouse=True)
def clean_generated_files():
    print("\nRemoving old generated files...")
    if not os.path.exists(OUTPATH):
        os.makedirs(OUTPATH)
    for f in glob.glob(join(OUTPATH, '*')):
        os.remove(f)
    assert glob.glob(join(OUTPATH, '*')) == []


def test_help():
    response = runner.invoke(_perform_mapping, ["--help"])
    assert response.exit_code == 0
    assert "Script for mapping genes to contigs" in response.output


def test_basic():
    params = {'-r': join(INPATH, 'cluster_genes/nr.reduced.clstr'),
              '-g': join(INPATH, 'cluster_genes/sample_genes.fa'),
              '-c': join(INPATH, 'assemble/merged.min500.contigs.fa'),
              '-b': join(INPATH, 'metabat2/'),
              '-t': join(INPATH, 'gtdbtk/'),
              '-m': join(INPATH, 'checkm/'),
              '-e': join(INPATH, 'eggnog-mapper/eggNOG_reduced.tsv'),
              '-o': join(OUTPATH)}
    response = runner.invoke(_perform_mapping, f"{dict2str(params)}")
    assert response.exit_code == 0
    for name in ['Mapped_genes_cluster', 'Individual_mapped_genes', 'MAGS']:
        out = load_df(join(OUTPATH, f"{name}.tsv"))
        exp = load_df(join(EXPPATH, f"{name}.tsv"))
        pdt.assert_frame_equal(out, exp)


def test_missing_checkm():
    params = {'-r': join(INPATH, 'cluster_genes/nr.reduced.clstr'),
              '-g': join(INPATH, 'cluster_genes/sample_genes.fa'),
              '-c': join(INPATH, 'assemble/merged.min500.contigs.fa'),
              '-b': join(INPATH, 'metabat2/'),
              '-t': join(INPATH, 'gtdbtk/'),
              '-m': join(INPATH, 'empty/'),  # difference wrt basic
              '-e': join(INPATH, 'eggnog-mapper/eggNOG_reduced.tsv'),
              '-o': join(OUTPATH)}
    response = runner.invoke(_perform_mapping, f"{dict2str(params)}")
    assert response.exit_code == 0
    for name in ['Mapped_genes_cluster', 'Individual_mapped_genes', 'MAGS']:
        out = load_df(join(OUTPATH, f"{name}.tsv"))
        exp = load_df(join(EXPPATH, f"{name}_missing_checkm.tsv"))
        pdt.assert_frame_equal(out, exp)


def test_missing_checkm_and_gtdb():
    params = {'-r': join(INPATH, 'cluster_genes/nr.reduced.clstr'),
              '-g': join(INPATH, 'cluster_genes/sample_genes.fa'),
              '-c': join(INPATH, 'assemble/merged.min500.contigs.fa'),
              '-b': join(INPATH, 'metabat2/'),
              '-t': join(INPATH, 'empty/'),  # difference wrt basic
              '-m': join(INPATH, 'empty/'),  # difference wrt basic
              '-e': join(INPATH, 'eggnog-mapper/eggNOG_reduced.tsv'),
              '-o': join(OUTPATH)}
    response = runner.invoke(_perform_mapping, f"{dict2str(params)}")
    assert response.exit_code == 0
    for name in ['Mapped_genes_cluster', 'Individual_mapped_genes', 'MAGS']:
        out = load_df(join(OUTPATH, f"{name}.tsv"))
        exp = load_df(join(EXPPATH, f"{name}_missing_checkm_gtdb.tsv"))
        pdt.assert_frame_equal(out, exp)
