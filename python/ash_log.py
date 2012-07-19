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
"""A module to log commands and shell session details into a sqlite3 database.

This module logs a command into a command history database, while also gathering
system-specific metadata.
"""

__author__ = 'Carl Anderson (carl.anderson@gmail.com)'

# NOTE: This variable is set automatically by the Makefile.
__version__ = '0.2.r115'


import argparse
import logging
import os
import sqlite3
import sys
import unix


# TODO(cpa): change the base class from ArgumentParser to object.
class Flags(argparse.ArgumentParser):
  """A class to manage all the flags for the command logger."""

  arguments = (
    ('a', 'alert', 'MSG', str, 'a message to display to the user'),
    ('c', 'command', 'CMD', str, 'a command to log'),
    ('e', 'command_exit', 'CODE', int, 'the exit code of the command to log'),
    ('p', 'command_pipe_status', 'CSV', str, 'the pipe states of the command to log'),
    ('s', 'command_start', 'TS', int, 'the timestamp when the command started'),
    ('f', 'command_finish', 'TS', int, 'the timestamp when the command stopped'),
    ('n', 'command_number', 'NUM', int, 'the builtin shell history command number'),
    ('x', 'exit', 'CODE', int, 'the exit code to use when exiting'),
  )

  flags = (
    ('S', 'get_session_id', 'emits the session ID (or creates one)'),
    ('E', 'end_session', 'ends the current session'),
  )

  class Formatter(argparse.HelpFormatter):
    """A simple formatter whith a slightly wider set of flag names."""
    def __init__(self, prog):
      argparse.HelpFormatter.__init__(self, prog, max_help_position=44)

  def __init__(self):
    """Initialize the Flags."""
    argparse.ArgumentParser.__init__(self, formatter_class=Flags.Formatter)

    # Add the standard argument-taking flags.
    for short_flag, long_flag, metavar, arg_type, help_text in Flags.arguments:
      self.add_argument('-' + short_flag, '--' + long_flag, metavar=metavar,
                        type=arg_type, help=help_text)

    # Add the standard no-argument-taking flags.
    for short_flag, long_flag, help_text in Flags.flags:
      self.add_argument('-' + short_flag, '--' + long_flag, action='store_true',
                        help=help_text)

    # Add a flag to display the version and exit.
    self.add_argument('-V', '--version', action='version', version=__version__,
                      help='prints the version and exits')

    self.flags = self.parse_args().__dict__
    self.__dict__.update(self.flags)


class Config(object):
  """A class to manage the configuration environment variables.

  All environment variables beginning with the prefix 'ASH_CFG_' are loaded
  and made accessible conveniently through an instance of this class.

  For example:
    ASH_CFG_HISTORY_DB='/foo/' becomes { 'HISTORY_DB': '/foo/' }
  """

  def __init__(self):
    """Initialize a Config instance, reading os.environ for variables."""
    # Select all the environment variables starting with 'ASH_CFG_' and strip
    # off the leading ASH_CFG_ portion to use as the name of the variable.
    self.variables = dict(
      [(x[8:], y) for x, y in os.environ.iteritems() if x.startswith('ASH_CFG_')]
    )

  def GetBool(self, variable):
    """Returns a bool value for a config variable, or None if not set."""
    value = self.GetString(variable)
    return value and value.strip() == 'true'

  def GetString(self, variable):
    """Returns a string value for a config variable, or None if not set."""
    if self.Sets(variable):
      return self.variables[variable.upper().strip()]

  def Sets(self, variable):
    """Returns true when the argument variable exists in the environment."""
    return variable and variable.upper().strip() in self.variables


def InitLogging():
  """Initializes the logging module.

  Uses the following shell environment variables to configure the logger:
    ASH_CFG_LOG_DATE_FMT - to format the date strings in the log file.
    ASH_CFG_LOG_LEVEL - to set the logging level (DEBUG, INFO, etc).
    ASH_CFG_LOG_FILE - the filename where the logger will write.
    ASH_SESSION_ID - the session id to include in the logged output.

  Lines are written in roughly this format:
    2012-07-17 23:59:59 PDT: SESSION 123: DEBUG: argv = "[0]='ls'"
  """
  config = Config()
  level = config.GetString('LOG_LEVEL')
  level = hasattr(logging, level) and getattr(logging, level) or logging.DEBUG
  session_id = os.getenv('ASH_SESSION_ID')
  format = '%(asctime)sSESSION ' + session_id + ': %(levelname)s: %(message)s'
  kwargs = {
    'datefmt': config.GetString('LOG_DATE_FMT'),
    'filename': config.GetString('LOG_FILE'),
    'format': format,
    'level': level,
  }
  logging.basicConfig(**kwargs)


