"""Bot slash commands."""

from .usage_command import setup_usage_command
from .nominate_command import setup_nominate_command
from .react_all_command import setup_react_all_command
from .check_activity_command import setup_check_activity_command

__all__ = [
    "setup_usage_command",
    "setup_nominate_command",
    "setup_react_all_command",
    "setup_check_activity_command",
]
