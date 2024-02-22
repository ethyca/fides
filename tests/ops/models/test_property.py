from fides.api.models.property import Property, PropertyType


class TestProperty:
    def test_create_property(self, db):
        prop = Property.create(
            db=db, data={"name": "New Property", "type": PropertyType.website}
        )
        assert prop.name == "New Property"
        assert prop.type == PropertyType.website.value
        assert prop.key == "new_property"

    def test_update_property(self, db):
        pass

    def test_delete_property(self, db):
        pass
