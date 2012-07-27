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
__version__ = '0.3.r131'


import os
import re
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
  """A class to store all the queries available to ash_query.py.

  Queries are parsed from /etc/ash/queries and ~/.ash/queries and made available
  to the command line utility.

  TODO(cpa): if there is an error in the file, something should be printed.
  """

  queries = []
  show_headings = True
  parser = re.compile(r"""
    \s*(?P<query_name>[A-Za-z0-9_-]+)\s*:\s*{\s*
      description\s*:\s*
        (?P<description>
          "([^"]|\\")*"      # A double-quoted string.
        )\s*
      sql\s*:\s*{
        (?P<sql>
          (
            [$]{[^}]*}     | # Shell variable expressions: ${FOO} or ${BAR:-0}
            [^}]             # Everything else in the query.
          )*
        )
      }\s*
    }""", re.VERBOSE)

  @classmethod
  def Init(cls):
    if cls.queries: return

    # Load the queries from /etc/ash/queries and ~/.ash/queries
    data = []
    for filename in ('/etc/ash/queries', os.getenv('HOME') + '/.ash/queries'):
      if not os.path.exists(filename): continue
      lines = [x for x in open(filename).readlines() if x and x[0] != '#']
      data.extend([x[:-1] for x in lines if x[:-1]])

    # Parse the loaded config files.
    cls.queries = {}  # {name: (description, sql)}
    for match in cls.parser.finditer('\n'.join(data)):
      query_name = match.group('query_name')
      description = match.group('description') or '""'
      cls.queries[query_name] = (description[1:-1], match.group('sql'))

  @classmethod
  def Get(cls, query_name):
    if not query_name or not query_name in cls.queries: return (None, None)
    raw = cls.queries[query_name][1]
    sql = os.popen('/bin/cat <<EOF_ASH_SQL\n%s\nEOF_ASH_SQL' % raw).read()
    return (raw, sql)

  @classmethod
  def PrintQueries(cls):
    data = sorted([(query, desc) for query, (desc, _) in cls.queries.items()])
    data.insert(0, ['Query', 'Description'])
    AlignedFormatter.PrintRows(data)


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
    data = sorted([(x.name, x.desc) for x in cls.formatters])
    data.insert(0, ['Format', 'Description'])
    AlignedFormatter.PrintRows(data)

  @classmethod
  def Get(cls, name):
    for fmt in cls.formatters:
      if fmt.name == name:
        return fmt
    return None

  def Print(self, rs):
    """Print the result set."""
    raise NotImplemented


class AlignedFormatter(Formatter):
  @classmethod
  def PrintRows(cls, rows):
    headings = rows[0]
    widths = [0 for _ in headings]
    separator = '    '
    XX = len(separator)
    max_column_width = 80

    # Skip the headings row, if that flag was specified.
    if not Formatter.show_headings:
      rows = rows[1:]

    # Calculate the min widths of each column.
    for row in rows:
      i = 0
      for col in row:
        if col:
          widths[i]= max(widths[i], min(max_column_width, len(str(col))))
        i += 1

    # Print the result set rows aligned.
    fmt = separator.join(['%%%ds' % -width for width in widths])
    for row in rows:
      print fmt % tuple(row)
  
  def Print(self, rs):
    AlignedFormatter.PrintRows(rs)


class AutoFormatter(Formatter):
  def Print(self, rs):
    print 'TODO(cpa): print these results auto-grouped'


class CSVFormatter(Formatter):
  def Print(self, rs):
    print 'TODO(cpa): print these results csv separated'


class NullFormatter(Formatter):
  def Print(self, rs):
    print 'TODO(cpa): print these results null separated'


def InitFormatters():
  AlignedFormatter('aligned', 'Columns are aligned and separated with spaces.')
  AutoFormatter('auto', 'TODO(cpa): Automatically group redundant values.')
  CSVFormatter('csv', 'TODO(cpa): Columns are comma separated with strings quoted.')
  NullFormatter('null', 'TODO(cpa): Columns are null separated with strings quoted.')


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
    raw, sql = Queries.Get(flags.print_query)
    if not raw:
      print >> sys.stderr, 'Query not found: %s' % flags.print_query
      return 1
    if raw.strip() != sql.strip():
      print 'Query: %s\nTemplate Form:\n%s\nActual SQL:\n%s' % (
          flags.print_query, raw, sql)
    else:
      print 'Query: %s\n%s' % (flags.print_query, sql)

  elif flags.query:
    # Get the formatter to be used to print the result set.
    default = util.Config().GetString('DEFAULT_FORMAT') or 'aligned'
    format_name = flags.format or default
    fmt = Formatter.Get(format_name)
    if not fmt:
      print >> sys.stderr, 'Unknown format: %s' % format_name
      return 1

    sql = Queries.Get(flags.query)[1]
    rs = util.Database().Fetch(sql)
    fmt.Print(rs)

  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv))

