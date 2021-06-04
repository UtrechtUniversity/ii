import os
import psutil
import sys

"""This file contains generic (non-iRODS-related) utility functions"""


def exit_with_error(message, errorcode=1):
    """Exits with error message"""
    print_error(message)
    exit(errorcode)


def print_error(message):
    """Prints error message"""
    _print_stderr("ERROR: {}".format(message))


def print_warning(message):
    """Prints warning message"""
    _print_stderr("WARNING: {}".format(message))


def print_debug(message):
    """Prints debug message"""
    _print_stderr("DEBUG: {}".format(message))


def get_ppid():
    """Returns the parent process ID (PPID)."""
    # This should be more portable than using os.get_ppid directly
    return psutil.Process(os.getpid()).ppid()


def _print_stderr(message):
    print(message, file=sys.stderr)
