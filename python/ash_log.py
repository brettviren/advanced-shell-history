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
import sys


ASH_VERSION = 'TODO(cpa): set the version and revision numbers'


class Flags(argparse.ArgumentParser):
  """A class to manage all the flags for the command logger."""

  arguments = (
    ('a', 'alert', 'MSG', 'a message to display to the user'),
    ('c', 'command', 'CMD', 'a command to log'),
    ('e', 'command_exit', 'CODE', 'the exit code of the command to log'),
    ('p', 'command_pipe_status', 'CSV', 'the pipe states of the command to log'),
    ('s', 'command_start', 'TS', 'the timestamp when the command started'),
    ('f', 'command_finish', 'TS', 'the timestamp when the command stopped'),
    ('n', 'command_number', 'NUM', 'the builtin shell history command number'),
    ('x', 'exit', 'CODE', 'the exit code to use when exiting'),
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
    for short_flag, long_flag, metavar, help_text in Flags.arguments:
      self.add_argument('-' + short_flag, '--' + long_flag, metavar=metavar,
                        help=help_text)

    # Add the standard no-argument-taking flags.
    for short_flag, long_flag, help_text in Flags.flags:
      self.add_argument('-' + short_flag, '--' + long_flag, action='store_true',
                        help=help_text)

    # Add a flag to display the version and exit.
    self.add_argument('-V', '--version', action='version', version=ASH_VERSION,
                      help='prints the version and exits')

    self.FLAGS = self.parse_args()


def main(argv):
  flags = Flags()


if __name__ == '__main__':
  main(sys.argv)
