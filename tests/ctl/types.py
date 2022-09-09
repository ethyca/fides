from typing import TYPE_CHECKING

if TYPE_CHECKING:

    class FixtureRequest:
        """Type for pytest fixture arguments"""

        param: str

else:
    from typing import Any

    FixtureRequest = Any
