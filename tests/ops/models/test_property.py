from typing import Any, Dict, Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.models.privacy_experience import PrivacyExperienceConfig
from fides.api.models.property import Property
from fides.api.schemas.property import Property as PropertySchema
from fides.api.schemas.property import PropertyType


class TestProperty:
    @pytest.fixture(scope="function")
    def property_a(self, db) -> Generator:
        prop_a = Property.create(
            db=db,
            data=PropertySchema(name="New Property", type=PropertyType.website).dict(),
        )
        yield prop_a
        prop_a.delete(db=db)

    @pytest.fixture(scope="function")
    def minimal_experience(
        self, db, privacy_experience_privacy_center
    ) -> Dict[str, Any]:
        experience_config = privacy_experience_privacy_center.experience_config
        experience_config.name = "Privacy Center"
        experience_config.save(db=db)
        return {"id": experience_config.id, "name": experience_config.name}

    def test_create_property(self, db, minimal_experience):
        prop = Property.create(
            db=db,
            data=PropertySchema(
                name="New Property",
                type=PropertyType.website,
                experiences=[minimal_experience],
            ).dict(),
        )
        assert prop.name == "New Property"
        assert prop.type == PropertyType.website
        assert prop.id.startswith("FDS")
        assert len(prop.experiences) == 1

        experience = prop.experiences[0]
        assert experience.id == minimal_experience["id"]
        assert experience.name == minimal_experience["name"]

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

    def test_update_property(self, db: Session, property_a, minimal_experience):
        property_a.update(
            db=db,
            data={
                "name": "Property B",
                "type": PropertyType.other,
                "experiences": [minimal_experience],
            },
        )

        updated_property = Property.get_by(db=db, field="id", value=property_a.id)
        assert updated_property.name == "Property B"
        assert updated_property.type == PropertyType.other
        assert updated_property.id.startswith("FDS")
        assert len(updated_property.experiences) == 1

        experience = updated_property.experiences[0]
        assert experience.id == minimal_experience["id"]
        assert experience.name == minimal_experience["name"]
