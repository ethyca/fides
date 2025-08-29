from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.models.sql_models import System
from fides.api.models.system_group import SystemGroup, SystemGroupMember
from fides.api.models.taxonomy import Taxonomy, TaxonomyElement


@pytest.fixture
def system_group_element(db: Session) -> TaxonomyElement:
    """Create a dedicated taxonomy and element to back a SystemGroup fides_key."""
    taxonomy_key = "system_group"
    taxonomy = Taxonomy.create(
        db=db,
        data={
            "fides_key": taxonomy_key,
            "name": "System Groups",
            # Allow application to systems
            "applies_to": ["system"],
        },
    )

    element = TaxonomyElement.create(
        db=db,
        data={
            "taxonomy_type": taxonomy.fides_key,
            "fides_key": "engineering",
            "name": "Engineering",
        },
    )
    return element


class TestSystemGroup:
    def test_create_system_group_minimal(self, db: Session, system_group_element):
        system_group = SystemGroup.create(
            db=db,
            data={
                "fides_key": system_group_element.fides_key,
            },
        )
        assert system_group.id is not None
        assert system_group.fides_key == system_group_element.fides_key
        assert system_group.data_uses == []  # default
        assert system_group.label_color is None
        assert system_group.data_steward is None

    def test_create_system_group_full(
        self, db: Session, system_group_element: TaxonomyElement, user
    ):
        group = SystemGroup.create(
            db=db,
            data={
                "fides_key": system_group_element.fides_key,
                "data_steward": user.username,
                "data_uses": [
                    "essential.service",
                    "marketing.advertising",
                ],
            },
        )
        assert (
            group.data_steward is not None
            and group.data_steward.username == user.username
        )
        assert set(group.data_uses) == {"essential.service", "marketing.advertising"}

    def test_fides_key_unique_constraint(
        self, db: Session, system_group_element: TaxonomyElement
    ):
        SystemGroup.create(db=db, data={"fides_key": system_group_element.fides_key})
        with pytest.raises(IntegrityError):
            SystemGroup.create(
                db=db, data={"fides_key": system_group_element.fides_key}
            )


class TestSystemGroupMember:
    @pytest.fixture
    def system_group(
        self, db: Session, system_group_element: TaxonomyElement
    ) -> SystemGroup:
        return SystemGroup.create(
            db=db, data={"fides_key": system_group_element.fides_key}
        )

    def test_create_member(
        self, db: Session, system_group: SystemGroup, system: System
    ):
        member = SystemGroupMember.create(
            db=db,
            data={
                "system_group_id": system_group.id,
                "system_id": system.id,
            },
        )
        assert member.id is not None
        assert member.system_group_id == system_group.id
        assert member.system_id == system.id

    def test_unique_group_system_pair(
        self, db: Session, system_group: SystemGroup, system: System
    ):
        SystemGroupMember.create(
            db=db,
            data={
                "system_group_id": system_group.id,
                "system_id": system.id,
            },
        )
        with pytest.raises(IntegrityError):
            SystemGroupMember.create(
                db=db,
                data={
                    "system_group_id": system_group.id,
                    "system_id": system.id,
                },
            )

    def test_cascade_delete_on_group(
        self, db: Session, system_group: SystemGroup, system: System
    ):
        member = SystemGroupMember.create(
            db=db,
            data={
                "system_group_id": system_group.id,
                "system_id": system.id,
            },
        )
        member_id = member.id
        # Delete the group; members should cascade-delete
        system_group.delete(db)
        assert db.query(SystemGroupMember).filter_by(id=member_id).first() is None

    def test_cascade_delete_on_system(
        self, db: Session, system_group: SystemGroup, system_with_cleanup: System
    ):
        member = SystemGroupMember.create(
            db=db,
            data={
                "system_group_id": system_group.id,
                "system_id": system_with_cleanup.id,
            },
        )
        member_id = member.id
        # Delete the system; members should cascade-delete
        system_with_cleanup.delete(db)
        assert db.query(SystemGroupMember).filter_by(id=member_id).first() is None
