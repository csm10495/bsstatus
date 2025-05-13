from unittest.mock import patch

import pytest
from pydantic import ValidationError

from bsstatus.config import Config, get_config


@patch("bsstatus.config.user_config_path")
def test_get_config_file_not_exists(mock_user_config_path, tmp_path):
    mock_user_config_path.return_value = tmp_path
    config_file_path = tmp_path / "config.json"

    assert not config_file_path.exists()

    config = get_config()
    mock_user_config_path.assert_called_once_with("bsstatus", ensure_exists=True)
    assert isinstance(config, Config)

    assert config_file_path.exists()
    assert Config.model_validate_json(config_file_path.read_text()) == config


@patch("bsstatus.config.user_config_path")
def test_get_config_file_exists(mock_user_config_path, tmp_path):
    mock_user_config_path.return_value = tmp_path
    config_file_path = tmp_path / "config.json"

    config_file_path.write_text(Config(pause_time=91).model_dump_json(indent=4))

    assert config_file_path.exists()

    config = get_config()
    mock_user_config_path.assert_called_once_with("bsstatus", ensure_exists=True)
    assert isinstance(config, Config)

    assert config_file_path.exists()
    assert Config.model_validate_json(config_file_path.read_text()) == Config(pause_time=91)


@patch("bsstatus.config.user_config_path")
def test_get_config_file_exists_but_it_has_extra_keys(mock_user_config_path, tmp_path):
    mock_user_config_path.return_value = tmp_path
    config_file_path = tmp_path / "config.json"

    config_file_path.write_text('{"a": 1}')

    with pytest.raises(ValidationError):
        get_config()

    mock_user_config_path.assert_called_once_with("bsstatus", ensure_exists=True)
