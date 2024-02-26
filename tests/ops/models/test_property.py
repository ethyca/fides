from fides.api.models.property import Property
from fides.api.schemas.property import Property as PropertySchema
from fides.api.schemas.property import PropertyType


class TestProperty:
    def test_create_property(self, db):
        prop = Property.create(
            db=db,
            data=PropertySchema(name="New Property", type=PropertyType.website).dict(),
        )
        assert prop.name == "New Property"
        assert prop.type == PropertyType.website
        assert prop.key == "new_property"
