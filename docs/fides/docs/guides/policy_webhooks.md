
# Configure Execution Policy Webhooks

## What is a Policy webhook?

An webhook is an HTTPS callback that you've defined on an [execution policy](../getting-started/execution_policies.md) to call an external REST API endpoint either *before* or *after* a privacy bequest executes.

Webhooks can be `one_way`, where the API is pinged and the privacy request continues, or `two_way`, where Fides will wait for a response. Any derived values returned from a `two_way` webhook will be saved, and can be used to locate other user information. For example, a webhook might take a known `email` `identity` and use that to find a `phone_number` `derived_identity`.

## Configuration

The process below will define an `https` [Connection](../getting-started/database_connectors.md) that contains the details to make a request to your API endpoint, and then create a `PolicyPreWebhook` or a `PolicyPostWebhook`for a specific execution policy using that Connection.

### Create an HTTPS Connection

The information that describes how to connect to your API endpoint is represented by a Fides [Connection](../getting-started/database_connectors.md)

```json title="<code>PATCH /v1/connection</code>"
[
    {
      "name": "My Webhook Connection Configuration",
      "key": "test_webhook_connection_config",
      "connection_type": "https",
      "access": "read"
    }
]
```


### Add your Connection secrets

The credentials needed to access your API endpoint are defined by making a PUT to the Connection Secrets endpoint. These credentials are encrypted in the Fides `app` database

```json title="<code>PUT /v1/connection/test_webhook_connection_config</code>"
    {
        "url": "https://www.example.com",
        "authorization": "test_authorization"
    }
```

### Define pre-execution or post-execution webhooks

After you've defined a new Connection, you can create lists of webhooks to run *before* (`PolicyPreWebhooks`)
or *after* (`PolicyPostWebhooks`) a privacy request is executed.

When defining webhooks, they should be included in the request body in the desired order. Any webhooks on the execution policy *not* included in the request will be removed from the policy.

To update a list of PolicyPreWebhooks

```json title="<code>PUT /policy/{policy_key}/webhook/pre_execution</code>"
[
    {
        "connection_config_key": "test_webhook_connection_config",
        "direction": "one_way",
        "key": "wake_up_snowflake_db",
        "name": "Wake up Snowflake DB Webhook"
    },
     {
        "connection_config_key": "test_webhook_connection_config",
        "direction": "two_way",
        "key": "prep_systems_webhook",
        "name": "Prep Systems Webhook"
    }
]
```

This creates two webhooks that are run sequentially for the execution policy before a privacy request runs.

Similarly, to update your list of post-execution webhooks on a policy, use the following endpoint

```
PUT /policy/{policy_key}/webhook/post_execution
```

See API docs for more information on how to [Update PolicyPreWebhooks](../api/index.md#operations-Policy_Webhooks-create_or_update_pre_execution_webhooks_api_v1_policy__policy_key__webhook_pre_execution_put)
and how to [Update PolicyPostWebhooks](../api/index.md#operations-Policy_Webhooks-create_or_update_post_execution_webhooks_api_v1_policy__policy_key__webhook_post_execution_put).

### Update a single webhook

To update a single webhook, send a PATCH request to update selected attributes. **Updates to order can likewise update the order of related webhooks.**

The following example will update the PolicyPreWebhook with key `webhook_hook` to be `two_way` instead of
`one_way`, and will update its order from 0 to 1.  Because we've defined two PolicyPreWebhooks, this causes the
webhook at position 1 to move to position 0.

```json title="<code>PATCH /policy/{policy_key}/webhook/pre-execution/wake_up_snowflake_db</code>"
{
    "direction": "two_way",
    "order": 1
}
```

Because this PATCH request updated the order of other webhooks, a reordered summary is included under the
`new_order` attribute:

```json title="Response"
{
    "resource": {
        "direction": "two_way",
        "key": "wake_up_snowflake_db",
        "name": "Wake up Snowflake DB Webhook",
        "connection_config": "<TRUNCATED>",
        "order": 1
    },
    "new_order": [
        {
            "key": "prep_systems_webhook",
            "order": 0
        },
        {
            "key": "wake_up_snowflake_db",
            "order": 1
        }
    ]
}
```

Similarly, to update your a post-execution webhook on an execution policy, use the following endpoint:

```
PATCH /policy/{policy_key}/webhook/post_execution/{post_execution_key}
```

See API docs for more information on how to [PATCH a PolicyPreWebhook](../api/index.md#operations-Policy_Webhooks-update_pre_execution_webhook_api_v1_policy__policy_key__webhook_pre_execution__pre_webhook_key__patch)
and how to [PATCH a PolicyPostWebhook](../api/index.md#operations-Policy_Webhooks-update_post_execution_webhook_api_v1_policy__policy_key__webhook_post_execution__post_webhook_key__patch).

## Webhook request format

Before and after running access or erasure requests, Fides will send requests to any configured webhooks in sequential order
with the following request body:

```json title="<code>POST {user-defined URL}</code>"
{
  "privacy_request_id": "pri_029832ba-3b84-40f7-8946-82aec6f95448",
  "direction": "one_way | two_way",
  "callback_type": "pre | post",
  "identity": {
    "email": "customer-1@example.com",
    "phone_number": "555-5555"
  }
}
```

These attributes were configured at the time of webhook creation. Known identities are also embedded in the request.

For `two-way` webhooks, Fides includes specific headers to pause request execution while any additional processing takes place

```json
{
  "reply-to": "/privacy-request/{privacy_request_id}/resume",
  "reply-to-token": "<jwe_token>"
}
```

To resume, send a request to the `reply-to` URL with the `reply-to-token`.  The `reply-to-token` will
expire when your Redis cache expires (represented by `default_ttl_seconds` in your Fides [config](../installation/configuration.md). When a request expires, it is be given an `error` status, and requires resubmission.

## Webhook response format

Your webhook should respond immediately. If more processing time is needed, either make sure it is configured as a
`one-way` webhook, or reply with `halt=True` if you want to pause execution and wait for any processing to finish.
**Note that only pre-execution webhooks can pause execution.**

Responses aren ot expected from `one-way` webhooks, but `two-way` webhooks should respond with the following

```json
{
  "derived_identity": {
    "email": "customer-1@gmail.com",
    "phone_number": "555-5555"
  },
  "halt": "true | false"
}
```

Derived identity is optional: a returned email or phone number will replace currently known emails or phone numbers.

## Resuming request execution

Once a paused webhook has completed processing, send a request to the `reply-to` URL sent in the original request header, along with the `reply-to-token` auth token.

```json title="<code>POST privacy_request/{privacy-request-id}/resume</code>"
{
  "derived_identity": {
    "email": "customer-1@gmail.com",
    "phone_number": "555-5555"
  }
}

```

If there are no derived identities, send an empty `{}` request body.

The `reply-to-token` is a JWE containing the current webhook ID, scopes to access the callback endpoint, and the datetime the token is issued.  Fides unpacks this and resumes the privacy request execution after the specified webhook. The `reply-to-token` expires after a set amount of time, (the `privacy_request_delay_timeout` in your Fides [config](../installation/configuration.md)). Once the Redis cache expires, Fides no longer has the original identity data and the privacy request should be resubmitted
