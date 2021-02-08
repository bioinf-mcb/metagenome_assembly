import os
import glob
import pytest
import pandas.util.testing as pdt

from os.path import join
from click.testing import CliRunner

from scripts.transform_deepfri_output import _process_deepfri
from scripts.tests.utils import dict2str, load_df
runner = CliRunner()

INPATH = join(os.getcwd(), "data/input/deepfri")
EXPPATH = join(os.getcwd(), "data/expected")
OUTPATH = join(os.getcwd(), "data/generated/deepfri")


@pytest.fixture(scope="session", autouse=True)
def clean_generated_files():
    print("\nRemoving old generated files...")
    for f in glob.glob(join(OUTPATH, '*')):
        os.remove(f)
    assert glob.glob(join(OUTPATH, '*')) == []


def test_help():
    response = runner.invoke(_process_deepfri, ["--help"])
    assert response.exit_code == 0
    assert " The script takes DeepfRI annotation file" in response.output


def test_basic():
    params = {'-i': join(INPATH, 'deepfri_reduced.tsv'),
              '-g': join(INPATH, 'GO_informative.txt'),
              '-o': join(OUTPATH, 'output.tsv')}
    response = runner.invoke(_process_deepfri, f"{dict2str(params)}")
    assert response.exit_code == 0
    genes_out = load_df(os.path.join(OUTPATH, "output.tsv"))
    genes_exp = load_df(os.path.join(EXPPATH, "deepfri_out.tsv"))
    pdt.assert_frame_equal(genes_out, genes_exp)
