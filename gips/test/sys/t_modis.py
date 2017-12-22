from __future__ import print_function

import logging
from datetime import datetime

import pytest
import envoy # deprecated
import sh

import util
from .util import *

logger = logging.getLogger(__name__)

pytestmark = sys # skip everything unless --sys

driver = 'modis'

# changing this will require changes in expected/
STD_ARGS = ('modis', '-s', NH_SHP_PATH, '-d', '2012-12-01,2012-12-03', '-v', '4')

@pytest.fixture
def setup_modis_data(pytestconfig):
    """Use gips_inventory to ensure presence of MODIS data in the data repo."""
    if not pytestconfig.getoption('setup_repo'):
        logger.debug("Skipping repo setup per lack of option.")
        return
    if datetime.today().date().weekday() == 2: # <-- is it Wednesday?
        raise Exception("It seems to be Wednesday; modis downloads are likely to fail.")
    logger.info("Downloading MODIS data . . .")
    cmd_str = 'gips_inventory ' + ' '.join(STD_ARGS) + ' --fetch'
    outcome = envoy.run(cmd_str)
    logger.info("MODIS data download complete.")
    if outcome.status_code != 0:
        #msg = ("MODIS data setup via `gips_inventory` technically failed, but this may be due to false"
        #       " positives in the driver; proceeding with tests")
        #logger.warning(msg)
        #logger.warning('=== standard out:  ' + outcome.std_out)
        #logger.warning('=== standard error:  ' + outcome.std_err)
        raise RuntimeError("MODIS data setup via `gips_inventory` failed",
                           outcome.std_out, outcome.std_err, outcome)


def t_inventory(setup_modis_data, repo_env, expected):
    """Test `gips_inventory modis` and confirm recorded output is given."""
    actual = repo_env.run('gips_inventory', *STD_ARGS)
    assert expected == actual

from .expected import modis as expectations

@pytest.mark.parametrize("product", expectations.t_process.keys())
def t_process(setup_modis_data, repo_wrapper, product):
    """Test gips_process on modis data."""
    record_mode, expected, runner = repo_wrapper
    outcome, actual = runner('gips_process', 'modis', '-s', NH_SHP_PATH,
                             '-d', '2012-12-01,2012-12-03', '-v', '4', '-p',
                             product)
    if not record_mode: # don't evaluate assertions when in record-mode
        assert outcome.exit_code == 0 and expected == actual

def t_info(repo_env, expected):
    """Test `gips_info modis` and confirm recorded output is given."""
    actual = repo_env.run('gips_info', 'modis')
    assert expected == actual

@pytest.mark.parametrize("product", expectations.t_project.keys())
def t_project(setup_modis_data, export_wrapper, product):
    """Test gips_project modis with warping."""
    record_mode, expected, runner = export_wrapper
    args = STD_ARGS + ('--res', '100', '100', '--outdir', OUTPUT_DIR,
                       '--notld', '-p', product)
    outcome, actual = runner('gips_project', *args)
    if not record_mode: # don't evaluate assertions when in record-mode
        assert outcome.exit_code == 0 and expected == actual

# TODO keep this test?
'''
def t_project_no_warp(setup_modis_data, clean_repo_env, output_tfe, expected):
    """Test gips_project modis without warping."""
    args = STD_ARGS + ('--outdir', OUTPUT_DIR, '--notld')
    actual = output_tfe.run('gips_project', *args)
    assert expected == actual
'''

def t_tiles(setup_modis_data, clean_repo_env, output_tfe, expected):
    """Test gips_tiles modis with warping."""
    args = STD_ARGS + ('--outdir', OUTPUT_DIR, '--notld')
    actual = output_tfe.run('gips_tiles', *args)
    assert expected == actual


def t_tiles_copy(setup_modis_data, clean_repo_env, output_tfe, expected):
    """Test gips_tiles modis with copying."""
    # doesn't quite use STD_ARGS
    args = ('modis', '-t', 'h12v04', '-d', '2012-12-01,2012-12-03', '-v', '4',
            '--outdir', OUTPUT_DIR, '--notld')
    actual = output_tfe.run('gips_tiles', *args)
    assert expected == actual


def t_stats(setup_modis_data, clean_repo_env, output_tfe, expected):
    """Test gips_stats on projected files."""
    # generate data needed for stats computation
    args = STD_ARGS + ('--res', '100', '100', '--outdir', OUTPUT_DIR, '--notld')
    prep_run = output_tfe.run('gips_project', *args)
    assert prep_run.exit_status == 0 # confirm it worked; not really in the test

    # compute stats
    gtfe = GipsTestFileEnv(OUTPUT_DIR, start_clear=False)
    actual = gtfe.run('gips_stats', OUTPUT_DIR)

    # check for correct stats content
    assert expected == actual
    
    
def t_gridded_export(setup_modis_data, clean_repo_env, output_tfe, expected):
    """Test gips_project using rastermask spatial spec"""
    rastermask = os.path.join(TEST_DATA_DIR, 'site_mask.tif')
    args = ('modis', '-p', 'indices', '-r', rastermask, '--fetch',
            '-d', '2005-01-01',
            '--outdir', OUTPUT_DIR, '--notld')

    actual = output_tfe.run('gips_project', *args)
    assert expected == actual

    
def t_cubic_gridded_export(setup_modis_data, clean_repo_env, output_tfe, expected):
    """Test gips_project using rastermask spatial spec"""
    rastermask = os.path.join(TEST_DATA_DIR, 'site_mask.tif')
    args = ('modis', '-p', 'indices', '-r', rastermask, '--fetch',
            '-d', '2005-01-01', '--interpolation', "2",
            '--outdir', OUTPUT_DIR, '--notld')

    actual = output_tfe.run('gips_project', *args)
    assert expected == actual

