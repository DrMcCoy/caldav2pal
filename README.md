caldav2pal README
=================

caldav2pal is a free/libre and open source (FLOSS) utility to convert
[CalDAV](https://en.wikipedia.org/wiki/CalDAV)/[CardDAV](https://en.wikipedia.org/wiki/CardDAV)
to [pal](https://palcal.sourceforge.net/) event files, licensed under the
terms of the [GNU Affero General Public License version 3](https://www.gnu.org/licenses/agpl.html)
(or later).

You can find [caldav2pal here on GitHub](https://github.com/DrMcCoy/caldav2pal).


Acknowledgment
--------------

The idea of caldav2pal is based on [ical2paleventfile](https://github.com/MHohenberg/ical2paleventfile).
It seemed to be abandoned, and, due to using the ics library, didn't support
recurring events, so I just went ahead and rewrote it with icalender and
recurring_ical_events instead.


What even is this?
------------------

[pal](https://palcal.sourceforge.net/) is a small command line utility that
displays a calendar, together with upcoming events.

Unfortunately, it doesn't support CalDAV, instead requiring its own event
file format. This is where caldav2pal comes into play: it converts CalDAV
calendars into pal event files, so that you can still use pal while keeping
your calendars online on a CalDAV server.


Installation
------------

To install caldav2pal system-wide, use
```
pip install .
```

To install caldav2pal for current user only, use
```
pip install --user .
```

To install in a virtualenv, use
```
pip -m venv env
source env/bin/activate
pip install .
```


Dependencies
------------

See the `pyproject.toml` for project dependencies.


Usage
-----

At the moment, caldav2pal doesn't really offer much in terms of command line
options.

```
usage: caldav2pal [-h] [-v]

caldav2pal 0.1.0 -- A FLOSS utility to convert CalDAV/CardDAV to pal

options:
  -h, --help     show this help message and exit
  -v, --version  print the version and exit
```


Configuration
-------------

caldav2pal is currently solely controlled by its configuration files,
`calendars.conf` and `contacts.conf`. You need to create those in your
`$XDG_CONFIG_HOME/caldav2pal/` directory (if you don't have XDG_CONFIG_HOME
set, it defaults to `$HOME/.config`).

`caldendars.conf` defines CalDAV calendars that will be converted into pal
event files, one event at a time. It does support recurring events, see
below for details.

`contacts.conf` defines CardDAV contact lists, which will be searched through
for birthday dates, to be put into pal events files. Both dates with and
without specified year are supported.

The format is the same for both files: they are INI-style files. The syntax
is the following:

```
[section]   # Make sure the section name is different for every calendar. Only alphanumerical characters, no spaces!
url = [URL of the CalDAV/CardDAV file]
pal = [output pal event filename] # always in your userdir under ~/.pal
name = [name of the calendar]
shorthand = [2-character shortcode]
```

So, for example, one section might be:

```
[myCalendar]
url = http://www.example.com/myCalendar.ics
pal = mycalendar.pal
name = my personal calendar
shorthand = mc
```

You can add as many sections as you like, # for comments are supported

Currently, only URLs with the schema `http://`, `https://` and `file://` are
supported. However, for `http://` and `https://`, you can specify a username
and password for HTTP Basic Auth:
```
url = https://sven:mysecretpassword@www.example.com/myCalendar.ics
```


Running caldav2pal
------------------

Simply run caldav2pal with
```
caldav2pal
```
and it will go through your configuration files, download calendars and
contacts, and create pal event files.

Note that on successive runs, caldav2pal will check the Last-Modified field
in the response header, and only convert the file again if its newer.
See below for how that interacts with recurring event.s

You can now add the created pal event files to your `~/.pal/pal.conf`.
Simply add a line in the form of
```
file mycalendar.pal
```
for every created event file.

If everything went through fine, it is now a good time to make caldav2pal run
regularly, for example by adding a cronjob for it.


Recurring events
----------------

caldav2pal supports recurring events, by expanding them into single events.
Because events might have an unlimited duration, only events one year into
the past and one year into the future are looked at.

This means, you need to rerun caldav2pal at least once every year to be
see current events. Though it's probably best to call caldav2pal more
frequent than that.

So what about the "don't recreate calendars when nothing changed" feature
talked about above? To make these two things work together, caldav2pal
considers a file that is older than 180 days in need of update, no matter
what the CalDAV server's Last-Modified response says. That means recurring
events can be expanded into the future even if the calendar itself hasn't
changed.
