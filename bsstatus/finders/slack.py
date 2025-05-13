"""
Home to the Slack StatusFinder implementation.
"""

import logging
import re
from typing import Any

from cachetools.func import ttl_cache
from slack_sdk import WebClient

from bsstatus.config import SlackConfig
from bsstatus.finders.base import StatusFinder
from bsstatus.status import Status

log = logging.getLogger(__name__)


class SlackStatusFinder(StatusFinder):
    """
    Status finder based off the Slack API.
    """

    def __init__(self, finder_config: SlackConfig) -> None:
        """
        Initializer. Sets up the Slack client.
        """
        super().__init__(finder_config)

        if self.config.token:
            self._client = WebClient(token=self.config.token)
        else:
            self._client = None

        # Compile the regexes to not need to do it on every check.
        self._busy_regex = re.compile(self.config.busy_regex)
        self._away_regex = re.compile(self.config.away_regex)

    @ttl_cache(ttl=5)
    def _get_users_info(self) -> dict[str, Any]:
        """
        Call the slack API up to once every 5 seconds to get the user info.
        """
        return self._client.users_info(user=self.config.user_id).data

    @ttl_cache(ttl=5)
    def _get_dnd_info(self) -> dict[str, Any]:
        """
        Call the slack API up to once every 5 seconds to get the dnd info.
        """
        return self._client.dnd_info(user=self.config.user_id).data

    @ttl_cache(ttl=5)
    def _get_presence(self) -> dict[str, Any]:
        """
        Call the slack API up to once every 5 seconds to get the presence info.
        """
        return self._client.users_getPresence(user=self.config.user_id).data

    def _get_combined_status_text(self) -> str:
        """
        Get the combined status icon + status text from the user info.
        """
        user_info = self._get_users_info()
        profile = user_info["user"]["profile"]
        status_text = profile.get("status_text", "").strip()
        status_emoji = profile.get("status_emoji", "").strip()
        return f"{status_emoji} {status_text}".strip()

    def _is_in_huddle(self) -> bool:
        """
        Check if the user is in a huddle.
        """
        user_info = self._get_users_info()
        profile = user_info["user"]["profile"]
        huddle_state = profile.get("huddle_state")
        return huddle_state is not None and huddle_state != "default_unset"

    def _is_dnd(self) -> bool:
        """
        Check if the user is in do not disturb mode.
        """
        dnd_settings = self._get_dnd_info()
        return dnd_settings["snooze_enabled"]

    def _is_marked_as_away(self) -> bool:
        """
        Check if the user is marked as away.
        """
        presence = self._get_presence()
        return presence["presence"] == "away"

    def _is_status_busy(self) -> bool:
        """
        Check if the user's status text matches the busy regex.
        """
        status_text = self._get_combined_status_text()
        return bool(self._busy_regex.match(status_text))

    def _is_status_away(self) -> bool:
        """
        Check if the user's status text matches the away regex.
        """
        status_text = self._get_combined_status_text()
        return bool(self._away_regex.match(status_text))

    def get_status(self) -> Status:
        """
        Get the current status of the user from Slack.
        """
        if self.config.token and self.config.user_id and self._client:
            # in a huddle
            if self._is_in_huddle():
                log.debug("User is in a huddle")
                return Status.DoNotDisturb

            # marked as dnd
            if self._is_dnd():
                log.debug("User is in do not disturb mode")
                return Status.DoNotDisturb

            # message says busy
            if self._is_status_busy():
                log.debug("User is busy according to status text")
                return Status.Busy

            # message says away
            if self._is_status_away():
                log.debug("User is away according to status text")
                return Status.Away

            # check presence
            if self._is_marked_as_away():
                log.debug("User is away according to presence")
                return Status.Away

            # We did all our checks.. must be available
            log.debug("User is available")
            return Status.Available

        # no idea?
        log.debug("No idea what the status is")
        return Status.Unknown
