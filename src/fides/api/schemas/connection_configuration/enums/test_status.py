from enum import Enum
from typing import Optional


class TestStatus(Enum):
    passed = "passed"
    failed = "failed"
    untested = "untested"

    def str_to_bool(self) -> Optional[bool]:
        """Translates query param string to optional/bool value
        for filtering ConnectionConfig.last_test_succeeded field"""
        if self == self.passed:
            return True
        if self == self.failed:
            return False
        return None
