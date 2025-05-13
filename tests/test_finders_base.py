from unittest.mock import patch

import pytest

from bsstatus.finders.base import StatusFinder


@patch("bsstatus.finders.base.get_config")
def test_base_finder(mock_get_config):
    """
    Test the initialization of the StatusFinder class.
    """
    mock_get_config.return_value = "mocked_config"

    finder = StatusFinder()

    mock_get_config.assert_called_once()
    assert finder.config == "mocked_config"

    with pytest.raises(NotImplementedError):
        finder.get_status()
