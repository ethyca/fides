import pytest
from starlette.status import HTTP_200_OK
from starlette.testclient import TestClient

from fides.api.models.sql_models import System  # type: ignore[attr-defined]
from fides.common.api.scope_registry import SYSTEM_UPDATE
from fides.common.api.v1.urn_registry import V1_URL_PREFIX


class TestAssignDataSteward:
    def test_assign_data_steward(
        self,
        api_client: TestClient,
        db,
        owner_user,
        generate_auth_header,
        system: System,
    ):
        """Assign an existing user as data steward to two systems and verify assignments."""

        # Create a second system to assign
        second_system: System = System.create(
            db=db,
            data={
                "fides_key": "second.system",
                "name": "Second System",
            },
        )

        url = V1_URL_PREFIX + "/system/assign-steward"
        payload = {
            "data_steward": owner_user.username,
            "system_keys": [system.fides_key, second_system.fides_key],
        }

        auth_header = generate_auth_header(scopes=[SYSTEM_UPDATE])
        response = api_client.post(url, headers=auth_header, json=payload)
        import pdb

        pdb.set_trace()
        assert response.status_code == HTTP_200_OK

        # Refresh instances from DB to pick up relationship changes
        db.refresh(system)
        db.refresh(second_system)

        assert owner_user in system.data_stewards
        assert owner_user in second_system.data_stewards
