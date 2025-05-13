from unittest.mock import MagicMock, patch

import pytest

from bsstatus.config import SlackConfig
from bsstatus.finders.slack import SlackStatusFinder
from bsstatus.status import Status

USERS_INFO_RESPONSE_DATA = {
    "ok": True,
    "user": {
        "id": "U08341W132A",
        "team_id": "T083AHE18Q3",
        "name": "csm10495",
        "deleted": False,
        "color": "84b22f",
        "real_name": "csm10495",
        "tz": "America/Los_Angeles",
        "tz_label": "Pacific Daylight Time",
        "tz_offset": -25200,
        "profile": {
            "title": "",
            "phone": "",
            "skype": "",
            "real_name": "csm10495",
            "real_name_normalized": "csm10495",
            "display_name": "",
            "display_name_normalized": "",
            "fields": None,
            "status_text": "",
            "status_emoji": "",
            "status_emoji_display_info": [],
            "status_expiration": 0,
            "avatar_hash": "g13d236234ff",
            "huddle_state": "default_unset",
            "first_name": "csm10495",
            "last_name": "",
            "image_24": "https://secure.gravatar.com/avatar/13d236234ffb822e312c7cfd90740c74.jpg?s=24&d=https%3A%2F%2Fa.slack-edge.com%2Fdf10d%2Fimg%2Favatars%2Fava_0007-24.png",
            "image_32": "https://secure.gravatar.com/avatar/13d236234ffb822e312c7cfd90740c74.jpg?s=32&d=https%3A%2F%2Fa.slack-edge.com%2Fdf10d%2Fimg%2Favatars%2Fava_0007-32.png",
            "image_48": "https://secure.gravatar.com/avatar/13d236234ffb822e312c7cfd90740c74.jpg?s=48&d=https%3A%2F%2Fa.slack-edge.com%2Fdf10d%2Fimg%2Favatars%2Fava_0007-48.png",
            "image_72": "https://secure.gravatar.com/avatar/13d236234ffb822e312c7cfd90740c74.jpg?s=72&d=https%3A%2F%2Fa.slack-edge.com%2Fdf10d%2Fimg%2Favatars%2Fava_0007-72.png",
            "image_192": "https://secure.gravatar.com/avatar/13d236234ffb822e312c7cfd90740c74.jpg?s=192&d=https%3A%2F%2Fa.slack-edge.com%2Fdf10d%2Fimg%2Favatars%2Fava_0007-192.png",
            "image_512": "https://secure.gravatar.com/avatar/13d236234ffb822e312c7cfd90740c74.jpg?s=512&d=https%3A%2F%2Fa.slack-edge.com%2Fdf10d%2Fimg%2Favatars%2Fava_0007-512.png",
            "status_text_canonical": "",
            "team": "T083AHE18Q3",
        },
        "is_admin": True,
        "is_owner": True,
        "is_primary_owner": True,
        "is_restricted": False,
        "is_ultra_restricted": False,
        "is_bot": False,
        "is_app_user": False,
        "updated": 1746844916,
        "is_email_confirmed": True,
        "has_2fa": False,
        "who_can_share_contact_card": "EVERYONE",
    },
}

DND_INFO_RESPONSE_DATA = {
    "ok": True,
    "dnd_enabled": True,
    "next_dnd_start_ts": 1747112400,
    "next_dnd_end_ts": 1747148400,
    "snooze_enabled": False,
}

USER_PRESENCE_RESPONSE_DATA = {
    "ok": True,
    "presence": "away",
    "online": False,
    "auto_away": False,
    "manual_away": False,
    "connection_count": 0,
}


