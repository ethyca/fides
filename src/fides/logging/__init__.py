import os
import sys

import structlog

logger = structlog.get_logger()

shared_processors = [
    # Processors that have nothing to do with output,
    # e.g., add timestamps or log level names
    structlog.processors.add_log_level,
    structlog.processors.TimeStamper(fmt="iso"),
    # If the "stack_info" key in the event dict is true, remove it and
    # render the current stack trace in the "stack" key.
    structlog.processors.StackInfoRenderer(),
    # If the "exc_info" key in the event dict is either true or a
    # sys.exc_info() tuple, remove "exc_info" and render the exception
    # with traceback into the "exception" key.
    structlog.processors.format_exc_info,
    # If some value is in bytes, decode it to a unicode str.
    structlog.processors.UnicodeDecoder(),
    # Add callsite parameters.
    structlog.processors.CallsiteParameterAdder(
        {
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.FUNC_NAME,
            structlog.processors.CallsiteParameter.LINENO,
        }
    ),
]

# if sys.stderr.isatty():
if os.getenv("FIDES__DEV_MODE"):
    # Pretty printing when we run in a terminal session.
    # Automatically prints pretty tracebacks when "rich" is installed
    processors = shared_processors + [
        structlog.dev.ConsoleRenderer(),
    ]
else:
    # Print JSON when we run, e.g., in a Docker container.
    # Also print structured tracebacks.
    processors = shared_processors + [
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer(),
    ]
structlog.configure(processors)

# Obfuscate secrets in logs
