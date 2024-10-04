import pytest

from fides.api.models.policy import Policy
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestShipstationConnector:
    def test_connection(self, shipstation_runner: ConnectorRunner):
        shipstation_runner.test_connection()

    async def test_access_request(
        self,
        shipstation_runner: ConnectorRunner,
        policy: Policy,
        shipstation_identity_email: str,
    ):

        key = shipstation_runner.dataset_config.fides_key
        external_id = shipstation_runner.external_references["customer_id"]
        access_request = await shipstation_runner.access_request(
            access_policy=policy,
            identities={"email": shipstation_identity_email},
        )

        for customer in access_request[f"{key}:customer"]:
            assert customer["customerId"] == int(external_id)

        for order in access_request[f"{key}:orders"]:
            assert order["customerId"] == int(external_id)

        assert_rows_match(
            access_request[f"{key}:customer"],
            min_size=1,
            keys=[
                "customerId",
                "createDate",
                "modifyDate",
                "name",
                "company",
                "street1",
                "street2",
                "city",
                "state",
                "postalCode",
                "countryCode",
                "phone",
                "email",
                "addressVerified",
                "marketplaceUsernames",
                "tags",
            ],
        )
        assert_rows_match(
            access_request[f"{key}:orders"],
            min_size=1,
            keys=[
                "orderId",
                "orderNumber",
                "orderKey",
                "orderDate",
                "createDate",
                "modifyDate",
                "paymentDate",
                "shipByDate",
                "orderStatus",
                "customerId",
                "customerUsername",
                "customerEmail",
                "billTo",
                "shipTo",
                "items",
                "orderTotal",
                "amountPaid",
                "taxAmount",
                "shippingAmount",
                "customerNotes",
                "internalNotes",
                "gift",
                "giftMessage",
                "paymentMethod",
                "requestedShippingService",
                "carrierCode",
                "serviceCode",
                "packageCode",
                "confirmation",
                "shipDate",
                "holdUntilDate",
                "weight",
                "dimensions",
                "insuranceOptions",
                "advancedOptions",
                "tagIds",
                "userId",
                "externallyFulfilled",
                "externallyFulfilledBy",
                "externallyFulfilledById",
                "externallyFulfilledByName",
                "labelMessages",
            ],
        )
