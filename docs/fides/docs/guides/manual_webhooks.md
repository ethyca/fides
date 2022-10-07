# Manual Webhooks

Manual webhooks are a simple way for data to be manually uploaded for an access request. Erasure requests are not supported at this time.
They differ from the more complex [manual connection configs](../getting-started/datasets.md#Configure-a-manual-Dataset) that integrate directly with the graph.
Manual webhooks gather data *outside* of the graph as a first step, and are more similar to [policy_webhooks](policy_webhooks.md).


If you have manual webhooks defined, privacy request execution will exit early and remain in a state of `requires_input`.
Once data has been manually uploaded for all the manual webhooks, then the privacy request can be resumed. Data uploaded
for manual webhooks is passed on directly to the data subject alongside the data package. It is
not filtered on data category.  Any manual data uploaded is passed on as-is.



## Configuration

### Create a connection config of type `manual_webhook`


```json title="<code>POST api/v1/connection</code>"
[
    {"name": "Manual Webhook ConnectionConfig",
    "key": "manual_webhook_key",
    "connection_type": "manual_webhook",
    "access": "read"
    }
]
```

| Field | Description |
|----|----|
| `key` | *Optional.* A unique key used to manage your connection config. This is auto-generated from `name` if left blank. Accepted values are alphanumeric, `_`, and `.`. |
| `name` | A unique user-friendly name for your connection config. This key will also be used to identity the manual webhook|
| `connection_type` | Should be `manual_webhook` for the resource described here. |
| `access` | One of `read` or `write` |


### Define the fields expected for your `manual_webhook`

Submit a list of fields that will need to be manually uploaded.


```json title="<code>PATCH api/v1/connection/{{manual_webhook_key}}/access_manual_webhook</code>"
{
    "fields": [
        {"pii_field": "First Name", "dsr_package_label": "first_name"},
        {"pii_field": "Last Name", "dsr_package_label": "last_name"},
        {"pii_field": "Phone Number", "dsr_package_label": null},
        {"pii_field": "Height", "dsr_package_label": "height"}
    ]
}
```

| Field | Description |
|----|----|
| `fields` | *Required.* A list of field mappings with `pii_field` and `dsr_package_label` keys. The `pii_field` is the label fidesops will display when it solicits manual input, and the `dsr_package_label` is the identifier fidesops will use when it uploads the data to the data subject.  If no `dsr_package_label` is supplied, it will be created from the `pii_field`.


### Upload manual webhook data for a given privacy request

Privacy request execution will exit early with a status of `requires_input` if we're missing data for `manual_webhooks`.
A request will need to be made for each manual_webhook to upload the requested data before request execution can proceed.

Note that the fields here are dynamic and should match the fields specified on the manual webhook. All fields are optional.
If no data exists, an empty dictionary should be uploaded. Fidesops treats this upload as confirmation that the
system was searched for data related to the data subject.

```json title="<code>PATCH /privacy-request/{{privacy_request_id}}/access_manual_webhook/{{manual_webhook_key}}</code>"
{
    "first_name": "Jane",
    "last_name": "Customer"
}
```

### Resume Privacy Request Execution

Once a PrivacyRequest with `requires_input` has had all of its manual data uploaded, prompt the privacy request to resume.

```json title="<code>POST /privacy-request/{{privacy_request_id}}/resume_from_requires_input</code>"
```

#### Example Upload

In this example, we visited one postgres collection automatically and retrieved Jane's `name`, `email`, and `id`.
Her `first_name` and `last_name` were manually uploaded as part of the `manual_webhook_key` Manual Webhook
and directly included here.

```json

{
  "postgres_example:customer": [
    {
      "name": "Jane Customer",
      "email": "customer-3@example.com",
      "id": 1
    }
  ],
  "manual_webhook_key": [
    {
      "first_name": "Jane",
      "last_name": "Customer"
    }
  ]
}
```
