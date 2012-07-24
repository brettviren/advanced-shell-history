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
user-defined queries.

TOOD(cpa): add logging to this at some point.
"""

__author__ = 'Carl Anderson (carl.anderson@gmail.com)'

# NOTE: This variable is set automatically by the Makefile.
__version__ = '0.3.r127'


import os
import sys

# Allow the local advanced_shell_history library to be imported.
_LIB = '/usr/local/lib'
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


class Queries(object):
  """A class to store all the queries available to ash_query.py."""

  queries = []
  show_headings = True

  @classmethod
  def Init(cls):
    if Queries.queries: return

    # Load the queries from /etc/ash/queries and ~/.ash/queries
    data = []
    for filename in ('/etc/ash/queries', os.getenv('HOME') + '/.ash/queries'):
      if not os.path.exists(filename): continue
      lines = [x for x in open(filename).readlines() if x and x[0] != '#']
      data.extend([x[:-1] for x in lines if x[:-1]])

    queries = {}  # {name: (description, sql)}
    # TODO(cpa): parse the loaded config files

    # Append each query to a list in sorted order.
    for query in sorted(queries.items()):
      cls.queries.append((query))

  @classmethod
  def Get(cls, query_name):
    queries = [x for x in cls.queries if x[0] == query_name]
    return queries and queries[0] or None

  @classmethod
  def PrintQueries(cls):
    if not cls.queries: return
    if cls.show_headings:
      print 'query', 'description'
    for query, description, _ in Queries.queries:
      print query, description


class Formatter(object):
  """A base class for an object that formats query results into a stream."""
  formatters = []
  show_headings = True

  def __init__(self, name, desc):
    Formatter.formatters.append(self)
    self.name = name
    self.desc = desc

  @classmethod
  def PrintTypes(cls):
    if not cls.formatters: return
    if cls.show_headings:
      print 'Format', 'Description'
    for formatter, description in [(x.name, x.desc) for x in cls.formatters]:
      print formatter, description


def InitFormatters():
  # TODO(cpa): create an instance of each type of formatter
  pass


def main(argv):
  # Setup.
  util.InitLogging()

  # Print an alert if one was specified.
  flags = Flags()

  # If no arguments were given, it may be best to show --help.>>
  if len(argv) == 1:
    config = util.Config()
    if config.Sets('DEFAULT_QUERY'):
      flags.query = config.GetString('DEFAULT_QUERY')
    elif not config.GetBool('HIDE_USAGE_FOR_NO_ARGS'):
      flags.PrintHelp()

  # Initialize the formatters that will display the results of the query.
  InitFormatters()
  Formatter.show_headings = not flags.hide_headings
  if flags.list_formats:
    Formatter.PrintTypes()
    return 0

  # Read the queries from the config files.
  Queries.Init()
  Queries.show_headings = not flags.hide_headings
  if flags.list_queries:
    Queries.PrintQueries()

  elif flags.print_query:
    query = Queries.Get(flags.print_query)
    if not query:
      print >> sys.stderr, 'Query not found: %s' % flags.print_query
      return 1
    print query[2]

  elif flags.query:
    query = Queries.Get(flags.query)
    # TODO(cpa): get the query to execute and execute it
    # TODO(cpa): pass the result set to the formatter
    print 'you want to execute query named: %s' % flags.query

  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv))

