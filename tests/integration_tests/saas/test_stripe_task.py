import random
from typing import List

import pytest
import requests

from fidesops.core.config import config
from fidesops.graph.graph import DatasetGraph
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.task import graph_task
from fidesops.task.filter_results import filter_data_categories
from fidesops.task.graph_task import get_cached_data_for_erasures
from tests.graph.graph_test_util import assert_rows_match


@pytest.mark.integration_saas
@pytest.mark.integration_stripe
def test_stripe_access_request_task(
    db,
    policy,
    stripe_connection_config,
    stripe_dataset_config,
    stripe_identity_email,
) -> None:
    """Full access request based on the Stripe SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_stripe_access_request_task_{random.randint(0, 1000)}"
    )
    identity = PrivacyRequestIdentity(**{"email": stripe_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = stripe_connection_config.get_saas_config().fides_key
    merged_graph = stripe_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [stripe_connection_config],
        {"email": stripe_identity_email},
    )

    # verify all collections are returned with the expected number of rows and fields

    assert_rows_match(
        v[f"{dataset_name}:bank_account"],
        min_size=1,
        keys=[
            "account_holder_name",
            "account_holder_type",
            "account_type",
            "bank_name",
            "country",
            "currency",
            "customer",
            "fingerprint",
            "id",
            "last4",
            "object",
            "routing_number",
            "status",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:card"],
        min_size=2,
        keys=[
            "address_city",
            "address_country",
            "address_line1",
            "address_line1_check",
            "address_line2",
            "address_state",
            "address_zip",
            "address_zip_check",
            "brand",
            "country",
            "customer",
            "cvc_check",
            "dynamic_last4",
            "exp_month",
            "exp_year",
            "fingerprint",
            "funding",
            "id",
            "last4",
            "name",
            "object",
            "tokenization_method",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:charge"],
        min_size=3,
        keys=[
            "amount",
            "amount_captured",
            "amount_refunded",
            "application",
            "application_fee",
            "application_fee_amount",
            "balance_transaction",
            "billing_details",
            "calculated_statement_descriptor",
            "captured",
            "created",
            "currency",
            "customer",
            "description",
            "disputed",
            "failure_balance_transaction",
            "failure_code",
            "failure_message",
            "fraud_details",
            "id",
            "invoice",
            "livemode",
            "object",
            "on_behalf_of",
            "order",
            "paid",
            "payment_intent",
            "payment_method",
            "payment_method_details",
            "receipt_email",
            "receipt_number",
            "receipt_url",
            "refunded",
            "review",
            "shipping",
            "source_transfer",
            "statement_descriptor",
            "statement_descriptor_suffix",
            "status",
            "transfer_data",
            "transfer_group",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:credit_note"],
        min_size=1,
        keys=[
            "amount",
            "created",
            "currency",
            "customer",
            "customer_balance_transaction",
            "discount_amount",
            "discount_amounts",
            "id",
            "invoice",
            "livemode",
            "memo",
            "number",
            "object",
            "out_of_band_amount",
            "pdf",
            "reason",
            "refund",
            "status",
            "subtotal",
            "tax_amounts",
            "total",
            "type",
            "voided_at",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=[
            "address",
            "balance",
            "created",
            "currency",
            "default_source",
            "delinquent",
            "description",
            "discount",
            "email",
            "id",
            "invoice_prefix",
            "invoice_settings",
            "livemode",
            "name",
            "next_invoice_sequence",
            "object",
            "phone",
            "preferred_locales",
            "shipping",
            "tax_exempt",
            "test_clock",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:customer_balance_transaction"],
        min_size=5,
        keys=[
            "amount",
            "created",
            "credit_note",
            "currency",
            "customer",
            "description",
            "ending_balance",
            "id",
            "invoice",
            "livemode",
            "object",
            "type",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:dispute"],
        min_size=2,
        keys=[
            "amount",
            "balance_transactions",
            "charge",
            "created",
            "currency",
            "evidence",
            "evidence_details",
            "id",
            "is_charge_refundable",
            "livemode",
            "object",
            "payment_intent",
            "reason",
            "status",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:invoice"],
        min_size=4,
        keys=[
            "account_country",
            "account_name",
            "amount_due",
            "amount_paid",
            "amount_remaining",
            "application_fee_amount",
            "attempt_count",
            "attempted",
            "auto_advance",
            "automatic_tax",
            "billing_reason",
            "charge",
            "collection_method",
            "created",
            "currency",
            "custom_fields",
            "customer",
            "customer_address",
            "customer_email",
            "customer_name",
            "customer_phone",
            "customer_shipping",
            "customer_tax_exempt",
            "customer_tax_ids",
            "default_payment_method",
            "default_source",
            "default_tax_rates",
            "description",
            "discount",
            "discounts",
            "due_date",
            "ending_balance",
            "footer",
            "hosted_invoice_url",
            "id",
            "invoice_pdf",
            "last_finalization_error",
            "livemode",
            "next_payment_attempt",
            "number",
            "object",
            "on_behalf_of",
            "paid",
            "paid_out_of_band",
            "payment_intent",
            "payment_settings",
            "period_end",
            "period_start",
            "post_payment_credit_notes_amount",
            "pre_payment_credit_notes_amount",
            "quote",
            "receipt_number",
            "starting_balance",
            "statement_descriptor",
            "status",
            "status_transitions",
            "subscription",
            "subtotal",
            "tax",
            "test_clock",
            "total",
            "total_tax_amounts",
            "transfer_data",
            "webhooks_delivered_at",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:invoice_item"],
        min_size=4,
        keys=[
            "amount",
            "currency",
            "customer",
            "date",
            "description",
            "discountable",
            "discounts",
            "id",
            "invoice",
            "livemode",
            "object",
            "period",
            "price",
            "proration",
            "quantity",
            "subscription",
            "tax_rates",
            "test_clock",
            "unit_amount",
            "unit_amount_decimal",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:payment_intent"],
        min_size=5,
        keys=[
            "amount",
            "amount_capturable",
            "amount_received",
            "application",
            "application_fee_amount",
            "automatic_payment_methods",
            "canceled_at",
            "cancellation_reason",
            "capture_method",
            "client_secret",
            "confirmation_method",
            "created",
            "currency",
            "customer",
            "description",
            "id",
            "invoice",
            "last_payment_error",
            "livemode",
            "next_action",
            "object",
            "on_behalf_of",
            "payment_method",
            "payment_method_options",
            "payment_method_types",
            "processing",
            "receipt_email",
            "review",
            "setup_future_usage",
            "shipping",
            "statement_descriptor",
            "statement_descriptor_suffix",
            "status",
            "transfer_data",
            "transfer_group",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:payment_method"],
        min_size=2,
        keys=[
            "billing_details",
            "card",
            "created",
            "customer",
            "id",
            "livemode",
            "object",
            "type",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:subscription"],
        min_size=1,
        keys=[
            "application_fee_percent",
            "automatic_tax",
            "billing_cycle_anchor",
            "billing_thresholds",
            "cancel_at",
            "cancel_at_period_end",
            "canceled_at",
            "collection_method",
            "created",
            "current_period_end",
            "current_period_start",
            "customer",
            "days_until_due",
            "default_payment_method",
            "default_source",
            "default_tax_rates",
            "discount",
            "ended_at",
            "id",
            "latest_invoice",
            "livemode",
            "next_pending_invoice_item_invoice",
            "object",
            "pause_collection",
            "payment_settings",
            "pending_invoice_item_interval",
            "pending_setup_intent",
            "pending_update",
            "schedule",
            "start_date",
            "status",
            "test_clock",
            "transfer_data",
            "trial_end",
            "trial_start",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:tax_id"],
        min_size=1,
        keys=[
            "country",
            "created",
            "customer",
            "id",
            "livemode",
            "object",
            "type",
            "value",
            "verification",
        ],
    )

    # verify we only returned data for our identity email
    assert v[f"{dataset_name}:customer"][0]["email"] == stripe_identity_email
    customer_id: str = v[f"{dataset_name}:customer"][0]["id"]

    for bank_account in v[f"{dataset_name}:bank_account"]:
        assert bank_account["customer"] == customer_id

    for card in v[f"{dataset_name}:card"]:
        assert card["customer"] == customer_id

    charge_ids: List[str] = []
    for charge in v[f"{dataset_name}:charge"]:
        assert charge["customer"] == customer_id
        charge_ids.append(charge["id"])

    payment_intent_ids: List[str] = []
    for payment_intent in v[f"{dataset_name}:payment_intent"]:
        assert payment_intent["customer"] == customer_id
        payment_intent_ids.append(payment_intent["id"])

    for credit_note in v[f"{dataset_name}:credit_note"]:
        assert credit_note["customer"] == customer_id

    for bank_account in v[f"{dataset_name}:bank_account"]:
        assert bank_account["customer"] == customer_id

    for customer_balance_transaction in v[
        f"{dataset_name}:customer_balance_transaction"
    ]:
        assert customer_balance_transaction["customer"] == customer_id

    # disputes are retrieved by charge.id or payment_intent.id
    for dispute in v[f"{dataset_name}:dispute"]:
        assert (
            dispute["charge"] in charge_ids
            or dispute["payment_intent"] in payment_intent_ids
        )

    for invoice in v[f"{dataset_name}:invoice"]:
        assert invoice["customer"] == customer_id

    for invoice_item in v[f"{dataset_name}:invoice_item"]:
        assert invoice_item["customer"] == customer_id

    for payment_method in v[f"{dataset_name}:payment_method"]:
        assert payment_method["customer"] == customer_id

    for subscription in v[f"{dataset_name}:subscription"]:
        assert subscription["customer"] == customer_id

    for tax_id in v[f"{dataset_name}:tax_id"]:
        assert tax_id["customer"] == customer_id

    # verify we keep the expected fields after filtering by the user data category
    target_categories = {"user"}
    filtered_results = filter_data_categories(
        v, target_categories, graph.data_category_field_mapping
    )

    assert set(filtered_results.keys()) == {
        f"{dataset_name}:bank_account",
        f"{dataset_name}:card",
        f"{dataset_name}:charge",
        f"{dataset_name}:credit_note",
        f"{dataset_name}:customer",
        f"{dataset_name}:customer_balance_transaction",
        f"{dataset_name}:dispute",
        f"{dataset_name}:invoice",
        f"{dataset_name}:invoice_item",
        f"{dataset_name}:payment_intent",
        f"{dataset_name}:payment_method",
        f"{dataset_name}:subscription",
        f"{dataset_name}:tax_id",
    }

    assert set(filtered_results[f"{dataset_name}:bank_account"][0].keys()) == {
        "account_holder_name",
        "bank_name",
        "country",
        "last4",
        "routing_number",
    }

    assert set(filtered_results[f"{dataset_name}:card"][0].keys()) == {
        "address_city",
        "address_country",
        "address_line1",
        "address_line2",
        "address_state",
        "address_zip",
        "country",
        "dynamic_last4",
        "last4",
        "name",
    }

    assert set(filtered_results[f"{dataset_name}:charge"][0].keys()) == {
        "amount",
        "amount_captured",
        "amount_refunded",
        "billing_details",
        "payment_method_details",
        "receipt_email",
        "source",
    }

    assert set(filtered_results[f"{dataset_name}:credit_note"][0].keys()) == {
        "amount",
        "discount_amount",
        "subtotal",
        "total",
    }

    assert set(filtered_results[f"{dataset_name}:customer"][0].keys()) == {
        "address",
        "balance",
        "email",
        "name",
        "phone",
        "preferred_locales",
        "shipping",
    }

    assert set(
        filtered_results[f"{dataset_name}:customer_balance_transaction"][0].keys()
    ) == {"ending_balance"}

    assert set(filtered_results[f"{dataset_name}:dispute"][0].keys()) == {
        "amount",
        "evidence",
    }

    assert set(filtered_results[f"{dataset_name}:invoice"][0].keys()) == {
        "account_country",
        "account_name",
        "amount_due",
        "amount_paid",
        "amount_remaining",
        "customer_address",
        "customer_email",
        "customer_name",
        "customer_phone",
        "customer_shipping",
        "discount",
        "starting_balance",
        "subtotal",
        "total",
    }

    assert set(filtered_results[f"{dataset_name}:invoice_item"][0].keys()) == {
        "amount",
        "unit_amount",
        "unit_amount_decimal",
    }

    assert set(filtered_results[f"{dataset_name}:payment_intent"][0].keys()) == {
        "amount",
        "amount_capturable",
        "amount_received",
        "receipt_email",
        "shipping",
    }

    assert set(filtered_results[f"{dataset_name}:payment_method"][0].keys()) == {
        "billing_details",
        "card",
    }

    assert set(filtered_results[f"{dataset_name}:subscription"][0].keys()) == {
        "discount",
    }

    assert set(filtered_results[f"{dataset_name}:tax_id"][0].keys()) == {
        "country",
        "verification",
    }


@pytest.mark.integration_saas
@pytest.mark.integration_stripe
def test_stripe_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    stripe_connection_config,
    stripe_dataset_config,
    stripe_erasure_identity_email,
    stripe_create_erasure_data,
) -> None:
    """Full erasure request based on the Stripe SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_stripe_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity = PrivacyRequestIdentity(**{"email": stripe_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = stripe_connection_config.get_saas_config().fides_key
    merged_graph = stripe_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [stripe_connection_config],
        {"email": stripe_erasure_identity_email},
    )

    # verify staged data is available for erasure
    assert_rows_match(
        v[f"{dataset_name}:bank_account"],
        min_size=1,
        keys=[
            "account_holder_name",
            "account_holder_type",
            "account_type",
            "bank_name",
            "country",
            "currency",
            "customer",
            "fingerprint",
            "id",
            "last4",
            "object",
            "routing_number",
            "status",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:card"],
        min_size=1,
        keys=[
            "address_city",
            "address_country",
            "address_line1",
            "address_line1_check",
            "address_line2",
            "address_state",
            "address_zip",
            "address_zip_check",
            "brand",
            "country",
            "customer",
            "cvc_check",
            "dynamic_last4",
            "exp_month",
            "exp_year",
            "fingerprint",
            "funding",
            "id",
            "last4",
            "name",
            "object",
            "tokenization_method",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:charge"],
        min_size=2,
        keys=[
            "amount",
            "amount_captured",
            "amount_refunded",
            "application",
            "application_fee",
            "application_fee_amount",
            "balance_transaction",
            "billing_details",
            "calculated_statement_descriptor",
            "captured",
            "created",
            "currency",
            "customer",
            "description",
            "disputed",
            "failure_balance_transaction",
            "failure_code",
            "failure_message",
            "fraud_details",
            "id",
            "invoice",
            "livemode",
            "object",
            "on_behalf_of",
            "order",
            "paid",
            "payment_intent",
            "payment_method",
            "payment_method_details",
            "receipt_email",
            "receipt_number",
            "receipt_url",
            "refunded",
            "review",
            "shipping",
            "source_transfer",
            "statement_descriptor",
            "statement_descriptor_suffix",
            "status",
            "transfer_data",
            "transfer_group",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:credit_note"],
        min_size=1,
        keys=[
            "amount",
            "created",
            "currency",
            "customer",
            "customer_balance_transaction",
            "discount_amount",
            "discount_amounts",
            "id",
            "invoice",
            "livemode",
            "memo",
            "number",
            "object",
            "out_of_band_amount",
            "pdf",
            "reason",
            "refund",
            "status",
            "subtotal",
            "tax_amounts",
            "total",
            "type",
            "voided_at",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=[
            "address",
            "balance",
            "created",
            "currency",
            "default_source",
            "delinquent",
            "description",
            "discount",
            "email",
            "id",
            "invoice_prefix",
            "invoice_settings",
            "livemode",
            "name",
            "next_invoice_sequence",
            "object",
            "phone",
            "preferred_locales",
            "shipping",
            "tax_exempt",
            "test_clock",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:customer_balance_transaction"],
        min_size=2,
        keys=[
            "amount",
            "created",
            "credit_note",
            "currency",
            "customer",
            "description",
            "ending_balance",
            "id",
            "invoice",
            "livemode",
            "object",
            "type",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:dispute"],
        min_size=3,
        keys=[
            "amount",
            "balance_transactions",
            "charge",
            "created",
            "currency",
            "evidence",
            "evidence_details",
            "id",
            "is_charge_refundable",
            "livemode",
            "object",
            "payment_intent",
            "reason",
            "status",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:invoice"],
        min_size=2,
        keys=[
            "account_country",
            "account_name",
            "amount_due",
            "amount_paid",
            "amount_remaining",
            "application_fee_amount",
            "attempt_count",
            "attempted",
            "auto_advance",
            "automatic_tax",
            "billing_reason",
            "charge",
            "collection_method",
            "created",
            "currency",
            "custom_fields",
            "customer",
            "customer_address",
            "customer_email",
            "customer_name",
            "customer_phone",
            "customer_shipping",
            "customer_tax_exempt",
            "customer_tax_ids",
            "default_payment_method",
            "default_source",
            "default_tax_rates",
            "description",
            "discount",
            "discounts",
            "due_date",
            "ending_balance",
            "footer",
            "hosted_invoice_url",
            "id",
            "invoice_pdf",
            "last_finalization_error",
            "livemode",
            "next_payment_attempt",
            "number",
            "object",
            "on_behalf_of",
            "paid",
            "paid_out_of_band",
            "payment_intent",
            "payment_settings",
            "period_end",
            "period_start",
            "post_payment_credit_notes_amount",
            "pre_payment_credit_notes_amount",
            "quote",
            "receipt_number",
            "starting_balance",
            "statement_descriptor",
            "status",
            "status_transitions",
            "subscription",
            "subtotal",
            "tax",
            "test_clock",
            "total",
            "total_tax_amounts",
            "transfer_data",
            "webhooks_delivered_at",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:invoice_item"],
        min_size=1,
        keys=[
            "amount",
            "currency",
            "customer",
            "date",
            "description",
            "discountable",
            "discounts",
            "id",
            "invoice",
            "livemode",
            "object",
            "period",
            "price",
            "proration",
            "quantity",
            "subscription",
            "tax_rates",
            "test_clock",
            "unit_amount",
            "unit_amount_decimal",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:payment_intent"],
        min_size=1,
        keys=[
            "amount",
            "amount_capturable",
            "amount_received",
            "application",
            "application_fee_amount",
            "automatic_payment_methods",
            "canceled_at",
            "cancellation_reason",
            "capture_method",
            "client_secret",
            "confirmation_method",
            "created",
            "currency",
            "customer",
            "description",
            "id",
            "invoice",
            "last_payment_error",
            "livemode",
            "next_action",
            "object",
            "on_behalf_of",
            "payment_method",
            "payment_method_options",
            "payment_method_types",
            "processing",
            "receipt_email",
            "review",
            "setup_future_usage",
            "shipping",
            "statement_descriptor",
            "statement_descriptor_suffix",
            "status",
            "transfer_data",
            "transfer_group",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:payment_method"],
        min_size=2,
        keys=[
            "billing_details",
            "card",
            "created",
            "customer",
            "id",
            "livemode",
            "object",
            "type",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:subscription"],
        min_size=1,
        keys=[
            "application_fee_percent",
            "automatic_tax",
            "billing_cycle_anchor",
            "billing_thresholds",
            "cancel_at",
            "cancel_at_period_end",
            "canceled_at",
            "collection_method",
            "created",
            "current_period_end",
            "current_period_start",
            "customer",
            "days_until_due",
            "default_payment_method",
            "default_source",
            "default_tax_rates",
            "discount",
            "ended_at",
            "id",
            "latest_invoice",
            "livemode",
            "next_pending_invoice_item_invoice",
            "object",
            "pause_collection",
            "payment_settings",
            "pending_invoice_item_interval",
            "pending_setup_intent",
            "pending_update",
            "schedule",
            "start_date",
            "status",
            "test_clock",
            "transfer_data",
            "trial_end",
            "trial_start",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:tax_id"],
        min_size=1,
        keys=[
            "country",
            "created",
            "customer",
            "id",
            "livemode",
            "object",
            "type",
            "value",
            "verification",
        ],
    )

    # run erasure with MASKING_STRICT to execute the update actions

    config.execution.MASKING_STRICT = True

    x = graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [stripe_connection_config],
        {"email": stripe_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
    )

    # verify masking request was issued for endpoints with an update action
    assert x == {
        f"{dataset_name}:customer": 1,
        f"{dataset_name}:tax_id": 0,
        f"{dataset_name}:invoice_item": 0,
        f"{dataset_name}:charge": 0,
        f"{dataset_name}:invoice": 0,
        f"{dataset_name}:card": 1,
        f"{dataset_name}:customer_balance_transaction": 0,
        f"{dataset_name}:payment_intent": 0,
        f"{dataset_name}:payment_method": 2,
        f"{dataset_name}:credit_note": 0,
        f"{dataset_name}:bank_account": 1,
        f"{dataset_name}:subscription": 0,
        f"{dataset_name}:dispute": 0,
    }

    stripe_secrets = stripe_connection_config.secrets
    base_url = f"https://{stripe_secrets['host']}"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {stripe_secrets['api_key']}",
    }

    # customer
    response = requests.get(
        url=f"{base_url}/v1/customers",
        headers=headers,
        params={"email": stripe_erasure_identity_email},
    )
    customer = response.json()["data"][0]
    customer_id = customer["id"]
    assert customer["shipping"]["name"] == "MASKED"

    # card
    response = requests.get(
        url=f"{base_url}/v1/customers/{customer_id}/sources",
        headers=headers,
        params={"object": "card"},
    )
    card = response.json()["data"][0]
    assert card["name"] == "MASKED"

    # payment method
    response = requests.get(
        url=f"{base_url}/v1/customers/{customer_id}/payment_methods",
        headers=headers,
        params={"type": "card"},
    )
    payment_methods = response.json()["data"]
    for payment_method in payment_methods:
        assert payment_method["billing_details"]["name"] == "MASKED"

    # bank account
    response = requests.get(
        url=f"{base_url}/v1/customers/{customer_id}/sources",
        headers=headers,
        params={"object": "bank_account"},
    )
    bank_account = response.json()["data"][0]
    assert bank_account["account_holder_name"] == "MASKED"

    # run erasure without MASKING_STRICT to execute the delete actions

    config.execution.MASKING_STRICT = False

    x = graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [stripe_connection_config],
        {"email": stripe_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
    )

    # verify masking request was issued for endpoints with an update or delete action
    assert x == {
        f"{dataset_name}:customer": 1,
        f"{dataset_name}:tax_id": 1,
        f"{dataset_name}:invoice_item": 1,
        f"{dataset_name}:charge": 0,
        f"{dataset_name}:invoice": 2,
        f"{dataset_name}:card": 1,
        f"{dataset_name}:customer_balance_transaction": 0,
        f"{dataset_name}:payment_intent": 0,
        f"{dataset_name}:payment_method": 2,
        f"{dataset_name}:credit_note": 0,
        f"{dataset_name}:bank_account": 1,
        f"{dataset_name}:subscription": 1,
        f"{dataset_name}:dispute": 0,
    }

    # customer
    response = requests.get(
        url=f"{base_url}/v1/customers",
        headers=headers,
        params={"email": stripe_erasure_identity_email},
    )
    customer = response.json()["data"][0]
    customer_id = customer["id"]
    assert customer["shipping"]["name"] == "MASKED"

    # tax_id
    response = requests.get(
        url=f"{base_url}/v1/customers/{customer_id}/tax_ids", headers=headers
    )
    tax_ids = response.json()["data"]
    assert tax_ids == []

    # invoice_item
    response = requests.get(
        url=f"{base_url}/v1/invoiceitems",
        headers=headers,
        params={"customer": {customer_id}},
    )
    invoice_item = response.json()["data"]
    # Can't delete an invoice item that is attached to an invoice that is no longer editable
    assert len(invoice_item) == 1

    # card
    response = requests.get(
        url=f"{base_url}/v1/customers/{customer_id}/sources",
        headers=headers,
        params={"object": "card"},
    )
    card = response.json()["data"][0]
    assert card["name"] == "MASKED"

    # payment_method
    response = requests.get(
        url=f"{base_url}/v1/customers/{customer_id}/payment_methods",
        headers=headers,
        params={"type": "card"},
    )
    payment_methods = response.json()["data"]
    for payment_method in payment_methods:
        assert payment_method["billing_details"]["name"] == "MASKED"

    # bank_account
    response = requests.get(
        url=f"{base_url}/v1/customers/{customer_id}/sources",
        headers=headers,
        params={"object": "bank_account"},
    )
    bank_account = response.json()["data"][0]
    assert bank_account["account_holder_name"] == "MASKED"

    # subscription
    response = requests.get(
        url=f"{base_url}/v1/customers/{customer_id}/subscriptions", headers=headers
    )
    subscriptions = response.json()["data"]
    assert subscriptions == []

    # reset
    config.execution.MASKING_STRICT = True
