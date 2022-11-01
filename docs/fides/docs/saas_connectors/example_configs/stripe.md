
# Stripe

## Implementation Summary

Fides uses the following Stripe endpoints to retrieve and delete Personally Identifiable Information (PII) when processing a Privacy Request. Right to Access and Right to Delete (Right to Forget) support for each endpoint is noted below.

|Endpoint | Right to Access | Right to Delete |
|----|----|----|
|[Customers](https://stripe.com/docs/api/customers/update) | Yes | Yes |
|[Charges](https://stripe.com/docs/api/charges/list) | Yes | No |
|[Disputes](https://stripe.com/docs/api/disputes/list) | Yes | No |
|[Payment Intents](https://stripe.com/docs/api/payment_intents/list) | Yes | Yes |
|[Payment Methods](https://stripe.com/docs/api/payment_methods/list) | Yes | No |
|[Bank Accounts](https://stripe.com/docs/api/customer_bank_accounts/list) | Yes | Yes |
|[Cards](https://stripe.com/docs/api/cards/list) | Yes | Yes |
|[Credit Notes](https://stripe.com/docs/api/credit_notes/list) | Yes | No |
|[Customer Balance Transactions](https://stripe.com/docs/api/customer_balance_transactions/list) | Yes | No |
|[Tax IDs](https://stripe.com/docs/api/customer_tax_ids/list) | Yes | Yes |
|[Invoices](https://stripe.com/docs/api/invoices/list) | Yes | Yes |
|[Invoice Items](https://stripe.com/docs/api/invoiceitems/list) | Yes | Yes |
|[Subscriptions](https://stripe.com/docs/api/subscriptions/list) | Yes | Yes |

## Connection Settings

Fides provides a [Postman collection](../../development/postman/using_postman.md) for easily establishing connections to your third party applications. Additional connection instructions may be found in the [configuration guide](../saas_config.md).

**Deletion requests** are fulfilled by masking PII via `UPDATE` endpoints. To [give Fides permission](../../installation/configuration.md#configuration-variable-reference) to remove PII using `DELETE` endpoints, ensure the `masking_strict` variable in your `fides.toml` file is set to `false`.

## Example Stripe Configuration

```yaml
saas_config:
  fides_key: stripe_connector_example
  name: Stripe SaaS Config
  description: A sample schema representing the Stripe connector for Fides
  version: 0.0.1

  connector_params:
    - name: host
    - name: api_key
    - name: payment_types
    - name: items_per_page

  client_config:
    protocol: https
    host:
      connector_param: host
    authentication:
      strategy: bearer_authentication
      configuration:
        token:
          connector_param: api_key

  test_request:
    method: GET
    path: /v1/customers
    
  endpoints:
  - name: customer
    requests:
      read:
        method: GET
        path: /v1/customers
        query_params:
          - name: email
            value: <email>
        param_values:
          - name: email
            identity: email
        data_path: data
      update:
        method: POST
        path: /v1/customers/<customer_id>
        headers:
          - name: Content-Type
            value: application/x-www-form-urlencoded
        param_values:
          - name: customer_id
            references:
              - dataset: stripe_connector_example
                field: customer.id
                direction: from
        body: '{<all_object_fields>}'
  - name: charge
    requests:
      read: 
        method: GET
        path: /v1/charges
        query_params:
          - name: customer
            value: <customer_id>
          - name: limit
            value: <limit>
        param_values:
          - name: customer_id
            references:
              - dataset: stripe_connector_example
                field: customer.id
                direction: from
          - name: limit
            connector_param: items_per_page
        data_path: data
        pagination:
          strategy: cursor
          configuration:
            cursor_param: starting_after
            field: id
  - name: dispute
    requests:
      read:
        method: GET
        path: /v1/disputes
        query_params:
          - name: charge
            value: <charge_id>
          - name: payment_intent
            value: <payment_intent_id>
          - name: limit
            value: <limit>
        param_values:
          - name: charge_id
            references:
              - dataset: stripe_connector_example
                field: charge.id
                direction: from
          - name: payment_intent_id
            references:
              - dataset: stripe_connector_example
                field: payment_intent.id
                direction: from
          - name: limit
            connector_param: items_per_page
        data_path: data
        pagination:
          strategy: cursor
          configuration:
            cursor_param: starting_after
            field: id
  - name: payment_intent
    requests:
      read:
        method: GET
        path: /v1/payment_intents
        query_params:
          - name: customer
            value: <customer_id>
          - name: limit
            value: <limit>
        param_values:
          - name: customer_id
            references:
              - dataset: stripe_connector_example
                field: customer.id
                direction: from
          - name: limit
            connector_param: items_per_page
        data_path: data
        pagination:
          strategy: cursor
          configuration:
            cursor_param: starting_after
            field: id
  - name: payment_method
    requests:
      read:
        method: GET
        path: /v1/customers/<customer_id>/payment_methods
        query_params:
          - name: type
            value: <type>
          - name: limit
            value: <limit>
        param_values:
          - name: customer_id
            references:
              - dataset: stripe_connector_example
                field: customer.id
                direction: from
          - name: type
            connector_param: payment_types
          - name: limit
            connector_param: items_per_page
        data_path: data
        pagination:
          strategy: cursor
          configuration:
            cursor_param: starting_after
            field: id
      update:
        method: POST
        path: /v1/payment_methods/<payment_method_id>
        headers:
          - name: Content-Type
            value: application/x-www-form-urlencoded
        param_values:
          - name: payment_method_id
            references:
              - dataset: stripe_connector_example
                field: payment_method.id
                direction: from
        body: '{<masked_object_fields>}'
  - name: bank_account
    requests:
      read:
        method: GET
        path: /v1/customers/<customer_id>/sources
        query_params:
          - name: object
            value: bank_account
          - name: limit
            value: <limit>
        param_values:
          - name: customer_id
            references:
              - dataset: stripe_connector_example
                field: customer.id
                direction: from
          - name: limit
            connector_param: items_per_page
        data_path: data
        pagination:
          strategy: cursor
          configuration:
            cursor_param: starting_after
            field: id
      update:
        method: POST
        path: /v1/customers/<customer_id>/sources/<bank_account_id>
        headers:
          - name: Content-Type
            value: application/x-www-form-urlencoded
        param_values:
          - name: customer_id
            references:
              - dataset: stripe_connector_example
                field: bank_account.customer
                direction: from
          - name: bank_account_id
            references:
              - dataset: stripe_connector_example
                field: bank_account.id
                direction: from
        body: '{<masked_object_fields>}'
  - name: card
    requests:
      read:
        method: GET
        path: /v1/customers/<customer_id>/sources
        query_params:
          - name: object
            value: card
          - name: limit
            value: <limit>
        param_values:
          - name: customer_id
            references:
              - dataset: stripe_connector_example
                field: customer.id
                direction: from
          - name: limit
            connector_param: items_per_page
        data_path: data
        pagination:
          strategy: cursor
          configuration:
            cursor_param: starting_after
            field: id
      update:
        method: POST
        path: /v1/customers/<customer_id>/sources/<card_id>
        headers:
          - name: Content-Type
            value: application/x-www-form-urlencoded
        param_values:
          - name: customer_id
            references:
              - dataset: stripe_connector_example
                field: card.customer
                direction: from
          - name: card_id
            references:
              - dataset: stripe_connector_example
                field: card.id
                direction: from
        body: '{<masked_object_fields>}'
  - name: credit_note
    requests:
      read:
        method: GET
        path: /v1/credit_notes
        query_params:
          - name: customer
            value: <customer_id>
          - name: limit
            value: <limit>
        param_values:
          - name: customer_id
            references:
              - dataset: stripe_connector_example
                field: customer.id
                direction: from
          - name: limit
            connector_param: items_per_page
        data_path: data
        pagination:
          strategy: cursor
          configuration:
            cursor_param: starting_after
            field: id
  - name: customer_balance_transaction
    requests:
      read:
        method: GET
        path: /v1/customers/<customer_id>/balance_transactions
        query_params:
          - name: limit
            value: <limit>
        param_values:
          - name: customer_id
            references:
              - dataset: stripe_connector_example
                field: customer.id
                direction: from
          - name: limit
            connector_param: items_per_page
        data_path: data
        pagination:
          strategy: cursor
          configuration:
            cursor_param: starting_after
            field: id
  - name: tax_id
    requests:
      read:
        method: GET
        path: /v1/customers/<customer_id>/tax_ids
        query_params:
          - name: limit
            value: <limit>
        param_values:
          - name: customer_id
            references:
              - dataset: stripe_connector_example
                field: customer.id
                direction: from
          - name: limit
            connector_param: items_per_page
        data_path: data
        pagination:
          strategy: cursor
          configuration:
            cursor_param: starting_after
            field: id
      delete:
        method: DELETE
        path: /v1/customers/<customer_id>/tax_ids/<tax_id>
        param_values:
          - name: customer_id
            references:
              - dataset: stripe_connector_example
                field: tax_id.customer
                direction: from
          - name: tax_id
            references:
              - dataset: stripe_connector_example
                field: tax_id.id
                direction: from
  - name: invoice
    requests:
      read:
        method: GET
        path: /v1/invoices
        query_params:
          - name: customer
            value: <customer_id>
          - name: limit
            value: <limit>
        param_values:
          - name: customer_id
            references:
              - dataset: stripe_connector_example
                field: customer.id
                direction: from
          - name: limit
            connector_param: items_per_page
        data_path: data
        pagination:
          strategy: cursor
          configuration:
            cursor_param: starting_after
            field: id
      delete:
        method: DELETE
        ignore_errors: true # You can only delete draft invoices. You can't delete invoices created by subscriptions.
        path: /v1/invoices/<invoice_id>
        param_values:
          - name: invoice_id
            references:
              - dataset: stripe_connector_example
                field: invoice.id
                direction: from
  - name: invoice_item
    requests:
      read:
        method: GET
        path: /v1/invoiceitems
        query_params:
          - name: customer
            value: <customer_id>
          - name: limit
            value: <limit>
        param_values:
          - name: customer_id
            references:
              - dataset: stripe_connector_example
                field: customer.id
                direction: from
          - name: limit
            connector_param: items_per_page
        data_path: data
        pagination:
          strategy: cursor
          configuration:
            cursor_param: starting_after
            field: id
      delete:
        method: DELETE
        ignore_errors: true # Can't delete an invoice item that is attached to an invoice that is no longer editable
        path: /v1/invoiceitems/<invoice_item_id>
        param_values:
         - name: invoice_item_id
           references:
              - dataset: stripe_connector_example
                field: invoice_item.id
                direction: from
  - name: subscription
    requests:
      read:
        method: GET
        path: /v1/subscriptions
        query_params:
          - name: customer
            value: <customer_id>
          - name: limit
            value: <limit>
        param_values:
          - name: customer_id
            references:
              - dataset: stripe_connector_example
                field: customer.id
                direction: from
          - name: limit
            connector_param: items_per_page
        data_path: data
        pagination:
          strategy: cursor
          configuration:
            cursor_param: starting_after
            field: id
      delete:
        method: DELETE
        path: /v1/subscriptions/<subscription_id>
        param_values:
          - name: subscription_id
            references:
              - dataset: stripe_connector_example
                field: subscription.id
                direction: from
```
