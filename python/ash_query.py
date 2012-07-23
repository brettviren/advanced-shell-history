#!/usr/bin/python
#
# Copyright 2012 Carl Anderson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""A script to query command history from a sqlite3 database.

This script fetches data from a command history database, using one of several
user-generated queries.
"""

__author__ = 'Carl Anderson (carl.anderson@gmail.com)'

# NOTE: This variable is set automatically by the Makefile.
__version__ = '0.3.r125'


import os
import sys

# Allow the local advanced_shell_history library to be imported.
_LIB = '/usr/local/lib/advanced_shell_history'
if _LIB not in sys.path:
  sys.path.append(_LIB)

from advanced_shell_history import util


class Flags(util.Flags):
  """A class to manage all the flags for the command logger."""

  arguments = (
    ('d', 'database', 'DB', str, 'a history database to query'),
    ('f', 'format', 'FMT', str, 'a format to display results'),
    ('p', 'print_query', 'NAME', str, 'print the query SQL'),
    ('q', 'query', 'NAME', str, 'the name of the saved query to execute'),
  )

  flags = (
    ('F', 'list_formats', 'display all available formats'),
    ('H', 'hide_headings', 'hide column headings from query results'),
    ('Q', 'list_queries', 'display all saved queries'),
  )

  def __init__(self):
    """Initialize the Flags."""
    util.Flags.__init__(self, Flags.arguments, Flags.flags)


Config = util.Config


def Execute(sql):
  # TODO(cpa): expand all inlined variables and execute the query.
  return 0


def main(argv):
  # If ASH_DISABLED is set, we skip everything and exit without error.
  if os.getenv('ASH_DISABLED'): return 0

  # Setup.
  util.InitLogging()

  # Print an alert if one was specified.
  flags = Flags()

  # If no arguments were given, it may be best to show --help.
  if len(argv) == 1:
    config = Config()
    if config.Sets('DEFAULT_QUERY'):
      return Execute(config.GetString('DEFAULT_QUERY'))
    if not config.GetBool('HIDE_USAGE_FOR_NO_ARGS'):
      flags.print_help()

  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv))

