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

import email.utils
import urllib
from base64 import b64encode
from configparser import ConfigParser
from datetime import datetime, timedelta
from importlib import metadata
from os import path
from pathlib import Path
from typing import Any

import requests
from dateutil.parser import parse as parsedate
from xdg import xdg_config_home

PACKAGE_NAME = "caldav2pal"
COPYRIGHT_YEARS = "2022"


class Util:
    """! Utility functions.
    """

    @staticmethod
    def get_project_info() -> dict[str, Any]:
        """! Get project metadata information.

        @return A dict containing project metadata information.
        """
        project_metadata = metadata.metadata(PACKAGE_NAME)

        info = {}  # type: dict[str, Any]
        info["name"] = project_metadata["Name"]
        info["version"] = project_metadata["Version"]
        info["summary"] = project_metadata["Summary"]
        info["years"] = COPYRIGHT_YEARS

        # Project URLs are stored with the "type" information pasted in front
        info["url"] = {}
        for i in project_metadata.get_all("Project-URL"):
            parsed = i.split(", ", 1)
            info["url"][parsed[0]] = parsed[1]

        # Authors are stored in an email address format, pasted together into one string
        info["authors"] = []
        for address in project_metadata["Author-email"].split(", "):
            parsed = email.utils.parseaddr(address)
            info["authors"].append(f"{parsed[0]} <{parsed[1]}>")

        return info

    @staticmethod
    def _basic_auth(username: str, password: str) -> str:
        """! Convert a username and password into a HTTP Basic Auth token.

        @param username  The username portion of the authentification.
        @param password  The password portion of the authentification.
        @return A token to be used for HTTP Basic Auth.
        """
        token = b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        return f"Basic {token}"

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

    @staticmethod
    def get_url(url: str) -> requests.models.Response | None:
        """! Get the contents of the specified URL.

        Both HTTP and HTTPS URLs are support, as is HTTP Basic Auth.

        @param url  The URL to query.
        @return A response object or None if the request failed.
        """
        parsed_url = urllib.parse.urlparse(url)

        headers = None
        if parsed_url.username is not None and parsed_url.password is not None:
            headers = {"Authorization": Util._basic_auth(parsed_url.username, parsed_url.password)}

        try:
            response = requests.get(url, timeout=10, headers=headers)
        except Exception as err:  # pylint: disable=broad-except
            print(err)
            return None

        return response

    @staticmethod
    def does_file_need_update(
            file: Path | str,
            response: requests.models.Response,
            max_age: timedelta | None = None) -> bool:
        """! Does a file need updating when compared to an URL resource?

        This function checks the Last-Modified time of a requests response against the modifed
        timestamp of a file to see if the URL resource is newer.

        @param file      The file to check if it needs updating.
        @param response  The requests response of an URL resource.
        @param max_age   The max age of the file. If the file is older, force a True response.
        @return True of the file needs updating, False otherwise.
        """

        # File doesn't exist or no Last-Modified field in the response -> Needs updating
        if not path.exists(file) or "Last-Modified" not in response.headers:
            return True

        url_datetime = parsedate(response.headers["Last-Modified"]).astimezone()
        file_datetime = datetime.fromtimestamp(path.getmtime(file)).astimezone()

        # Last-Modified is newer than the file's modification time -> Needs updating
        if url_datetime > file_datetime:
            return True

        # File is older than its maximum age -> Needs updating
        if max_age is not None and datetime.now().astimezone() > (file_datetime + max_age):
            return True

        # File is a-okay!
        return False
