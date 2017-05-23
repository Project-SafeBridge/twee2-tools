"""Generic utility functions."""

import os
import errno
import re

# Natural string sorting

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    """Used for sorting in natural order.
    From http://nedbatchelder.com/blog/200712/human_sorting.html
    """
    return [atoi(c) for c in re.split('(\d+)', repr(text))]

# File operations

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def load_file(file_path):
    """Loads the file at the specified path as a list of strings.

    Returns:
        A list of strings, each holding one line. Lines have their \n newline
        characters stripped already.
    """
    with open(file_path) as f:
        lines = [line.rstrip('\n') for line in f]
    return lines

