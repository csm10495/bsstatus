"""
Configuration interface for bsstatus.

bsstatus stores its configurations in the config.json file inside
the bsstatus directory in the user's config directory.

We use the platformdirs library to determine the user's config directory.
"""

import logging

from platformdirs import user_config_path
from pydantic import BaseModel, ConfigDict

log = logging.getLogger(__name__)


class SlackConfig(BaseModel):
    """
    Holds configurations for working with Slack.
    """

    # The user id of the user to monitor. NOT the slack user name.
    user_id: str | None = None

    # Usually starts with xoxp-
    # Need at leastt dnd:read and users:read
    token: str | None = None

    # When parsing the status text, if this regex matches, the user is considered busy.
    busy_regex: str = ".*busy.*"

    # When parsing the status text, if this regex matches, the user is considered away.
    away_regex: str = ".*(afk|brb|be right back|lunch|walking).*"


class ICalConfig(BaseModel):
    """
    Holds configurations for working with an iCal.
    """

    # The URL of the iCal to monitor.
    url: str | None = None

    # The timezone to assume for the ical (if not otherwise determined).
    # Example: 'America/Los_Angeles'
    assumed_timezone: str | None = None


class BlinkstickConfig(BaseModel):
    """
    Holds configurations for working with the Blinkstick.
    """

    # The color to use when the user is away.
    away_color: int = 0x323200

    # The color to use when the user is busy.
    busy_color: int = 0x332100

    # The color to use when the user is do not disturb.
    dnd_color: int = 0x320000

    # The color to use when the user is available.
    available_color: int = 0x003200

    # The color to use when the user state is unknown.
    unknown_color: int = 0x000032


class Config(BaseModel):
    """
    Holds all configurations for bsstatus.
    """

    # We can monitor multiple slacks at once.
    slacks: list[SlackConfig] = [SlackConfig()]

    # We can monitor multiple icals at once.
    icals: list[ICalConfig] = [ICalConfig()]

    # There is only one blinkstick configuration
    blinkstick: BlinkstickConfig = BlinkstickConfig()

    # The time (in seconds) to wait between checking the status of the user.
    pause_time: int = 5

    model_config = ConfigDict(extra="forbid")


def get_config() -> Config:
    """
    Fetch a Config object based off the config file.

    If the config file does not exist, it will be created with default values.
    """
    config_dir_path = user_config_path("bsstatus", ensure_exists=True)
    config_file_path = config_dir_path / "config.json"

    if not config_file_path.exists():
        log.debug(f"Writing new config file (with defaults) to {config_file_path}")
        config_file_path.write_text(Config().model_dump_json(indent=4))

    c = Config.model_validate_json(config_file_path.read_text())
    log.debug(f"Config: {c.model_dump_json(indent=4)}")
    return c