@pytest.fixture
def mock_slack_api():
    with patch("bsstatus.finders.slack.WebClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.users_info.return_value = MagicMock(data=USERS_INFO_RESPONSE_DATA)
        mock_instance.dnd_info.return_value = MagicMock(data=DND_INFO_RESPONSE_DATA)
        mock_instance.users_getPresence.return_value = MagicMock(data=USER_PRESENCE_RESPONSE_DATA)
        yield mock_instance


@pytest.fixture
def slack_status_finder(mock_slack_api):
    yield SlackStatusFinder(
        SlackConfig(token="fake-token", user_id="fake-user-id", busy_regex=".*busy.*", away_regex=".*away.*")
    )


def test_init_with_token_and_user_id(slack_status_finder):
    sc = SlackConfig(token="fake-token", user_id="fake-user-id", busy_regex=".*busy.*", away_regex=".*away.*")
    slack_status_finder.__init__(sc)

    assert slack_status_finder.config == sc
    assert slack_status_finder._client is not None
    assert slack_status_finder._busy_regex.pattern == ".*busy.*"
    assert slack_status_finder._away_regex.pattern == ".*away.*"


def test_init_without_token_or_user_id(slack_status_finder):
    sc = SlackConfig(token=None, user_id=None, busy_regex=".*busy.*", away_regex=".*away.*")
    slack_status_finder.__init__(sc)

    assert slack_status_finder.config == sc
    assert slack_status_finder._client is None
    assert slack_status_finder._busy_regex.pattern == ".*busy.*"
    assert slack_status_finder._away_regex.pattern == ".*away.*"


def test_get_users_info(slack_status_finder):
    users_info = slack_status_finder._get_users_info()
    assert users_info == USERS_INFO_RESPONSE_DATA
    slack_status_finder._client.users_info.assert_called_once_with(user="fake-user-id")


def test_get_dnd_info(slack_status_finder):
    dnd_info = slack_status_finder._get_dnd_info()
    assert dnd_info == DND_INFO_RESPONSE_DATA
    slack_status_finder._client.dnd_info.assert_called_once_with(user="fake-user-id")


def test_get_presence(slack_status_finder):
    presence = slack_status_finder._get_presence()
    assert presence == USER_PRESENCE_RESPONSE_DATA
    slack_status_finder._client.users_getPresence.assert_called_once_with(user="fake-user-id")


def test_get_combined_status_text(slack_status_finder):
    slack_status_finder._client.users_info.return_value.data["user"]["profile"]["status_text"] = " status text! "
    slack_status_finder._client.users_info.return_value.data["user"]["profile"]["status_emoji"] = " :smile: "

    assert slack_status_finder._get_combined_status_text() == ":smile: status text!"


def test_is_in_huddle(slack_status_finder):
    assert not slack_status_finder._is_in_huddle()

    slack_status_finder._client.users_info.return_value.data["user"]["profile"]["huddle_state"] = "set"
    assert slack_status_finder._is_in_huddle()


def test_is_dnd(slack_status_finder):
    assert not slack_status_finder._is_dnd()

    slack_status_finder._client.dnd_info.return_value.data["snooze_enabled"] = True
    assert slack_status_finder._is_dnd()


def test_is_marked_as_away(slack_status_finder):
    assert slack_status_finder._is_marked_as_away()

    slack_status_finder._client.users_getPresence.return_value.data["presence"] = "active"
    assert not slack_status_finder._is_marked_as_away()


def test_is_status_busy(slack_status_finder):
    slack_status_finder._get_combined_status_text = MagicMock(return_value="I am busy")
    assert slack_status_finder._is_status_busy()

    slack_status_finder._get_combined_status_text = MagicMock(return_value="I am a potato")
    assert not slack_status_finder._is_status_busy()


def test_is_status_away(slack_status_finder):
    slack_status_finder._get_combined_status_text = MagicMock(return_value="I am away")
    assert slack_status_finder._is_status_away()

    slack_status_finder._get_combined_status_text = MagicMock(return_value="I am a potato")
    assert not slack_status_finder._is_status_away()


def test_get_status_missing_configs(slack_status_finder):
    slack_status_finder.config.token = None
    slack_status_finder.config.user_id = None

    assert slack_status_finder.get_status() == Status.Unknown


def test_get_status_all(slack_status_finder):
    slack_status_finder._is_in_huddle = MagicMock(return_value=True)
    assert slack_status_finder.get_status() == Status.DoNotDisturb

    slack_status_finder._is_in_huddle = MagicMock(return_value=False)
    slack_status_finder._is_dnd = MagicMock(return_value=True)
    assert slack_status_finder.get_status() == Status.DoNotDisturb

    slack_status_finder._is_dnd = MagicMock(return_value=False)
    slack_status_finder._is_status_busy = MagicMock(return_value=True)
    assert slack_status_finder.get_status() == Status.Busy

    slack_status_finder._is_status_busy = MagicMock(return_value=False)
    slack_status_finder._is_status_away = MagicMock(return_value=True)
    assert slack_status_finder.get_status() == Status.Away

    slack_status_finder._is_status_away = MagicMock(return_value=False)
    slack_status_finder._is_marked_as_away = MagicMock(return_value=True)
    assert slack_status_finder.get_status() == Status.Away

    slack_status_finder._is_marked_as_away = MagicMock(return_value=False)
    assert slack_status_finder.get_status() == Status.Available
