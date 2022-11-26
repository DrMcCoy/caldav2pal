"""! Converting CalDAV calendars to events.
"""

# caldav2pal - A FLOSS utility to convert CalDAV/CardDAV to pal
# Copyright (c) 2022 Sven "DrMcCoy" Hesse <drmccoy@drmccoy.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from configparser import SectionProxy
from datetime import date, datetime, timedelta
from typing import TextIO

import icalendar  # type: ignore
import recurring_ical_events  # type: ignore

from util import Util


def _is_all_day(event: icalendar.cal.Event) -> bool:
    """! Is this an all-day event?
    """

    # An all-day event stores the start and end timestamp as a datetime.date object, while other
    # events use datetime.datetime. So we need to distinguish between datetime and date here.
    # But since datetime inherits from date, we can't use use isinstance(..., date): that would
    # evaluate to true for datetime as well.
    #
    # pylint: disable=unidiomatic-typecheck
    return type(event["DTSTART"].dt) is date and type(event["DTEND"].dt) is date


def _is_multiple_days(event) -> bool:
    """! Does this event run over multiple days?
    """
    return _get_start_datetime(event).date() != _get_end_datetime(event).date()


def _get_start_datetime(event: icalendar.cal.Event) -> datetime:
    """! Return the event's start datetime in the local timezone.
    """

    # Expand date to datetime, by appending 00:00:00. See above for the unidiomatic-typecheck.
    #
    # pylint: disable=unidiomatic-typecheck
    if type(event["DTSTART"].dt) is date:
        return datetime.combine(event["DTSTART"].dt, datetime.min.time()).astimezone()

    return event["DTSTART"].dt.astimezone()


def _get_end_datetime(event: icalendar.cal.Event) -> datetime:
    """! Return the event's end datetime in the local timezone.
    """

    # If this is an all-day event, the end timestamp is stored as a date, and in that case, the
    # end date is *exclusive*. So to expand such a date into a datetime, append 00:00:00 and
    # subtract a single second, so that the datetime is inclusive again. See above for that
    # unidiomatic-typecheck.
    #
    # pylint: disable=unidiomatic-typecheck
    if type(event["DTEND"].dt) is date:
        end_datetime = datetime.combine(event["DTEND"].dt, datetime.min.time()).astimezone()
        end_datetime -= timedelta(seconds=1)
    else:
        end_datetime = event["DTEND"].dt.astimezone()

    # Make sure the end is never before the start
    start_datetime = _get_start_datetime(event)
    end_datetime = start_datetime if start_datetime > end_datetime else end_datetime

    return end_datetime


def _convert_event(pal_file: TextIO, event: icalendar.cal.Event) -> None:
    """! Converts one calendar event into a pal event line

    @param pal_file  The pal event file to write into.
    @param event     The event to convert.
    """

    # Name of the event. Add a placeholder text if empty
    name = event["SUMMARY"]
    if name is None or name.isspace() or len(name) == 0:
        name = "[Event without title]"

    # Get start and end, and split them into date and time

    start_datetime = _get_start_datetime(event)
    end_datetime = _get_end_datetime(event)

    start_date = str(start_datetime).replace('-', '')[:8]
    end_date = str(end_datetime).replace('-', '')[:8]

    start_time = str(start_datetime).replace('-', '')[9:14]
    end_time = str(end_datetime).replace('-', '')[9:14]

    if _is_all_day(event):
        if _is_multiple_days(event):
            # An all-day event that goes over multiple days
            pal_file.write(f"DAILY:{start_date}:{end_date} {name}\n")
        else:
            # An all-day event that occurs for a single day
            pal_file.write(f"{start_date} {name}\n")
    else:
        if _is_multiple_days(event):
            # An event with a start time that goes beyond the end of the day
            pal_file.write(f"{start_date} [{start_time}] {name}\n")
        else:
            # An event which starts and ends in the same day
            pal_file.write(f"{start_date} [{start_time}-{end_time}] {name}\n")


def _convert_calendar(calendar: SectionProxy, section_name: str) -> None:
    """! Converts one CalDAV calendar file to pal events.

    @param calendar      The config file section we're looking at.
    @param section_name  The name of the config file section.
    """
    url = calendar.get("url", None)
    pal = calendar.get("pal", None)
    name = calendar.get("name", None)
    shorthand = calendar.get("shorthand", None)

    print(f"=== {section_name} ===")
    print(f"URL: {url}")
    print(f"PAL: {pal}")
    print(f"Name: {name}")
    print(f"Shorthand: {shorthand}")

    # Section is similar to contacts2birthdays.py, but not a good candidate to unify
    # pylint: disable=duplicate-code

    # Make sure we have all the data we need
    if url is None or pal is None or name is None or shorthand is None:
        print("Malformed, skipping")
        return

    # Try to download the calendar. If it fails, bail
    response = Util.get_url(url)
    if response is None:
        return

    pal_path = Util.get_pal_file(pal)

    # A calendar needs updating if the URL is newer or the file is older than 180 days
    if not Util.does_file_need_update(pal_path, response, timedelta(days=180)):
        print("Source ics is not newer than pal file")
        return

    # We expand recurring events one year into the past and one year into the future. To
    # make sure future events don't "run out", the update-check above triggers on 180 days.
    start_date = datetime.now() - timedelta(days=365)
    end_date = datetime.now() + timedelta(days=365)

    counter = 0

    with open(pal_path, "w", encoding="utf-8") as pal_file:
        pal_file.write(f"{shorthand} {name}\n")

        # Read and expand the events, then convert them all in sequence

        ical = icalendar.Calendar.from_ical(response.text)
        events = recurring_ical_events.of(ical).between(start_date, end_date)

        for event in events:
            _convert_event(pal_file, event)
            counter = counter + 1

    print(f"{counter} event(s) converted")


def convert_calendars_to_events() -> None:
    """! Converts CalDAV calendars to events.

    Calendars are defined in our caldendars.conf config file, and each calendar file is downloaded to have
    all event extracted and converted into a pal event file.
    """
    config = Util.get_config("calendars.conf")
    if config is None:
        print("No calendars.conf exists, skipping converting calendars to events")
        return

    # Run through all the sections in the config file
    for section in config.sections():
        _convert_calendar(config[section], section)
