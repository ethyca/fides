import pytest

from fides.core.config import get_config
from fides.api.ops.db import session


class TestGetDbEngine:
    def test_get_session_nothing_provided(self) -> None:
        """Test getting a db engine without passing in any required vars."""
        with pytest.raises(ValueError):
            session.get_db_engine(config=None, database_uri="")

    @pytest.mark.parametrize("test_mode", [True, False])
    def test_get_session_test_modes(self, test_mode: bool) -> None:
        """Test getting a db engine without passing in any required vars."""
        config = get_config()
        original_value = config.test_mode
        config.test_mode = test_mode

        db_engine = session.get_db_engine(config=config)
        config.test_mode = original_value
        assert db_engine