class Database(object):
  """A wrapper around a database connection."""

  class Object(object):
    """A construct for objects to be inserted into the Database."""
    def __init__(self, table_name):
      self.values = {}
      self.table_name = table_name
      sql = '''
        select sql
        from sqlite_master
        where
          type = 'table'
          and name = ?;
      '''
      # Check that the table exists, creating it if not.
      with Database().cursor as cur:
        cur.execute(sql, (table_name,))
        rs = cur.fetchone()
        if not rs:
          cur.execute(self.GetCreateTableSql())
        elif rs[0] != self.GetCreateTableSql():
          logging.warning('Table %s exists, but has an unexpected schema.' % table_name)

    def Insert(self):
      """Insert the object into the database, returning the new rowid."""
      sql = 'INSERT INTO %s ( %s ) VALUES ( %s )' % (
        self.table_name,
        ', '.join(self.values),
        ', '.join(['?' for _ in self.values])
      )
      with Database().cursor as cur:
        cur.execute(sql, tuple(self.values.values()))
        return cur.lastrowid
      return 0

  def __init__(self):
    """Initialize a Database with an open connection to the history database."""
    db_filename = Config().GetString('HISTORY_DB')
    # TODO(cpa): test that the file exists and is readable.
    # TODO(cpa): create the database if it does not exist yet.
    self.connection = sqlite3.connect(db_filename)
    self.cursor = self.connection.cursor()


class Session(Database.Object):
  """An abstraction of a shell session to store to the history database."""

  def __init__(self):
    """Initialize a Session, populating session values."""
    Database.Object.__init__(self, 'sessions')
    self.values = {
      'time_zone': unix.GetTimeZone(),
      'start_time': unix.GetTime(),
      'ppid': unix.GetPPID(),
      'pid': unix.GetPID(),
      'tty': unix.GetTTY(),
      'uid': unix.GetUID(),
      'euid': unix.GetEUID(),
      'logname': unix.GetLoginName(),
      'hostname': unix.GetHostName(),
      'host_ip': unix.GetHostIP(),
      'shell': unix.GetShell(),
      'sudo_user': unix.GetEnv('SUDO_USER'),
      'sudo_uid': unix.GetEnv('SUDO_UID'),
      'ssh_client': unix.GetEnv('SSH_CLIENT'),
      'ssh_connection': unix.GetEnv('SSH_CONNECTION')
    }

  def Close(self):
    """Closes this session in the database."""
    sql = '''
      UPDATE sessions
      SET
        end_time = ?,
        duration = ? - start_time
      WHERE id == ?;
    '''
    with Database().cursor as cur:
      ts = unix.GetTime()
      cur.execute(sql, (ts, ts, unix.GetEnvInt('ASH_SESSION_ID'),))


class Command(Database.Object):
  """An abstraction of a command to store to the history database."""
  def __init__(self, command, rval, start, finish, number, pipes):
    Database.Object.__init__(self, 'commands')
    self.values = {
      'session_id': unix.GetEnvInt('ASH_SESSION_ID'),
      'shell_level': unix.GetEnvInt('SHLVL'),
      'command_no': number,
      'tty': unix.GetTTY(),
      'euid': unix.GetEUID(),
      'cwd': unix.GetCWD(),
      'rval': rval,
      'start_time': start,
      'end_time': finish,
      'duration': finish - start,
      'pipe_cnt': len(pipes.split('_')),
      'pipe_vals': pipes,
      'command': command
    }
    # If the user changed directories, CWD will be the new directory, not the
    # one where the command was actually entered.
    if rval == 0 and (command == 'cd' or command.startswith('cd ')):
      self.values['cwd'] = unix.GetEnv('OLDPWD')


def main(argv):
  # If ASH_DISABLED is set, we skip everything and exit without error.
  if os.getenv('ASH_DISABLED'): return 0

  # Setup.
  InitLogging()

  # Log the command, if debug logging is enabled.
  if logging.getLogger().isEnabledFor(logging.DEBUG):
    command = []
    for arg in argv:
      command.append('[%d]=\'%s\'' % (len(command), arg))
    logging.debug('argv = "' + ','.join(command) + '"')

  # Print an alert if one was specified.
  flags = Flags()
  if flags.alert:
    print >> sys.stderr, flags.alert

  # Create the session id, if not already set in the environment.
  session_id = os.getenv('ASH_SESSION_ID')
  if flags.get_session_id:
    if session_id is None:
      session_id = Session().Insert()
    print session_id

  # Insert a new command into the database, if one was supplied.
  command_flag_used = bool(flags.command
    or flags.command_exit
    or flags.command_pipe_status
    or flags.command_start
    or flags.command_finish
    or flags.command_number)
  if command_flag_used:
    Command(
      flags.command, flags.command_exit, flags.command_start,
      flags.command_finish, flags.command_number, flags.command_pipe_status
    ).Insert()

  # End the current session.
  if flags.end_session:
    Session().Close()

  # Return the desired exit code.
  return flags.exit


if __name__ == '__main__':
  sys.exit(main(sys.argv))
