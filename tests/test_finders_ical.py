from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from icalendar import Calendar

from bsstatus.config import ICalConfig
from bsstatus.finders.ical import ICalStatusFinder
from bsstatus.status import Status

# All our tests assume this timezone
TESTING_TIMEZONE = ZoneInfo("America/Los_Angeles")

# 20250328 ... 20250401
ALL_DAY_EVENT = """BEGIN:VEVENT
UID:40000008200E00074C5B7101A82E0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
 AAAAAAAAAAAAAAAAAA
SUMMARY:Ryans DTO
DTSTART;VALUE=DATE:20250328
DTEND;VALUE=DATE:20250401
CLASS:PUBLIC
PRIORITY:5
DTSTAMP:20250514T014416Z
TRANSP:TRANSPARENT
STATUS:CONFIRMED
SEQUENCE:0
LOCATION:
X-MICROSOFT-CDO-APPT-SEQUENCE:0
X-MICROSOFT-CDO-BUSYSTATUS:BUSY
X-MICROSOFT-CDO-INTENDEDSTATUS:BUSY
X-MICROSOFT-CDO-ALLDAYEVENT:TRUE
X-MICROSOFT-CDO-IMPORTANCE:1
X-MICROSOFT-CDO-INSTTYPE:0
X-MICROSOFT-DONOTFORWARDMEETING:FALSE
X-MICROSOFT-DISALLOW-COUNTER:FALSE
X-MICROSOFT-REQUESTEDATTENDANCEMODE:DEFAULT
X-MICROSOFT-ISRESPONSEREQUESTED:FALSE
END:VEVENT
"""


# Noon to 1pm pacific time, daily
DAILY_LUNCH_EVENT = """BEGIN:VEVENT
RRULE:FREQ=DAILY;UNTIL=20260513T190000Z;INTERVAL=1
UID:040000008200E00074C5B7100AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
 ABCABCABCABC
SUMMARY:Lunch Block
DTSTART;TZID=Pacific Standard Time:20240513T120000
DTEND;TZID=Pacific Standard Time:20240513T130000
CLASS:PUBLIC
PRIORITY:5
DTSTAMP:20250514T014416Z
TRANSP:OPAQUE
STATUS:CONFIRMED
SEQUENCE:0
LOCATION:
X-MICROSOFT-CDO-APPT-SEQUENCE:0
X-MICROSOFT-CDO-BUSYSTATUS:BUSY
X-MICROSOFT-CDO-INTENDEDSTATUS:BUSY
X-MICROSOFT-CDO-ALLDAYEVENT:FALSE
X-MICROSOFT-CDO-IMPORTANCE:1
X-MICROSOFT-CDO-INSTTYPE:1
X-MICROSOFT-DONOTFORWARDMEETING:FALSE
X-MICROSOFT-DISALLOW-COUNTER:FALSE
X-MICROSOFT-REQUESTEDATTENDANCEMODE:DEFAULT
X-MICROSOFT-ISRESPONSEREQUESTED:FALSE
END:VEVENT
"""


def event_text_to_calendar(event_text: str) -> str:
    """
    Converts the event text to a calendar text.
    """
    return Calendar.from_ical(f"""BEGIN:VCALENDAR
VERSION:2.0
{event_text}
END:VCALENDAR""")


@pytest.fixture
def ical_status_finder():
    yield ICalStatusFinder(
        ICalConfig(url="ical-url"),
    )


def test_init(ical_status_finder):
    config = ical_status_finder.config
    del ical_status_finder.config

    ical_status_finder.__init__(config)
    assert ical_status_finder.config == config


@patch("bsstatus.finders.ical.requests.get", return_value=MagicMock(text=ALL_DAY_EVENT))
@patch("bsstatus.finders.ical.Calendar.from_ical", return_value="calendar")
def test_get_calendar_with_url(mock_from_ical, mock_get, ical_status_finder):
    assert ical_status_finder._get_calendar() == "calendar"

    mock_get.assert_called_once_with("ical-url")
    mock_get.return_value.raise_for_status.assert_called_once()
    mock_from_ical.assert_called_once_with(ALL_DAY_EVENT)


def test_get_calendar_without_url(ical_status_finder):
    ical_status_finder.config.url = None
    assert ical_status_finder._get_calendar() == Calendar()


def test_get_event_name(ical_status_finder):
    assert ical_status_finder._get_event_name(Calendar.from_ical(ALL_DAY_EVENT)) == "Ryans DTO"
    assert ical_status_finder._get_event_name(Calendar.from_ical(DAILY_LUNCH_EVENT)) == "Lunch Block"
    assert ical_status_finder._get_event_name(Calendar()) is None


