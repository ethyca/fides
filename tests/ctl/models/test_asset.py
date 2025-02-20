from typing import Any, Dict
from uuid import uuid4

import pytest
from fideslang.models import System as SystemSchema
from sqlalchemy import delete, insert, select
from sqlalchemy.exc import IntegrityError

from fides.api.db.system import create_system
from fides.api.models.asset import Asset

"""
Unit tests for the Asset model class.

These tests are in the `test/ctl` subdir to load async db fixtures correctly.
"""


@pytest.fixture(autouse=True)
async def clear_table(async_session):
    """Ensure a clean table state before and after each test."""
    async with async_session.begin():
        await async_session.execute(delete(Asset))
    yield
    async with async_session.begin():
        await async_session.execute(delete(Asset))


@pytest.fixture()
async def javascript_asset_data(system_async) -> Dict[str, Any]:
    return {
        "name": "gtm.js",
        "asset_type": "javascript",
        "base_url": "https://www.googletagmanager.com/gtm.js",
        "domain": "www.googletagmanager.com",
        "system_id": system_async.id,
        "locations": ["US", "Canada"],
        "data_uses": ["analytics"],
        "meta": {
            "prop_1": "test",
        },
    }


@pytest.fixture()
async def cookie_asset_data(system_async) -> Dict[str, Any]:
    # cookies have no `base_url`
    return {
        "name": "cookie1",
        "asset_type": "cookie",
        "domain": "www.googletagmanager.com",
        "system_id": system_async.id,
        "locations": ["US", "Canada"],
        "data_uses": ["analytics"],
    }


@pytest.fixture
async def system_2_async(async_session):
    resource = SystemSchema(
        fides_key=str(uuid4()),
        organization_fides_key="default_organization",
        name="test_system_2",
        system_type="test",
        privacy_declarations=[],
    )

    system = await create_system(
        resource,
        async_session,
    )
    return system


class TestUpsertAsset:

    async def test_upsert_asset_async(self, async_session, javascript_asset_data):
        """
        Tests basic upsert (create and update) function of the Asset model.

        Ensures that upsert function defines uniqueness criteria based on input data.
        """
        async with async_session.begin():
            created_asset = await Asset.upsert_async(
                async_session=async_session,
                data=javascript_asset_data,
            )

            # ensure our asset was stored in the DB properly
            created_asset: Asset = (
                (
                    await async_session.execute(
                        select(Asset).where(Asset.id == created_asset.id)
                    )
                )
                .scalars()
                .first()
            )

            assert created_asset.name == "gtm.js"
            assert created_asset.asset_type == "javascript"
            assert created_asset.domain == "www.googletagmanager.com"
            assert created_asset.system_id == javascript_asset_data["system_id"]
            assert created_asset.base_url == "https://www.googletagmanager.com/gtm.js"
            assert created_asset.locations == ["US", "Canada"]
            assert created_asset.data_uses == ["analytics"]

            # update a field on the asset - specifically, this field is _not_ part of uniqueness criteria
            javascript_asset_data["locations"] = ["US", "Canada", "EU"]
            # update existing meta prop
            javascript_asset_data["meta"]["prop_1"] = "updated"
            # and add a new meta prop
            javascript_asset_data["meta"]["prop_2"] = "test"

            # and update the asset
            await Asset.upsert_async(
                async_session=async_session,
                data=javascript_asset_data,
            )

            # retrieve updated asset, ensure it's the same record as before,
            # but with updated locations
            updated_asset: Asset = (
                (
                    await async_session.execute(
                        select(Asset).where(
                            Asset.id == created_asset.id
                        )  # same ID as created asset above
                    )
                )
                .scalars()
                .first()
            )

            # check locations have been updated
            assert updated_asset.locations == [
                "US",
                "Canada",
                "EU",
            ]  # check updated locations
            # check meta is updated as expected
            assert updated_asset.meta["prop_1"] == "updated"
            assert updated_asset.meta["prop_2"] == "test"

            # ensure all other attributes have stayed the same
            assert updated_asset.name == created_asset.name
            assert updated_asset.asset_type == created_asset.asset_type
            assert updated_asset.domain == created_asset.domain
            assert updated_asset.system_id == created_asset.system_id
            assert updated_asset.base_url == created_asset.base_url

            # now, let's change an attribute that's part of the uniqueness criteria,
            # and ensure a new asset is created
            javascript_asset_data["name"] = "gtm2.js"
            new_asset = await Asset.upsert_async(
                async_session=async_session,
                data=javascript_asset_data,
            )

            # now, retrieve new asset
            new_asset: Asset = (
                (
                    await async_session.execute(
                        select(Asset).where(Asset.id == new_asset.id)
                    )
                )
                .scalars()
                .first()
            )
            # ensure it is a _new_ record, i.e. `id` is different
            assert new_asset.id != updated_asset.id
            # ensure all other attributes are as expected
            assert new_asset.name == "gtm2.js"
            assert new_asset.asset_type == "javascript"
            assert new_asset.domain == "www.googletagmanager.com"
            assert new_asset.system_id == javascript_asset_data["system_id"]
            assert new_asset.base_url == "https://www.googletagmanager.com/gtm.js"

    # @pytest.mark.skip(reason="Figuring out unique index constraints")
    async def test_upsert_asset_no_base_url(self, async_session, cookie_asset_data):
        """
        Ensures assets can be created and updated without a `base_url` even if `base_url` is part of unique key.

        Ensures adding a base URL to an asset properly creates a new record with the upsert function.
        """

        async with async_session.begin():
            created_asset = await Asset.upsert_async(
                async_session=async_session,
                data=cookie_asset_data,
            )

            # ensure our asset was stored in the DB properly
            created_asset: Asset = (
                (
                    await async_session.execute(
                        select(Asset).where(Asset.id == created_asset.id)
                    )
                )
                .scalars()
                .first()
            )

            assert created_asset.name == "cookie1"
            assert created_asset.asset_type == "cookie"
            assert created_asset.domain == "www.googletagmanager.com"
            assert created_asset.system_id == cookie_asset_data["system_id"]
            assert created_asset.base_url is None
            assert created_asset.locations == ["US", "Canada"]
            assert created_asset.data_uses == ["analytics"]

            # now add a base_url, and ensure a _new_ record is created
            cookie_asset_data["base_url"] = "https://www.googletagmanager.com/gtm.js"
            new_asset = await Asset.upsert_async(
                async_session=async_session,
                data=cookie_asset_data,
            )

            # retrieve new asset
            new_asset: Asset = (
                (
                    await async_session.execute(
                        select(Asset).where(Asset.id == new_asset.id)
                    )
                )
                .scalars()
                .first()
            )
            # ensure this is an entirely new record
            assert new_asset.id != created_asset.id
            # ensure base_url is set
            assert new_asset.base_url == "https://www.googletagmanager.com/gtm.js"
            # sanity check other attributes are set correctly
            assert new_asset.name == "cookie1"
            assert new_asset.asset_type == "cookie"
            assert new_asset.domain == "www.googletagmanager.com"
            assert new_asset.system_id == cookie_asset_data["system_id"]
            assert new_asset.locations == ["US", "Canada"]

    async def test_upsert_asset_requires_uniqueness_attributes(
        self, async_session, javascript_asset_data
    ):
        """
        Ensures the upsert function raises a ValueError if required uniqueness attributes are not provided.
        """
        # remove a required attribute
        del javascript_asset_data["domain"]
        with pytest.raises(ValueError) as e:
            await Asset.upsert_async(
                async_session=async_session,
                data=javascript_asset_data,
            )


