from sqlalchemy.orm import Session

from fides.api.models.custom_asset import CustomAsset, CustomAssetType


class TestCustomAsset:
    def test_custom_asset(self, db: Session):
        CustomAsset.create_or_update(
            db,
            data={
                "key": CustomAssetType.fides_css.value,
                "content": "--fides-overlay-primary-color: #00ff00;",
            },
        )
        custom_asset = CustomAsset.get_by(
            db, field="key", value=CustomAssetType.fides_css.value
        )
        assert custom_asset is not None
        assert custom_asset.content == "--fides-overlay-primary-color: #00ff00;"