def test_should_ignore_event(ical_status_finder):
    event = Calendar.from_ical(ALL_DAY_EVENT)

    ical_status_finder.config.ignore_events_matching_any_of_all = [
        {
            "X-MICROSOFT-REQUESTEDATTENDANCEMODE": "DEFAULT",
        }
    ]
    assert ical_status_finder._should_ignore_event(event)

    ical_status_finder.config.ignore_events_matching_any_of_all = [
        {
            "X-MICROSOFT-REQUESTEDATTENDANCEMODE": "POTATOES",
        }
    ]
    assert not ical_status_finder._should_ignore_event(event)

    ical_status_finder.config.ignore_events_matching_any_of_all = [
        {
            "X-MICROSOFT-REQUESTEDATTENDANCEMODE": "POTATOES",
            "SOMETHING-ELSE": "FALSE",
        }
    ]
    assert not ical_status_finder._should_ignore_event(event)

    ical_status_finder.config.ignore_events_matching_any_of_all = [
        {
            "X-MICROSOFT-REQUESTEDATTENDANCEMODE": "POTATOES",
        },
        {"SOMETHING-ELSE": "FALSE"},
    ]
    assert not ical_status_finder._should_ignore_event(event)

    ical_status_finder.config.ignore_events_matching_any_of_all = [
        {
            "X-MICROSOFT-REQUESTEDATTENDANCEMODE": "DEFAULT",
            "X-MICROSOFT-CDO-BUSYSTATUS": "BUSY",
        },
        {"SOMETHING-ELSE": "FALSE"},
    ]
    assert ical_status_finder._should_ignore_event(event)


@patch("bsstatus.finders.ical.datetime")
@patch("bsstatus.finders.ical.get_localzone", return_value=TESTING_TIMEZONE)
def test_get_now(mock_get_localzone, mock_datetime, ical_status_finder):
    mock_datetime.now.return_value = "now"

    assert ical_status_finder._get_now() == "now"

    mock_get_localzone.assert_called_once_with()
    mock_datetime.now.assert_called_once_with(mock_get_localzone.return_value)


def test_get_events_going_on_now_match(ical_status_finder):
    ical_status_finder._should_ignore_event = MagicMock(return_value=False)
    ical_status_finder._get_calendar = MagicMock(return_value=event_text_to_calendar(DAILY_LUNCH_EVENT))
    ical_status_finder._get_now = MagicMock(return_value=datetime(2024, 5, 13, 12, 0, tzinfo=TESTING_TIMEZONE))

    events = ical_status_finder._get_events_going_on_now()
    assert len(events) == 1
    assert ical_status_finder._get_event_name(events[0]) == "Lunch Block"
    ical_status_finder._should_ignore_event.assert_called_once_with(events[0])


def test_get_events_going_on_now_match_but_ignoring(ical_status_finder):
    ical_status_finder._should_ignore_event = MagicMock(return_value=True)
    ical_status_finder._get_calendar = MagicMock(return_value=event_text_to_calendar(DAILY_LUNCH_EVENT))
    ical_status_finder._get_now = MagicMock(return_value=datetime(2024, 5, 13, 12, 0, tzinfo=TESTING_TIMEZONE))

    assert len(ical_status_finder._get_events_going_on_now()) == 0
    ical_status_finder._should_ignore_event.assert_called_once()


def test_get_events_going_on_now_no_match(ical_status_finder):
    ical_status_finder._should_ignore_event = MagicMock(return_value=False)
    ical_status_finder._get_calendar = MagicMock(return_value=event_text_to_calendar(DAILY_LUNCH_EVENT))
    ical_status_finder._get_now = MagicMock(return_value=datetime(2024, 5, 13, 14, 0, tzinfo=TESTING_TIMEZONE))

    assert len(ical_status_finder._get_events_going_on_now()) == 0
    ical_status_finder._should_ignore_event.assert_not_called()


def test_in_event_now(ical_status_finder):
    ical_status_finder._get_events_going_on_now = MagicMock(return_value=[1, 2, 3])
    assert ical_status_finder._in_event_now()
    ical_status_finder._get_events_going_on_now.assert_called_once()


def test_in_event_now_no_events(ical_status_finder):
    ical_status_finder._get_events_going_on_now = MagicMock(return_value=[])
    assert not ical_status_finder._in_event_now()
    ical_status_finder._get_events_going_on_now.assert_called_once()


def test_get_status(ical_status_finder):
    ical_status_finder._in_event_now = MagicMock(return_value=True)
    assert ical_status_finder.get_status() == Status.Busy

    ical_status_finder._in_event_now = MagicMock(return_value=False)
    assert ical_status_finder.get_status() == Status.Available

    ical_status_finder.config.url = None
    assert ical_status_finder.get_status() == Status.Unknown


@pytest.mark.parametrize(
    "now,status",
    [
        # lunch
        (datetime(2024, 5, 13, 12, 0, tzinfo=TESTING_TIMEZONE), Status.Busy),
        # nothing
        (datetime(2024, 5, 13, 14, 0, tzinfo=TESTING_TIMEZONE), Status.Available),
        # Ryan's DTO doesn't matter to me since it's all day and by default that is ignored.
        (datetime(2025, 5, 14, 11, 0, tzinfo=TESTING_TIMEZONE), Status.Available),
    ],
)
def test_e2e_at_times(ical_status_finder, now, status):
    ical_status_finder._get_now = MagicMock(return_value=now)
    ical_status_finder._get_calendar = MagicMock(return_value=event_text_to_calendar(ALL_DAY_EVENT + DAILY_LUNCH_EVENT))
    assert ical_status_finder.get_status() == status
