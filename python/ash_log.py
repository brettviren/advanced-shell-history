#!/usr/bin/python
"""
  Copyright 2012 Carl Anderson

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

  This module logs a command into a command history database, while also
  gathering system-specific metadata.
"""

__author__ = 'Carl Anderson (carl.anderson@gmail.com)'


import argparse
import os
import sys


# NOTE: This variable is set automatically by the Makefile.
ASH_VERSION = '0.2.r113'


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
    self.add_argument('-V', '--version', action='version', version=ASH_VERSION,
                      help='prints the version and exits')

    self.flags = self.parse_args().__dict__
    self.__dict__.update(self.flags)


class Config(object):
  def __init__(self):
    cfg = os.getenv('ASH_CFG')
    if not cfg:
      print 'TODO(cpa): ASH_CFG environment variable is not set.'
      sys.exit(1)
    if not os.path.exists(cfg):
      print 'TODO(cpa): config file not accessible or does not exist.'
      sys.exit(1)
    if not os.access(cfg, os.R_OK):
      print 'TODO(cpa): config file is not readable.'
      sys.exit(1)
    self.filename = cfg
    with open(cfg) as fd:
      lines = [ln[8:] for ln in fd.readlines() if ln.startswith('ASH_CFG_')]
    self.variables = {}
    for line in lines:
      key, val = line.split('=', 1)
      self.variables[key.upper().strip()] = val.split(val[0], 2)[1]

  def GetBool(self, variable):
    if self.Sets(variable):
      return 'true' == self.variables[variable.upper().strip()].lower().strip()
    # TODO(cpa): log an error or warning here?
    return None

  def Sets(self, variable):
    return variable and variable.upper().strip() in self.variables

def main(argv):
  # If ASH_DISABLED is set, we want to skip everything and exit without error.
  if os.getenv('ASH_DISABLED'): return 0

  # Get the session id from the environment, if set.
  session_id = os.getenv('ASH_SESSION_ID')

  # Load the config file.
  config = Config()

  # TODO(cpa): if logging.debugging, log the entire command
  flags = Flags()

  if flags.alert:
    print >> sys.stderr, flags.alert

  # TODO(cpa): get the DB filename from config.
  if flags.get_session_id:
    print 'you want the session ID'
    if session_id is None:
      print 'Need to insert one and return the new rowid value'
      # TODO(cpa): try to insert a new session and get the new session ID
    # TODO(cpa): print the session ID number

  # Insert a new command into the database, if one was supplied.
  command_flag_used = bool(flags.command
    or flags.command_exit
    or flags.command_pipe_status
    or flags.command_start
    or flags.command_finish
    or flags.command_number)
  if command_flag_used:
    print 'You want to enter a new command into the DB.'
    # TODO(cpa): insert the command into the database.

  # End the current session.
  if flags.end_session:
    print 'you want to end this session.'
    # TODO(cpa): execute the 'close session' query

  # Return the desired exit code.
  return flags.exit


if __name__ == '__main__':
  sys.exit(main())
