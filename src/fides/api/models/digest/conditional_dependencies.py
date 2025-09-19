from enum import Enum


class DigestConditionType(str, Enum):
    """Types of digest conditions - each can have their own tree."""

    RECEIVER = "receiver"
    CONTENT = "content"
    PRIORITY = "priority"
