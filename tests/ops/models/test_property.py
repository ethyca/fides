from fides.api.models.property import Property
from fides.api.schemas.property import PropertyCreate, PropertyType


class TestProperty:
    def test_create_property(self, db):
        prop = Property.create(
            db=db,
            data=PropertyCreate(name="New Property", type=PropertyType.website).dict(),
        )
        assert prop.name == "New Property"
        assert prop.type == PropertyType.website
        assert prop.key == "new_property"

    def test_update_property(self, db):
        pass

    def test_delete_property(self, db):
        pass
