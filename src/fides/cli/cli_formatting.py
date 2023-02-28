"""
This is a configuration file for `rich_click`, used to customize the
visual aesthetic and output of the CLI.

This is the list of all documented configuration options for `rich_click`.

You can set a style attribute by adding one or more of the following words:

- "bold" or "b" for bold text.
- "blink" for text that flashes (use this one sparingly).
- "blink2" for text that flashes rapidly (not supported by most terminals).
- "conceal" for concealed text (not supported by most terminals).
- "italic" or "i" for italic text (not supported on Windows).
- "reverse" or "r" for text with foreground and background colors reversed.
- "strike" or "s" for text with a line through it.
- "underline" or "u" for underlined text.
- "underline2" or "uu" for doubly underlined text.
- "frame" for framed text.
- "encircle" for encircled text.
- "overline" or "o" for overlined text.

The list of valid colors is here:
- https://rich.readthedocs.io/en/stable/appendix/colors.html
"""

from rich_click import rich_click

# Default styles
rich_click.STYLE_OPTION = "bold #fca311"
rich_click.STYLE_SWITCH = "bold #fca311"
rich_click.STYLE_ARGUMENT = "bold #00ff5f"
rich_click.STYLE_METAVAR = "bold #8700af"
rich_click.STYLE_METAVAR_APPEND = "dim yellow"
rich_click.STYLE_METAVAR_SEPARATOR = "dim"
rich_click.STYLE_HEADER_TEXT = ""
rich_click.STYLE_FOOTER_TEXT = ""
rich_click.STYLE_USAGE = "yellow"
rich_click.STYLE_USAGE_COMMAND = "bold"
rich_click.STYLE_DEPRECATED = "red"
rich_click.STYLE_HELPTEXT_FIRST_LINE = ""
rich_click.STYLE_HELPTEXT = ""
rich_click.STYLE_OPTION_HELP = ""
rich_click.STYLE_OPTION_DEFAULT = "bold #8700af"
rich_click.STYLE_OPTION_ENVVAR = "dim yellow"
rich_click.STYLE_REQUIRED_SHORT = "red"
rich_click.STYLE_REQUIRED_LONG = "dim red"
rich_click.STYLE_OPTIONS_PANEL_BORDER = "dim"
rich_click.ALIGN_OPTIONS_PANEL = "left"
rich_click.STYLE_OPTIONS_TABLE_SHOW_LINES = False
rich_click.STYLE_OPTIONS_TABLE_LEADING = 0
rich_click.STYLE_OPTIONS_TABLE_PAD_EDGE = False
rich_click.STYLE_OPTIONS_TABLE_PADDING = (0, 1)
rich_click.STYLE_OPTIONS_TABLE_BOX = ""
rich_click.STYLE_OPTIONS_TABLE_ROW_STYLES = None
rich_click.STYLE_OPTIONS_TABLE_BORDER_STYLE = None
rich_click.STYLE_COMMANDS_PANEL_BORDER = "dim"
rich_click.ALIGN_COMMANDS_PANEL = "left"
rich_click.STYLE_COMMANDS_TABLE_SHOW_LINES = False
rich_click.STYLE_COMMANDS_TABLE_LEADING = 0
rich_click.STYLE_COMMANDS_TABLE_PAD_EDGE = False
rich_click.STYLE_COMMANDS_TABLE_PADDING = (0, 1)
rich_click.STYLE_COMMANDS_TABLE_BOX = ""
rich_click.STYLE_COMMANDS_TABLE_ROW_STYLES = None
rich_click.STYLE_COMMANDS_TABLE_BORDER_STYLE = None
rich_click.STYLE_ERRORS_PANEL_BORDER = "red"
rich_click.ALIGN_ERRORS_PANEL = "left"
rich_click.STYLE_ERRORS_SUGGESTION = "dim"
rich_click.STYLE_ABORTED = "red"
rich_click.MAX_WIDTH = None  # Set to an int to limit to that many characters
rich_click.COLOR_SYSTEM = "auto"  # Set to None to disable colors

# Fixed strings
rich_click.HEADER_TEXT = None
rich_click.FOOTER_TEXT = None
rich_click.DEPRECATED_STRING = "(Deprecated) "
rich_click.DEFAULT_STRING = "[default: {}]"
rich_click.ENVVAR_STRING = "[env var: {}]"
rich_click.REQUIRED_SHORT_STRING = "*"
rich_click.REQUIRED_LONG_STRING = "[required]"
rich_click.RANGE_STRING = " [{}]"
rich_click.APPEND_METAVARS_HELP_STRING = "({})"
rich_click.ARGUMENTS_PANEL_TITLE = "Arguments"
rich_click.OPTIONS_PANEL_TITLE = "Options"
rich_click.COMMANDS_PANEL_TITLE = "Commands"
rich_click.ERRORS_PANEL_TITLE = "Error"
rich_click.ERRORS_SUGGESTION = (
    None  # Default: Try 'cmd -h' for help. Set to False to disable.
)
rich_click.ERRORS_EPILOGUE = None
rich_click.ABORTED_TEXT = "Aborted."

# Behaviours
rich_click.SHOW_ARGUMENTS = True  # Show positional arguments
rich_click.SHOW_METAVARS_COLUMN = (
    True  # Show a column with the option metavar (eg. INTEGER)
)
rich_click.APPEND_METAVARS_HELP = (
    False  # Append metavar (eg. [TEXT]) after the help text
)
rich_click.GROUP_ARGUMENTS_OPTIONS = (
    False  # Show arguments with options instead of in own panel
)
rich_click.USE_MARKDOWN = True  # Parse help strings as markdown
rich_click.USE_MARKDOWN_EMOJI = True  # Parse emoji codes in markdown :smile:
rich_click.USE_RICH_MARKUP = (
    False  # Parse help strings for rich markup (eg. [red]my text[/])
)
rich_click.COMMAND_GROUPS = {}  # Define sorted groups of panels to display subcommands
rich_click.OPTION_GROUPS = (
    {}
)  # Define sorted groups of panels to display options and arguments
rich_click.USE_CLICK_SHORT_HELP = (
    False  # Use click's default function to truncate help text
)
