from typing import Generator

import pytest
from sqlalchemy.orm import Session
from fides.api.models.sql_models import DataUse


class TestHierarchicalTaxonomy:

    @pytest.fixture(scope="function")
    def child_data_use_b(self, db: Session) -> Generator:
        payload_b = {
            "name": "Data Use B",
            "fides_key": "data_use_a.data_use_b",
            "parent_key": "data_use_a",
            "active": True,
            "is_default": False,
            "description": "Data Use B",
        }
        data_use_b = DataUse.create(db=db, data=payload_b)

        yield data_use_b

        data_use_b.delete(db)

    @pytest.fixture(scope="function")
    def child_data_use_c(self, db: Session) -> Generator:
        payload_c = {
            "name": "Data Use C",
            "fides_key": "data_use_a.data_use_c",
            "parent_key": "data_use_a",
            "active": True,
            "is_default": False,
            "description": "Data Use C",
        }
        data_use_c = DataUse.create(db=db, data=payload_c)

        yield data_use_c

        data_use_c.delete(db)

    @pytest.fixture(scope="function")
    def parent_data_use_a(
            self, db
    ) -> Generator:

        payload_a = {
            "name": "Data Use A",
            "fides_key": "data_use_a",
            "active": True,
            "is_default": False,
            "description": "Data Use A",
        }

        data_use_a = DataUse.create(db=db, data=payload_a)

        yield data_use_a

        data_use_a.delete(db)

    def test_create_with_invalid_parent_key(self, db):
        with pytest.raises(ValueError) as exc:
            payload = {
                "name": "Data Use Test",
                "fides_key": "data_use_test",
                "parent_key": "invalid",
                "active": True,
                "is_default": False,
                "description": "Data Use Test",
            }

            DataUse.create(db=db, data=payload)
        assert "something" in str(exc)

    def test_update_with_invalid_parent_key(self, db, parent_data_use_a, child_data_use_b, child_data_use_c):
        with pytest.raises(ValueError) as exc:
            payload = {
                "name": "Data Use update",
                "fides_key": child_data_use_b.fides_key,
                "parent_key": "invalid",
                "description": "Data Use Update",
            }

            child_data_use_b.update(db=db, data=payload)
        assert "something" in str(exc)

    def test_create_with_parent_key(
            self, db, parent_data_use_a, child_data_use_b, child_data_use_c
    ):
        payload = {
            "name": "Data Use Test",
            "fides_key": "new_taxonomy_item",
            "parent_key": child_data_use_b,
            "active": True,
            "is_default": False,
            "description": "Something",
        }

        data_use = DataUse.create(db=db, data=payload)
        assert data_use["fides_key"] == "new_taxonomy_item"

    def test_update_with_parent_key(
            self, db, parent_data_use_a, child_data_use_b, child_data_use_c
    ):
        """
        Tree: A----B
               \
                ----C
        """
        payload = {
            "name": "Data Use Test",
            "fides_key": child_data_use_b.fides_key,
            "parent_key": child_data_use_b.parent_key,
            "active": True,
            "is_default": False,
            "description": "updating this",
        }

        child_data_use_b.update(db=db, data=payload)
        db.commit(child_data_use_b)
        assert child_data_use_b["description"] == "updating this"

    def test_update_no_parent_key(
            self, db, parent_data_use_a, child_data_use_b, child_data_use_c
    ):
        """
        Tree: A----B
               \
                ----C
        """
        payload = {
            "name": "Data Use Test",
            "fides_key": child_data_use_b.fides_key,
            "active": True,
            "is_default": False,
            "description": "updating this",
        }

        child_data_use_b.update(db=db, data=payload)
        db.commit(child_data_use_b)
        assert child_data_use_b["description"] == "updating this"

    @pytest.mark.skip(reason="We never update the parent key from the FE, but we should evaluate what we want to do here")
    def test_update_new_parent_key(
            self, db, parent_data_use_a, child_data_use_b, child_data_use_c
    ):
        pass


    def test_delete_child_data_use(
            self,
            db,
            parent_data_use_a, child_data_use_b, child_data_use_c
    ):
        """
        Tree: A----B
               \
                ----C
        """
        assert len(parent_data_use_a.children) == 2
        assert child_data_use_b.parent.fides_key == parent_data_use_a.fides_key
        assert child_data_use_c.parent.fides_key == parent_data_use_a.fides_key

        child_data_use_c.delete(db)

        # verify it's removed from the parent
        db.refresh(parent_data_use_a)
        assert parent_data_use_a.children == []

    def test_delete_parent_notice(
            self,
            db,
            parent_data_use_a, child_data_use_b, child_data_use_c
    ):
        """
        Tree: A----B
               \
                ----C
        """
        assert len(parent_data_use_a.children) == 2
        assert child_data_use_b.parent.fides_key == parent_data_use_a.fides_key
        assert child_data_use_c.parent.fides_key == parent_data_use_a.fides_key

        with pytest.raises(Exception) as exc:
            parent_data_use_a.delete(db)
