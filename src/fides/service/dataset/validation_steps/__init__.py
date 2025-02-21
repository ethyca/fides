"""
Dynamically loads all validation step modules in this directory.

This allows validation steps to be added or removed by simply adding/removing Python files,
without modifying existing code. Each .py file (except __init__.py) should contain a single
validation step.
"""

import importlib
import os
import os.path

# path to the current directory
directory = os.path.dirname(__file__)

# loop through the files in the validation directory
for filename in os.listdir(directory):
    # ignore non-Python files and the __init__.py file
    if filename.endswith(".py") and filename != "__init__.py":
        # import the module
        module = importlib.import_module(f"{__name__}.{filename[:-3]}")
