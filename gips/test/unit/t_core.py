"""Unit tests for core functions, such as those found in gips.core and gips.data.core."""

import sys

import pytest
import mock

import gips
from gips.data.landsat.landsat import landsatRepository

def t_version_override(mocker):
    """Test gips.__init__.detect_version() for correct override of __version__."""
    env = mocker.patch.object(gips.os, 'environ')
    # os.environ.get is called by libs as well as detect_version(); fortunately no harm seems to
    # come from giving them bad results.

    # no override requested
    env.get.side_effect = lambda key, default=None: default # key not found
    version_a = gips.detect_version()

    # override requested
    env.get.side_effect = lambda key, default=None: 'fancy-new-version'
    version_b = gips.detect_version()

    env.get.assert_has_calls([ # assert two identical calls
        mock.call('GIPS_OVERRIDE_VERSION', gips.version.__version__) for _ in range(2)
    ])
    assert (version_a, version_b) == (gips.version.__version__, 'fancy-new-version')


def t_repository_find_tiles_normal_case(mocker):
    """Test Repository.find_tiles using landsatRepository as a guinea pig."""
    m_list_tiles = mocker.patch('gips.data.core.dbinv.list_tiles')
    expected = [u'tile1', u'tile2', u'tile3'] # list_tiles returns unicode
    m_list_tiles.return_value = expected
    actual = landsatRepository.find_tiles()
    assert expected == actual


def t_repository_find_tiles_error_case(mocker):
    """Confirm Repository.find_tiles falls back to filesystem search."""
    m_list_tiles = mocker.patch('gips.data.core.dbinv.list_tiles')
    m_list_tiles.side_effect = Exception('AAAAAAAAAAH!') # intentionally break list_tiles

    # confirm call was still a success via the righ code path
    with pytest.raises(SystemExit):
        landsatRepository.find_tiles()