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
__version__ = '0.3.r119'


import argparse
import logging
import sqlite3
import sys


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
  session_id = os.getenv('ASH_SESSION_ID') or 'NEW'
  config = Config()
  level = config.GetString('LOG_LEVEL') or 'INFO'
  level = hasattr(logging, level) and getattr(logging, level) or logging.DEBUG
  format = '%(asctime)sSESSION ' + session_id + ': %(levelname)s: %(message)s'
  kwargs = {
    'datefmt': config.GetString('LOG_DATE_FMT'),
    'filename': config.GetString('LOG_FILE'),
    'format': format,
    'level': level,
  }
  logging.basicConfig(**kwargs)


