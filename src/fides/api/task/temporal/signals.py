"""Signal dataclasses for Temporal workflow communication.

Used by manual tasks and async callback tasks to unblock
waiting workflows when external input is received.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class TaskCompletedSignal:
    """Signal sent when a manual or callback task receives external input."""

    collection_address: str
    data: Optional[Dict[str, Any]] = None
    rows_masked: Optional[int] = None
