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
"""A helper library to expose Unix system information."""

import os
import sys
import time


def GetCWD():
  # TODO(cpa): return the current working directory.
  return 'TODO(cpa): CWD'


def GetEnv(variable):
  # TODO(cpa): return the environment variable value
  return None


def GetEUID():
  # TODO(cpa): return the EUID of the command
  return 0


def GetHostIp():
  # TODO(cpa): return the host ips
  return 'TODO(cpa): host ip'


def GetHostName():
  # TODO(cpa): return the hostname
  return 'TODO(cpa): hostname'


def GetLoginName():
  # TODO(cpa): return the user login name
  return 'TODO(cpa): user login name'


def GetPID():
  # TODO(cpa): return the PID of the command
  return 0


def GetPPID():
  # TODO(cpa): return the PPID of the command
  return 0


def GetShell():
  # TODO(cpa): return the name of the shell (zsh or bash)
  return 'TODO(cpa): bash or zsh'


def GetTime():
  # TODO(cpa): return the epoch time
  return 0


def GetTimeZone():
  # TODO(cpa): return the local time zone string.
  return 'GMT'


def GetTTY():
  # TODO(cpa): return the name of the current tty
  return 'TODO(cpa): the shell tty'


def GetUID():
  # TODO(cpa): return the UID of the command
  return 0

