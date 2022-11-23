"""! Utility functions.
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

from configparser import ConfigParser
from os import path
from pathlib import Path

from xdg import xdg_config_home

PACKAGE_NAME = "caldav2pal"


class Util:
    """! Utility functions.
    """

    @staticmethod
    def get_config_file(config: Path | str) -> Path:
        """! Get the specific config file within our config directory as a path object.

        @param config  The config filename we want.
        @return A path object with the full path of the config file.
        """
        return xdg_config_home() / PACKAGE_NAME / config

    @staticmethod
    def get_config(config: Path | str) -> ConfigParser | None:
        """! Get the specific config file within our config directory as a ConfigParser object.

        @param config  The config filename we want.
        @return A ConfigParser object if the config file exists, None otherwise.
        """
        config_file = Util.get_config_file(config)
        if not path.exists(config_file):
            return None

        config_parser = ConfigParser()
        config_parser.read(config_file)
        return config_parser

    @staticmethod
    def get_pal_file(event: Path | str) -> Path:
        """! Get the specific pal event file within the pal config directory as a path object.

        @param event  The pal event filename we want.
        @return A path object with the full path of the pal event file.
        """
        return Path(path.expanduser(Path("~/.pal/") / event))
