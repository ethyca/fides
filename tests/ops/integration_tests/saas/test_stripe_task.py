from typing import List

import pytest
import requests

from fides.api.graph.graph import DatasetGraph
from fides.api.models.policy import Policy
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.filter_results import filter_data_categories
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import CONFIG
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner
from tests.ops.test_helpers.cache_secrets_helper import clear_cache_identities


@pytest.mark.integration_saas
class TestStripeConnector:

    def test_stripe_connection_test(self, stripe_runner: ConnectorRunner) -> None:
        stripe_runner.test_connection()

    # @pytest.mark.parametrize(
    #     "dsr_version",
    #     ["use_dsr_3_0", "use_dsr_2_0"],
    # )
    # async def test_stripe_access_request_task_with_email(
    #     self,
    #     stripe_runner: ConnectorRunner,
    #     policy: Policy,
    #     dsr_version,
    #     request,
    #     stripe_identity_email,
    # ) -> None:
    #     """Full access request based on the Stripe SaaS config"""
    #     request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    #     dataset_name = stripe_runner.dataset_config.fides_key

    #     access_results = await stripe_runner.access_request(
    #             access_policy=policy, identities={"email": stripe_identity_email}
    #         )

    #     # verify we only returned data for our identity email

    #     assert len(access_results[f"{dataset_name}:customer"]) == 1

    #     assert access_results[f"{dataset_name}:customer"][0]["email"] == stripe_identity_email
    #     customer_id: str = access_results[f"{dataset_name}:customer"][0]["id"]

    #     for bank_account in access_results[f"{dataset_name}:bank_account"]:
    #         assert bank_account["customer"] == customer_id

    #     for card in access_results[f"{dataset_name}:card"]:
    #         assert card["customer"] == customer_id

    #     charge_ids: List[str] = []
    #     for charge in access_results[f"{dataset_name}:charge"]:
    #         assert charge["customer"] == customer_id
    #         charge_ids.append(charge["id"])

    #     payment_intent_ids: List[str] = []
    #     for payment_intent in access_results[f"{dataset_name}:payment_intent"]:
    #         assert payment_intent["customer"] == customer_id
    #         payment_intent_ids.append(payment_intent["id"])

    #     for credit_note in access_results[f"{dataset_name}:credit_note"]:
    #         assert credit_note["customer"] == customer_id

    #     for bank_account in access_results[f"{dataset_name}:bank_account"]:
    #         assert bank_account["customer"] == customer_id

    #     for customer_balance_transaction in access_results[
    #         f"{dataset_name}:customer_balance_transaction"
    #     ]:
    #         assert customer_balance_transaction["customer"] == customer_id

    #     # disputes are retrieved by charge.id or payment_intent.id
    #     for dispute in access_results[f"{dataset_name}:dispute"]:
    #         assert (
    #             dispute["charge"] in charge_ids
    #             or dispute["payment_intent"] in payment_intent_ids
    #         )

    #     for invoice in access_results[f"{dataset_name}:invoice"]:
    #         assert invoice["customer"] == customer_id

    #     for invoice_item in access_results[f"{dataset_name}:invoice_item"]:
    #         assert invoice_item["customer"] == customer_id

    #     for payment_method in access_results[f"{dataset_name}:payment_method"]:
    #         assert payment_method["customer"] == customer_id

    #     for subscription in access_results[f"{dataset_name}:subscription"]:
    #         assert subscription["customer"] == customer_id

    #     for tax_id in access_results[f"{dataset_name}:tax_id"]:
    #         assert tax_id["customer"] == customer_id

    # @pytest.mark.parametrize(
    #     "dsr_version",
    #     ["use_dsr_3_0", "use_dsr_2_0"],
    # )
    # async def test_stripe_access_request_task_with_phone_number(
    #     self,
    #     stripe_runner: ConnectorRunner,
    #     policy: Policy,
    #     dsr_version,
    #     request,
    #     stripe_identity_email,
    #     stripe_identity_phone_number,
    # ) -> None:
    #     """Full access request based on the Stripe SaaS config"""
    #     request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0
    #     # The Privacy request fixture we're using already has an email/phone cached
    #     # so I'm clearing that first
    #     dataset_name = stripe_runner.dataset_config.fides_key

    #     access_results = await stripe_runner.access_request(
    #         access_policy=policy, identities={"phone_number": stripe_identity_phone_number}
    #     )

    #     # verify we only returned data for our identity phone number and that
    #     # it is the same customer that we retrieved using the identity email
    #     assert access_results[f"{dataset_name}:customer"][0]["phone"] == stripe_identity_phone_number
    #     assert access_results[f"{dataset_name}:customer"][0]["email"] == stripe_identity_email

    @pytest.mark.integration_saas
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_non_strict_erasure_request_with_email(
        self,
        stripe_runner: ConnectorRunner,
        policy: Policy,
        dsr_version,
        request,
        erasure_policy_string_rewrite,
        stripe_erasure_identity_email,
        stripe_test_client,
        stripe_create_erasure_data,
    ) -> None:
        """Full erasure request based on the Stripe SaaS config"""
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        dataset_name = stripe_runner.dataset_config.fides_key

        (
            _,
            erasure_results,
        ) = await stripe_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": stripe_erasure_identity_email},
        )

        # verify masking request was issued for endpoints with both update/delete actions
        assert erasure_results == {
            f"{dataset_name}:customer": 1,
            f"{dataset_name}:tax_id": 1,
            f"{dataset_name}:invoice_item": 1,
            f"{dataset_name}:charge": 0,
            f"{dataset_name}:invoice": 2,
            f"{dataset_name}:card": 1,
            f"{dataset_name}:customer_balance_transaction": 0,
            f"{dataset_name}:payment_intent": 0,
            f"{dataset_name}:payment_method": 3,
            f"{dataset_name}:credit_note": 0,
            f"{dataset_name}:bank_account": 1,
            f"{dataset_name}:subscription": 1,
            f"{dataset_name}:dispute": 0,
        }

        # customer
        customer = stripe_test_client.get_customer(stripe_erasure_identity_email)
        customer_id = customer["id"]
        assert customer["shipping"]["name"] == "MASKED"

        # card
        cards = stripe_test_client.get_card(customer_id)
        assert cards == []

        # payment method
        payment_methods = stripe_test_client.get_payment_method(customer_id)
        for payment_method in payment_methods:
            assert payment_method["billing_details"]["name"] == "MASKED"

        # bank account
        bank_account = stripe_test_client.get_bank_account(customer_id)
        assert bank_account["account_holder_name"] == "MASKED"

        # tax_id
        tax_ids = stripe_test_client.get_tax_ids(customer_id)
        assert tax_ids == []

        # invoice_item
        invoice_item = stripe_test_client.get_invoice_items(customer_id)
        # Can't delete an invoice item that is attached to an invoice that is no longer editable
        assert len(invoice_item) == 1

        # subscription
        subscriptions = stripe_test_client.get_subscription(customer_id)
        assert subscriptions == []
