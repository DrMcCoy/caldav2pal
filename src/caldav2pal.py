"""! Main entry point for caldav2pal.
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

import argparse
from argparse import RawTextHelpFormatter

from calendars2events import convert_calendars_to_events
from contacts2birthdays import convert_contacts_to_birthdays
from util import Util


def _parse_args() -> argparse.Namespace:
    """! Parse command line arguments.

    @return An object containing the parsed command line arguments.
    """
    info = Util.get_project_info()
    nameversion = f"{info['name']} {info['version']}"
    description = f"{nameversion} -- {info['summary']}"
    version = (f"{nameversion}\n"
               f"{info['url']['homepage']}\n\n"
               f"Copyright (c) {info['years']} {', '.join(info['authors'])}\n\n"
               "This is free software; see the source for copying conditions.  There is NO\n"
               "warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.")

    parser = argparse.ArgumentParser(description=description, formatter_class=RawTextHelpFormatter)

    parser.add_argument("-v", "--version", action="version",
                        version=version,
                        help="print the version and exit")

    return parser.parse_args()


def main() -> None:
    """! caldav2pal main function.
    """
    _parse_args()

    convert_contacts_to_birthdays()
    convert_calendars_to_events()


if __name__ == '__main__':
    main()
