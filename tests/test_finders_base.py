import pytest

from bsstatus.finders.base import StatusFinder


def test_base_finder():
    finder = StatusFinder("mocked_config")
    assert finder.config == "mocked_config"

    with pytest.raises(NotImplementedError):
        finder.get_status()