class TestGetAssetBySystem:
    @pytest.fixture
    async def create_assets_for_systems(
        self, async_session, javascript_asset_data, system_2_async
    ):
        async with async_session.begin():
            # create one asset tied to system 1
            created_asset_1 = await Asset.upsert_async(
                async_session=async_session,
                data=javascript_asset_data,
            )

            # create another asset tied to system 1
            javascript_asset_data["name"] = "gtm2.js"
            created_asset_2 = await Asset.upsert_async(
                async_session=async_session,
                data=javascript_asset_data,
            )

            # create a third asset tied to system 2
            javascript_asset_data["name"] = "gtm3.js"
            javascript_asset_data["system_id"] = system_2_async.id
            created_asset_3 = await Asset.upsert_async(
                async_session=async_session,
                data=javascript_asset_data,
            )

            return (created_asset_1, created_asset_2, created_asset_3)

    async def test_get_asset_by_system_async(
        self, async_session, create_assets_for_systems, system_async, system_2_async
    ):
        """
        Tests the get_by_system_async function of the Asset model.

        Ensures that the function returns the correct assets for a given system.
        """

        async with async_session.begin():
            # now, retrieve assets for system 1 by its id
            assets = await Asset.get_by_system_async(
                async_session=async_session,
                system_id=system_async.id,
            )

            # ensure we have 2 assets for system 1
            assert len(assets) == 2

            # ensure the assets are as expected
            assert create_assets_for_systems[0] in assets
            assert create_assets_for_systems[1] in assets

            # and retrieve assets for system 1 by its key
            assets = await Asset.get_by_system_async(
                async_session=async_session,
                system_fides_key=system_async.fides_key,
            )

            # ensure we have 2 assets for system 1
            assert len(assets) == 2

            # ensure the assets are as expected
            assert create_assets_for_systems[0] in assets
            assert create_assets_for_systems[1] in assets

            # now, retrieve assets for system 2 by its id
            assets = await Asset.get_by_system_async(
                async_session=async_session,
                system_id=system_2_async.id,
            )

            # ensure we have 1 assets for system 2
            assert len(assets) == 1

            # ensure the assets are as expected
            assert create_assets_for_systems[2] in assets


class TestAssetDbConstraints:
    async def test_asset_unique_index(self, async_session, javascript_asset_data):
        """
        Ensures the db-level unique index works as expected for the Asset model.
        """
        async with async_session.begin():
            created_asset = await Asset.upsert_async(
                async_session=async_session,
                data=javascript_asset_data,
            )

            # now try to 'manually' insert a different asset but with same uniqueness criteria
            # and ensure it's rejected at the db level.
            # this is not done through the upsert function, as that would attempt to update the existing record
            javascript_asset_data["locations"] = ["US", "Canada", "EU"]
            with pytest.raises(IntegrityError):
                await async_session.execute(insert(Asset).values(javascript_asset_data))

        async with async_session.begin():
            # if we remove the base_url, this should be valid, as it's hitting a different unique key
            del javascript_asset_data["base_url"]
            result = await async_session.execute(
                insert(Asset).values(javascript_asset_data)
            )
            assert result.inserted_primary_key.id
