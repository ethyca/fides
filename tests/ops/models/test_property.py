from typing import Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.models.property import Property
from fides.api.schemas.property import Property as PropertySchema
from fides.api.schemas.property import PropertyType


class TestProperty:
    @pytest.fixture
    def property_a(self, db) -> Generator:
        prop_a = Property.create(
            db=db,
            data=PropertySchema(name="New Property", type=PropertyType.website).dict(),
        )
        yield prop_a
        prop_a.delete(db=db)

    def test_create_property(self, db):
        prop = Property.create(
            db=db,
            data=PropertySchema(name="New Property", type=PropertyType.website).dict(),
        )
        assert prop.name == "New Property"
        assert prop.type == PropertyType.website
        assert prop.id.startswith("FDS")
        assert prop.experiences == []

    def test_create_property_with_special_characters(self, db):
        prop = Property.create(
            db=db,
            data=PropertySchema(
                name="New Property (Prod)", type=PropertyType.website
            ).dict(),
        )
        assert prop.name == "New Property (Prod)"
        assert prop.type == PropertyType.website
        assert prop.id.startswith("FDS")
        assert prop.experiences == []

    def test_update_property(self, db: Session, property_a):
        property_a.name = "Property B"
        property_a.type = PropertyType.other
        property_a.save(db=db)

        updated_property = Property.get_by(db=db, field="id", value=property_a.id)
        assert updated_property.name == "Property B"
        assert updated_property.type == PropertyType.other
        assert updated_property.id.startswith("FDS")
        assert updated_property.experiences == []


class TestPrivacyExperienceConfigProperty:
    @pytest.fixture
    def property_a(self, db) -> Generator:
        prop_a = Property.create(
            db=db,
            data=PropertySchema(name="New Property", type=PropertyType.website).dict(),
        )
        yield prop_a
        prop_a.delete(db=db)

    def test_link_property_and_experience(
        self, db: Session, property_a, privacy_experience_privacy_center
    ):
        experience_config = privacy_experience_privacy_center.experience_config
        experience_config.name = "Privacy Center"
        experience_config.save(db=db)

        property_a.experiences.append(
            privacy_experience_privacy_center.experience_config
        )
        property_a.save(db=db)

        updated_property = Property.get_by(db=db, field="id", value=property_a.id)
        assert updated_property.name == "New Property"
        assert updated_property.type == PropertyType.website
        assert updated_property.id.startswith("FDS")
        assert len(updated_property.experiences) == 1

        experience = updated_property.experiences[0]
        assert experience.name == "Privacy Center"
