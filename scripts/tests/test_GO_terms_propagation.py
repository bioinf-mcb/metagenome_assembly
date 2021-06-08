import os
import glob
import pytest
import pandas.util.testing as pdt

from os.path import join
from click.testing import CliRunner

from scripts.GO_terms_propagation import _propagate_GO
from scripts.tests.utils import dict2str, load_df
runner = CliRunner()

INPATH = join(os.getcwd(), "data/input/go_propagation")
EXPPATH = join(os.getcwd(), "data/expected")
OUTPATH = join(os.getcwd(), "data/generated/go_propagation")


@pytest.fixture(scope="session", autouse=True)
def clean_generated_files():
    print("\nRemoving old generated files...")
    if not os.path.exists(OUTPATH):
        os.makedirs(OUTPATH)
    for f in glob.glob(join(OUTPATH, '*')):
        os.remove(f)
    assert glob.glob(join(OUTPATH, '*')) == []


def test_help():
    response = runner.invoke(_propagate_GO, ["--help"])
    assert response.exit_code == 0
    assert " Script for Propagation of GO terms." in response.output


def test_basic():
    params = {'-g': join(INPATH, 'map_red.tsv'),
              '-t': join(INPATH, 'go-basic.obo.1'),
              '-o': join(OUTPATH, 'output.tsv')}
    response = runner.invoke(_propagate_GO, f"{dict2str(params)}")
    assert response.exit_code == 0
    genes_out = load_df(join(OUTPATH, "output.tsv"))
    genes_exp = load_df(join(EXPPATH, "new_tree_propagated_GO.tsv"))
    pdt.assert_frame_equal(genes_out, genes_exp)
