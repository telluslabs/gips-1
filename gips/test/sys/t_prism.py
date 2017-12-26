import logging

import pytest
import envoy

from .util import *

logger = logging.getLogger(__name__)

pytestmark = sys  # skip everything unless --sys

# changing this will require changes in expected/
driver = 'prism'
STD_TILE = 'CONUS'
STD_DATES = '1982-12-01,1982-12-03'
STD_ARGS = (driver, '-s', NH_SHP_PATH, '-d', STD_DATES, '-v', '4')


@pytest.fixture
def setup_prism_data(pytestconfig):
    """Use gips_inventory to ensure presence of PRISM data in the data repo."""
    if not pytestconfig.getoption('setup_repo'):
        logger.debug("Skipping repo setup per lack of option.")
        return
    cmd_str = 'gips_inventory ' + ' '.join(STD_ARGS) + ' --fetch'
    logger.info("Downloading PRISM assets with " + cmd_str)
    outcome = envoy.run(cmd_str)
    logger.info("PRISM data download complete.")
    if outcome.status_code != 0:
        raise RuntimeError("PRISM data setup via `gips_inventory` failed",
                           outcome.std_out, outcome.std_err, outcome)


setup_fixture = setup_prism_data

# ###   SHOULD BE STANDARD BELOW HERE #####

def t_process(setup_fixture, repo_env, expected):
    """Test gips_process on {} data.""".format(driver)
    process_actual = repo_env.run('gips_process', *STD_ARGS)
    inventory_actual = envoy.run('gips_inventory ' + ' '.join(STD_ARGS))

    # TODO port this to all drivers that symlink products -- move to util, common call, yadda yadda
    # Check symlinks specially:  Build list of expected paths to symlinks, and their
    # expected targets, then compare with actual symlinks on the filesystem.
    # have to build expectations about symlinks dynamically as they depend on a user setting.
    # setting in question -----vvvvvvvvvvvvvv
    tgt_prefix = '/vsizip//' + DATA_REPO_ROOT.strip('/')
    expected_symlinks = {
        os.path.join(DATA_REPO_ROOT, partial_ln): os.path.join(tgt_prefix, partial_tgt)
        for partial_ln, partial_tgt in expected._symlinks.items()}
    actual_symlinks = {ln: os.readlink(ln) if os.path.islink(ln) else 'Not-a-symlink'
        for ln in expected_symlinks}

    assert (expected == process_actual and inventory_actual.std_out == expected._inv_stdout
        and expected_symlinks == actual_symlinks)


# # TODO: determine why overwrite fails  (see comment in prism driver)
# #       and then uncomment this test.
# def t_process_overwrite(setup_fixture, repo_env, expected):
#     """Test gips_process on {} data.""".format(driver)
#     args = STD_ARGS + ('--overwrite',)
#     process_run1 = repo_env.run('gips_process', *STD_ARGS)
#     process_run2 = repo_env.run('gips_process', *args)
#     assert expected == process_run2
#     assert process_run1.timestamps != process_run2.timestamps

def t_project(setup_fixture, clean_repo_env, output_tfe, expected):
    """Test gips_project {} with warping.""".format(driver)
    args = STD_ARGS + ('--res', '100', '100', '--outdir', OUTPUT_DIR, '--notld')
    actual = output_tfe.run('gips_project', *args)
    assert expected == actual


def t_project_no_warp(setup_fixture, clean_repo_env, output_tfe, expected):
    """Test gips_project {} without warping.""".format(driver)
    args = STD_ARGS + ('--outdir', OUTPUT_DIR, '--notld')
    actual = output_tfe.run('gips_project', *args)
    assert expected == actual


# # Haven't used gips_tiles ever
# def t_tiles(setup_fixture, clean_repo_env, output_tfe, expected):
#     """Test gips_tiles {} with warping.""".format(driver)
#     args = STD_ARGS + ('--outdir', OUTPUT_DIR, '--notld')
#     actual = output_tfe.run('gips_tiles', *args)
#     assert expected == actual


def t_tiles_copy(setup_fixture, clean_repo_env, output_tfe, expected):
    """Test gips_tiles {} with copying.""".format(driver)
    # doesn't quite use STD_ARGS
    args = (driver, '-t', STD_TILE, '-d', STD_DATES, '-v', '4',
            '--outdir', OUTPUT_DIR, '--notld')
    actual = output_tfe.run('gips_tiles', *args)
    assert expected == actual


def t_stats(setup_fixture, clean_repo_env, output_tfe, expected):
    """Test gips_stats on projected files."""
    # generate data needed for stats computation
    args = STD_ARGS + ('--res', '100', '100', '--outdir', OUTPUT_DIR, '--notld')
    prep_run = output_tfe.run('gips_project', *args)
    assert prep_run.exit_status == 0  # confirm it worked; not really in the test

    # compute stats
    gtfe = GipsTestFileEnv(OUTPUT_DIR, start_clear=False)
    actual = gtfe.run('gips_stats', OUTPUT_DIR)

    # check for correct stats content
    assert expected == actual
