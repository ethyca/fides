from typing import Optional

from fideslang.validation import FidesKey


class FidesOpsKey(FidesKey):
    """
    Overrides fideslang FidesKey validation to throw ValueError
    """

    @classmethod
    def validate(cls, value: Optional[str]) -> Optional[str]:
        """Throws ValueError if val is not a valid FidesKey"""
        if value == "<instance_fides_key>":
            # Ignore <instance_fides_key> in saas templates.  This value will be replaced with a
            # user-specified value.
            return value

        if value is not None and not cls.regex.match(value):
            raise ValueError(
                "FidesKey must only contain alphanumeric characters, '.', '_' or '-'."
            )

        return value
