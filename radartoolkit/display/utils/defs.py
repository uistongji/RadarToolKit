

""" Various definitions, errors and constants that can be used throughout the program

"""
import sys

CONTIGUOUS = 'contiguous'  # contiguous chunking

# String formatting template for numbered dimension names
DIM_TEMPLATE = "dim-{}"
SUB_DIM_TEMPLATE = "subdim-{}"

# Use different unicode character per platform as it looks better.
if sys.platform == 'linux':
    RIGHT_ARROW = "\u2794"
elif sys.platform == 'win32' or sys.platform == 'cygwin':
    RIGHT_ARROW = "\u2794"
elif sys.platform == 'darwin':
    RIGHT_ARROW = "\u279E"
else:
    RIGHT_ARROW = "\u2794"


class InvalidInputError(Exception):
    """ Exception raised when the input is invalid after editing
    """
    pass


