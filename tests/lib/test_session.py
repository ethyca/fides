import pytest
from sqlalchemy import text

from fides.api.db import session
from fides.common.engine_creators import make_sync_creator
from fides.config import get_config


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

    def test_get_engine_with_creator(self) -> None:
        """Engine created via creator= can execute queries."""
        creator = make_sync_creator()
        engine = session.get_db_engine(creator=creator, pool_size=1)
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
        finally:
            engine.dispose()

    def test_creator_with_keepalives_raises(self) -> None:
        """Passing both creator and keepalives params is an error."""
        creator = make_sync_creator()
        with pytest.raises(
            ValueError,
            match="keepalives_idle/interval/count cannot be used with creator",
        ):
            session.get_db_engine(creator=creator, keepalives_idle=30)
