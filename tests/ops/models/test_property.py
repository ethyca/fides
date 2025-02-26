import json
from typing import Any, Dict

import pytest
from sqlalchemy.orm import Session

from fides.api.models.property import Property, PropertyPath
from fides.api.schemas.privacy_center_config import PrivacyCenterConfig
from fides.api.schemas.property import Property as PropertySchema
from fides.api.schemas.property import PropertyType
from fides.api.util.saas_util import load_as_string


class TestProperty:

    @pytest.fixture
    def privacy_center_config(self) -> PrivacyCenterConfig:
        return PrivacyCenterConfig(
            **json.loads(
                load_as_string("tests/ops/resources/privacy_center_config.json")
            )
        )

    @pytest.fixture(scope="function")
    def minimal_experience(
        self, db, privacy_experience_privacy_center
    ) -> Dict[str, Any]:
        experience_config = privacy_experience_privacy_center.experience_config
        experience_config.name = "Privacy Center"
        experience_config.save(db=db)
        return {"id": experience_config.id, "name": experience_config.name}

    def test_create_property(self, db, minimal_experience, privacy_center_config):
        prop = Property.create(
            db=db,
            data=PropertySchema(
                name="New Property",
                type=PropertyType.website,
                messaging_templates=[],
                experiences=[minimal_experience],
                privacy_center_config=privacy_center_config,
                stylesheet=":root:root { --chakra-colors-gray-50: #fff9ea; }",
                paths=["test"],
            ).model_dump(),
        )
        assert prop.name == "New Property"
        assert prop.type == PropertyType.website
        assert prop.id.startswith("FDS")
        assert prop.privacy_center_config == privacy_center_config.model_dump()
        assert prop.stylesheet == ":root:root { --chakra-colors-gray-50: #fff9ea; }"
        assert prop.paths == ["test"]
        assert prop.is_default is True
        assert len(prop.experiences) == 1

        experience = prop.experiences[0]
        assert experience.id == minimal_experience["id"]
        assert experience.name == minimal_experience["name"]

        prop.delete(db)

    def test_create_second_property(self, db, privacy_center_config, property_a):
        prop = Property.create(
            db=db,
            data=PropertySchema(
                name="New Property 2",
                type=PropertyType.website,
                experiences=[],
                messaging_templates=[],
                privacy_center_config=privacy_center_config,
                stylesheet=":root:root { --chakra-colors-gray-50: #fff9ea; }",
                paths=["testing"],
            ).model_dump(),
        )
        assert prop.name == "New Property 2"
        assert prop.type == PropertyType.website
        assert prop.id.startswith("FDS")
        assert prop.privacy_center_config == privacy_center_config.model_dump()
        assert prop.stylesheet == ":root:root { --chakra-colors-gray-50: #fff9ea; }"
        assert prop.paths == ["testing"]
        assert prop.is_default is False
        assert len(prop.experiences) == 0

        prop.delete(db)

    def test_create_property_duplicate_paths(
        self, db, minimal_experience, privacy_center_config
    ):
        first_prop = Property.create(
            db=db,
            data=PropertySchema(
                name="First Property",
                type=PropertyType.website,
                experiences=[minimal_experience],
                messaging_templates=[],
                privacy_center_config=privacy_center_config,
                stylesheet=":root:root { --chakra-colors-gray-50: #fff9ea; }",
                paths=["test"],
            ).model_dump(),
        )

        with pytest.raises(ValueError):
            Property.create(
                db=db,
                data=PropertySchema(
                    name="Second Property",
                    type=PropertyType.website,
                    experiences=[minimal_experience],
                    messaging_templates=[],
                    privacy_center_config=privacy_center_config,
                    stylesheet=":root:root { --chakra-colors-gray-50: #fff9ea; }",
                    paths=["test"],
                ).model_dump(),
            )

        second_prop = Property.filter(
            db=db, conditions=(Property.name == "Second Property")
        ).first()
        assert second_prop is None

        first_prop.delete(db)

    def test_create_property_with_special_characters(self, db):
        prop = Property.create(
            db=db,
            data=PropertySchema(
                name="New Property (Prod)",
                type=PropertyType.website,
                experiences=[],
                messaging_templates=[],
                paths=[],
            ).model_dump(),
        )
        assert prop.name == "New Property (Prod)"
        assert prop.type == PropertyType.website
        assert prop.id.startswith("FDS")
        assert prop.experiences == []

        prop.delete(db)

    def test_update_property(self, db: Session, property_a, minimal_experience):
        property_a.update(
            db=db,
            data={
                "name": "Property B",
                "type": PropertyType.other,
                "experiences": [minimal_experience],
                "paths": [],
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

    def test_update_property_remove_only_default(self, db: Session, property_a):

        # When property_a fixture gets created, the db model sets is_default to True.
        # Here we attempt to set the only default property to is_default = false
        with pytest.raises(ValueError):
            property_a.update(
                db=db,
                data={
                    "name": "Property A",
                    "type": PropertyType.other,
                    "experiences": [],
                    "paths": [],
                    "is_default": False,
                },
            )

    def test_update_property_duplicate_paths(self, db: Session):
        first_prop = Property.create(
            db=db,
            data=PropertySchema(
                name="First Property",
                type=PropertyType.website,
                experiences=[],
                messaging_templates=[],
                paths=["test"],
            ).model_dump(),
        )

        second_prop = Property.create(
            db=db,
            data=PropertySchema(
                name="Second Property",
                type=PropertyType.website,
                experiences=[],
                messaging_templates=[],
                paths=[],
            ).model_dump(),
        )

        with pytest.raises(ValueError):
            second_prop.update(db=db, data={"paths": ["test"]})

        first_prop.delete(db)
        second_prop.delete(db)

    def test_property_paths_are_deleted_on_property_update(
        self, db: Session, minimal_experience, privacy_center_config
    ):
        prop = Property.create(
            db=db,
            data=PropertySchema(
                name="New Property with Paths",
                type=PropertyType.website,
                experiences=[minimal_experience],
                messaging_templates=[],
                privacy_center_config=privacy_center_config,
                stylesheet=":root:root { --chakra-colors-gray-50: #fff9ea; }",
                paths=["first", "second", "third"],
            ).model_dump(),
        )

        property_paths = PropertyPath.filter(
            db=db, conditions=(PropertyPath.property_id == prop.id)
        ).all()
        assert len(property_paths) == 3

        prop.update(
            db=db,
            data={
                "name": "New Property with Paths",
                "paths": ["first", "second"],
            },
        )

        property_paths = PropertyPath.filter(
            db=db, conditions=(PropertyPath.property_id == prop.id)
        ).all()
        assert len(property_paths) == 2

        prop.delete(db)

    def test_delete_property(self, db: Session, property_a):
        property_a.delete(db=db)
        assert Property.get_by(db=db, field="id", value=property_a.id) is None
        # verify associated paths are automatically deleted
        assert (
            PropertyPath.get_by(db=db, field="property_id", value=property_a.id) is None
        )
