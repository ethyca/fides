import importlib
import os
import os.path

# path to the current directory
directory = os.path.dirname(__file__)

# loop through the files in the SaaS fixtures directory
for filename in os.listdir(directory):
    # ignore non-Python files and the __init__.py file
    if filename.endswith(".py") and filename != "__init__.py":
        # import the module
        module = importlib.import_module(f"{__name__}.{filename[:-3]}")

        # add the fixtures to the global context
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if callable(attr):
                globals()[attr_name] = attr
