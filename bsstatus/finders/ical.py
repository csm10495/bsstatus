"""
Home to the ICalStatusFinder StatusFinder implementation.
"""

import logging
from datetime import datetime

import recurring_ical_events
import requests
from cachetools.func import ttl_cache
from icalendar import Calendar, Event
from tzlocal import get_localzone

from bsstatus.config import ICalConfig
from bsstatus.finders.base import StatusFinder
from bsstatus.status import Status

log = logging.getLogger(__name__)


class ICalStatusFinder(StatusFinder):
    """
    Status finder based off an event on a calendar.
    """

    def __init__(self, finder_config: ICalConfig):
        """
        Initializer. Caches the timezone ZoneInfo based off the config.
        """
        super().__init__(finder_config)

    @ttl_cache(ttl=300)
    def _get_calendar(self) -> Calendar:
        """
        Fetches the calendar from the configured url and returns a Calendar object.

        This method caches the result for 5 minutes to avoid re-downloading the calendar too much.
        """
        if self.config.url:
            result = requests.get(self.config.url)
            result.raise_for_status()

            return Calendar.from_ical(result.text)

        return Calendar()

    def _get_event_name(self, event: Event) -> str | None:
        """
        Returns the name of the event via the SUMMARY key.

        Generally only used for debugging purposes.
        """
        if "SUMMARY" in event:
            return str(event["SUMMARY"])

    def _should_ignore_event(self, event: Event) -> bool:
        """
        Checks if the event should be ignored based on the config.
        """
        # Check if the event matches any of the ignore rules.
        for dict_of_rules in self.config.ignore_events_matching_any_of_all:
            if all(key in event and str(event[key]) == str(value) for key, value in dict_of_rules.items()):
                log.debug(f"Ignoring event {self._get_event_name(event)!r} due to ignore rule.")
                return True

        return False

    def _get_now(self) -> datetime:
        """
        Returns the current time in the local timezone.
        """
        return datetime.now(get_localzone())

    def _get_events_going_on_now(self) -> list[Event]:
        """
        Iterates through the events in the calendar and returns a list of events that are happening now,
        but aren't ignored by the ignore rules.
        """
        now = self._get_now()

        events = []
        for e in recurring_ical_events.of(self._get_calendar()).between(now, now):
            if self._should_ignore_event(e):
                continue

            events.append(e)
            log.debug(f"Current event: {self._get_event_name(e)!r}")

        return events

    def _in_event_now(self) -> bool:
        """
        Checks if the user is in a event (according to their calendar) right now.
        """
        return bool(self._get_events_going_on_now())

    def get_status(self) -> Status:
        """
        Get the current status of the user from the iCal URL.
        """
        if self.config.url:
            if self._in_event_now():
                log.debug("According to our calendar, we're in a event.")
                return Status.Busy

            log.debug("According to our calendar, we're not in a event.")
            return Status.Available

        # No ical url was given.. we have no idea.
        log.debug("No idea what the status is since no ical url was given.")
        return Status.Unknown
