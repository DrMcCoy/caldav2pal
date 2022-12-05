"""! Converting CardDAV contacts to birthdays.
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
from datetime import datetime
from pathlib import Path
from typing import TextIO

from vobject import readComponents as vcard_read  # type: ignore
from vobject.base import Component as Contact

from util import Util


def _convert_contact(pal_file: TextIO, contact: Contact) -> int:
    """! Converts one CardDAV contact file to birthdays.

    @param pal_file  The pal event file to write into.
    @param contact   The vcard contact to convert.
    """
    counter = 0

    # For each contact, run through its list of birthday dates
    for bday in contact.contents.get("bday", []):
        # Parse the date
        bday_date = datetime.strptime(bday.value, "%Y-%m-%d")  # type: ignore

        # If the year does not appears in the "fake" years list to omit, use it. Otherwise, don't
        age_str = ""
        if str(bday_date.year) not in bday.params.get("X-APPLE-OMIT-YEAR", []):  # type: ignore
            # Birth year and special marker for pal to calculate the age from the birth year
            age_str = f", {bday_date.year} (!{bday_date.year}!)"

        # The birthday occurs every year on that month and day. Also add the contact name, and their age if known
        pal_file.write(f"0000{bday_date.month:02d}{bday_date.day:02d} {contact.fn.value}{age_str}\n")

        counter = counter + 1

    return counter


def _convert_contacts(contacts: SectionProxy, section_name: str) -> None:
    """! Converts one CardDAV contacts file to birthdays.

    @param contacts      The config file section we're looking at.
    @param section_name  The name of the config file section.
    """
    url = contacts.get("url", None)
    pal = contacts.get("pal", None)
    name = contacts.get("name", None)
    shorthand = contacts.get("shorthand", None)

    # Section is similar to calendars2events.py, but not a good candidate to unify
    # pylint: disable=duplicate-code

    print(f"=== {section_name} ===")
    print(f"URL: {url}")
    print(f"PAL: {pal}")
    print(f"Name: {name}")
    print(f"Shorthand: {shorthand}")

    # Make sure we have all the data we need
    if url is None or pal is None or name is None or shorthand is None:
        print("Malformed, skipping")
        return

    # Try to download the calendar. If it fails, bail
    response = Util.get_url(url)
    if response is None:
        return

    pal_path = Util.get_pal_file(pal)

    # If the pal event file is older than the URL, it needs updating
    if not Util.does_file_need_update(pal_path, response):
        print("Source vcard is not newer than pal file")
        return

    counter = 0

    with open(pal_path, "w", encoding="utf-8") as pal_file:
        pal_file.write(f"{shorthand} {name}\n")

        # Read the contacts file, then convert them all in sequence

        vcard = vcard_read(response.text)
        while (contact := next(vcard, None)) is not None:
            counter += _convert_contact(pal_file, contact)

    print(f"{counter} birthday(s) converted")


def convert_contacts_to_birthdays(config_file: str | None = None) -> None:
    """! Converts CardDAV contacts to birthdays.

    Contacts are defined in our contacts.conf config file, and each contact file is downloaded to have
    all contact birthday dates extracted and converted into a pal event file listing the birthdays.
    """
    config_path = Path(config_file) if config_file is not None else Util.get_config_file("contacts.conf")

    config = Util.open_config(config_path)
    if config is None:
        print(f"Can't open file '{config_path}', skipping converting contacts to birthdays")
        return

    # Run through all the sections in the config file
    for section in config.sections():
        _convert_contacts(config[section], section)
