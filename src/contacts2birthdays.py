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

    for bday in contact.contents.get("bday", []):
        bday_date = datetime.strptime(bday.value, "%Y-%m-%d")  # type: ignore

        age_str = ""
        if str(bday_date.year) not in bday.params.get("X-APPLE-OMIT-YEAR", []):  # type: ignore
            age_str = f", {bday_date.year} (!{bday_date.year}!)"

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

    # pylint: disable=duplicate-code

    print(f"=== {section_name} ===")
    print(f"URL: {url}")
    print(f"PAL: {pal}")
    print(f"Name: {name}")
    print(f"Shorthand: {shorthand}")

    if url is None or pal is None or name is None or shorthand is None:
        print("Malformed, skipping")
        return

    response = Util.get_url(url)
    if response is None:
        return

    pal_path = Util.get_pal_file(pal)

    if not Util.does_file_need_update(pal_path, response):
        print("Source vcard is not newer than pal file")
        return

    counter = 0

    with open(pal_path, "w", encoding="utf-8") as pal_file:
        pal_file.write(f"{shorthand} {name}\n")

        vcard = vcard_read(response.text)
        while (contact := next(vcard, None)) is not None:
            counter += _convert_contact(pal_file, contact)

    print(f"{counter} birthday(s) converted")


def convert_contacts_to_birthdays() -> None:
    """! Converts CardDAV contacts to birthdays.

    Contacts are defined in our contacts.conf config file, and each contact file is downloaded to have
    all contact birthday dates extracted and converted into a pal event file listing the birthdays.
    """
    config = Util.get_config("contacts.conf")
    if config is None:
        print("No contacts.conf exists, skipping converting contacts to birthdays")
        return

    for section in config.sections():
        _convert_contacts(config[section], section)
