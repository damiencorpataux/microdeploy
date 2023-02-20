from .test_pinout_pinwrap import * #TestPinoutPinwrap
from .test_pinout_pinout import *

# Regex for matching exception message:
# - in python:      TypeError: missing 1 required positional argument: 'pinmap' (rationale for or: r'message from micropython|message from python')
# - in micropython: TypeError: takes 2 positional arguments but 1 were given
re_for_exception_function_missing_required_arguments = r'takes \d positional argument(s?) but \d were given|missing \d required positional argument'