<<<<<<< HEAD:docs/fides/docs/guides/policy_webhooks.md
# Configure Execution Policy Webhooks

## What is a Policy webhook?

An webhook is an HTTPS callback that you've defined on an [execution policy](../getting-started/execution_policies.md) to call an external REST API endpoint either *before* or *after* a privacy bequest executes.

Webhooks can be `one_way`, where the API is pinged and the privacy request continues, or `two_way`, where Fides will wait for a response. Any derived values returned from a `two_way` webhook will be saved, and can be used to locate other user information. For example, a webhook might take a known `email` `identity` and use that to find a `phone_number` `derived_identity`.

## Configuration
The process below will define an `https` [Connection](../getting-started/database_connectors.md) that contains the details to make a request to your API endpoint, and then create a `PolicyPreWebhook` or a `PolicyPostWebhook`for a specific execution policy using that Connection.

### Create an HTTPS Connection
The information that describes how to connect to your API endpoint is represented by a Fides [Connection](../getting-started/database_connectors.md). 
=======
# Configure Policy Webhooks

## What is a Policy webhook?

A Policy webhook is an HTTPS Callback that you've defined on a Policy to call an external
REST API endpoint *before* or *after* a Privacy Request executes.

You can define as many webhooks as you'd like.  Webhooks can be `one_way`, where we will just ping your API and move on,
or `two_way`, where we will wait for a response. Any `derived_identities` returned from a `two_way` webhook will be saved
and can be used to locate other user information.  For example, a webhook might take a known `email` `identity` and
use that to find a `phone_number` `derived_identity`.

Another use case for a Policy Webhook might be to log a user out of your mobile app after you've cleared
their data from your system.  In this case, you'd create a `Policy` and a `ConnectionConfig` to describe the URL to hit
to clear the cache. You'd then create a `one-way` `PolicyPostWebhook` to run after your PrivacyRequest executes.

## Configuration

Big picture, you will define an `https` `ConnectionConfig` that contains the details to make a request to your API endpoint.  
You will then define a `PolicyPreWebhook` or a `PolicyPostWebhook`for a specific `Policy` using that `ConnectionConfig`.

### Create an HTTPS ConnectionConfig

The information that describes how to connect to your API endpoint lives on a `ConnectionConfig`. We also use
`ConnectionConfigs` to connect to databases like `PostgreSQL` and `MongoDB`.  This same construct can help us store
how to connect to an external API endpoint.

For more information on ConnectionConfigs, see how to [Create a ConnectionConfig.](/fidesops/api/#operations-Connections-put_connections_api_v1_connection_put)
>>>>>>> unified-fides-2:docs/fidesops/docs/guides/policy_webhooks.md

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

<<<<<<< HEAD:docs/fides/docs/guides/policy_webhooks.md
### Add your Connection secrets
The credentials needed to access your API endpoint are defined by making a PUT to the Connection Secrets endpoint. These credentials are encrypted in the Fides `app` database.
=======
### Adding ConnectionConfig secrets

The secret details needed to talk to your API endpoint are defined by making a PUT to the ConnectionConfig Secrets endpoint:
These credentials are stored encrypted in the `fidesops` `app` database.

See API docs on how to [Set a ConnectionConfig's Secrets](/fidesops/api#operations-Connections-put_connection_config_secrets_api_v1_connection__connection_key__secret_put).
>>>>>>> unified-fides-2:docs/fidesops/docs/guides/policy_webhooks.md

```json title="<code>PUT /v1/connection/test_webhook_connection_config</code>"
    {
        "url": "https://www.example.com",
        "authorization": "test_authorization"
    }
```

### Define pre-execution or post-execution webhooks
<<<<<<< HEAD:docs/fides/docs/guides/policy_webhooks.md
After you've defined a new Connection, you can create lists of webhooks to run *before* (`PolicyPreWebhooks`)
or *after* (`PolicyPostWebhooks`) a privacy request is executed.

When defining webhooks, they should be included in the request body in the desired order. Any webhooks on the execution policy *not* included in the request will be removed from the policy.

To update a list of PolicyPreWebhooks:
=======

After you've defined a `ConnectionConfig`, you can create lists of webhooks to run *before* (`PolicyPreWebhooks`)
or *after* (`PolicyPostWebhooks`) a PrivacyRequest is executed.

If you are defining PolicyPreWebhooks, all desired PolicyPreWebhooks should be included in the request
body in the desired order.  Any PolicyPreWebhooks on the Policy *not* included in the request, will be removed from the
Policy. The same applies for PolicyPostWebhooks.

To update your list of PolicyPreWebhooks:
>>>>>>> unified-fides-2:docs/fidesops/docs/guides/policy_webhooks.md

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

<<<<<<< HEAD:docs/fides/docs/guides/policy_webhooks.md
This creates two webhooks that are run sequentially for the execution policy before a privacy request runs.

Similarly, to update your list of post-execution webhooks on a policy, use the following endpoint:
=======
This creates two webhooks that are run sequentially for the Policy before a PrivacyRequest runs.

Similarly, to update your list of Post-Execution webhooks on a Policy:
>>>>>>> unified-fides-2:docs/fidesops/docs/guides/policy_webhooks.md

```
PUT /policy/{policy_key}/webhook/post_execution
```

<<<<<<< HEAD:docs/fides/docs/guides/policy_webhooks.md
See API docs for more information on how to [Update PolicyPreWebhooks](../api/index.md#operations-Policy_Webhooks-create_or_update_pre_execution_webhooks_api_v1_policy__policy_key__webhook_pre_execution_put)
and how to [Update PolicyPostWebhooks](../api/index.md#operations-Policy_Webhooks-create_or_update_post_execution_webhooks_api_v1_policy__policy_key__webhook_post_execution_put).

### Update a single webhook
To update a single webhook, send a PATCH request to update selected attributes. **Updates to order can likewise update the order of related webhooks.**

The following example will update the PolicyPreWebhook with key `webhook_hook` to be `two_way` instead of
`one_way`, and will update its order from 0 to 1.  Because we've defined two PolicyPreWebhooks, this causes the
=======
See API docs for more information on how to [Update PolicyPreWebhooks](/fidesops/api#operations-Policy_Webhooks-create_or_update_pre_execution_webhooks_api_v1_policy__policy_key__webhook_pre_execution_put)
and how to [Update PolicyPostWebhooks](/fidesops/api#operations-Policy_Webhooks-create_or_update_post_execution_webhooks_api_v1_policy__policy_key__webhook_post_execution_put).

### Update a single webhook

To update a single PolicyPreWebhook or PolicyPostWebhook, send a PATCH request to update selected attributes.
Note that updates to order can likewise update the order of related webhooks.

The following example will update the PolicyPreWebhook with key `webhook_hook` to be `two_way` instead of
`one_way` and will update its order from 0 to 1.  Because we've defined two PolicyPreWebhooks, this causes the
>>>>>>> unified-fides-2:docs/fidesops/docs/guides/policy_webhooks.md
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

<<<<<<< HEAD:docs/fides/docs/guides/policy_webhooks.md
Similarly, to update your a post-execution webhook on an execution policy, use the following endpoint:
=======
Similarly, to update your a Post-Execution webhook on a Policy:
>>>>>>> unified-fides-2:docs/fidesops/docs/guides/policy_webhooks.md

```
PATCH /policy/{policy_key}/webhook/post_execution/{post_execution_key}
```

<<<<<<< HEAD:docs/fides/docs/guides/policy_webhooks.md
See API docs for more information on how to [PATCH a PolicyPreWebhook](../api/index.md#operations-Policy_Webhooks-update_pre_execution_webhook_api_v1_policy__policy_key__webhook_pre_execution__pre_webhook_key__patch)
and how to [PATCH a PolicyPostWebhook](../api/index.md#operations-Policy_Webhooks-update_post_execution_webhook_api_v1_policy__policy_key__webhook_post_execution__post_webhook_key__patch).

## Webhook request format
Before and after running access or erasure requests, Fides will send requests to any configured webhooks in sequential order
=======
See API docs for more information on how to [PATCH a PolicyPreWebhook](/fidesops/api#operations-Policy_Webhooks-update_pre_execution_webhook_api_v1_policy__policy_key__webhook_pre_execution__pre_webhook_key__patch)
and how to [PATCH a PolicyPostWebhook](/fidesops/api#operations-Policy_Webhooks-update_post_execution_webhook_api_v1_policy__policy_key__webhook_post_execution__post_webhook_key__patch).

## Webhook request format

Before and after running access or erasure requests, fidesops will send requests to any configured webhooks in sequential order
>>>>>>> unified-fides-2:docs/fidesops/docs/guides/policy_webhooks.md
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

<<<<<<< HEAD:docs/fides/docs/guides/policy_webhooks.md
These attributes were configured at the time of webhook creation. Known identities are also embedded in the request.

For `two-way` webhooks, Fides includes specific headers to pause request execution while any additional processing takes place.
=======
Most of these attributes were configured by you: the `direction`, the `callback_type` ("pre" for `PolicyPreWebhook`s that will run
before PrivacyRequest execution or "post" for `PolicyPostWebhook`s that will run after PrivacyRequestExecution).
Known identities are also embedded in the request.

For `two-way` `PolicyPreWebhooks`, we include specific headers in case you need to pause PrivacyRequest
execution while you take care of additional processing on your end.
>>>>>>> unified-fides-2:docs/fidesops/docs/guides/policy_webhooks.md

```json
{
  "reply-to": "/privacy-request/{privacy_request_id}/resume",
  "reply-to-token": "<jwe_token>"
}
```

<<<<<<< HEAD:docs/fides/docs/guides/policy_webhooks.md
To resume, send a request to the `reply-to` URL with the `reply-to-token`.  The `reply-to-token` will
expire when your Redis cache expires (represented by `default_ttl_seconds` in your Fides [config](../installation/configuration.md). When a request expires, it is be given an `error` status, and requires resubmission.

## Webhook response format
Your webhook should respond immediately. If more processing time is needed, either make sure it is configured as a
`one-way` webhook, or reply with `halt=True` if you want to pause execution and wait for any processing to finish.
**Note that only pre-execution webhooks can pause execution.**

Responses aren ot expected from `one-way` webhooks, but `two-way` webhooks should respond with the following:
=======
 To resume, you should send a request back to the `reply-to` URL with the `reply-to-token`.  The `reply-to-token` will
expire when your redis cache expires: `config.redis.default_ttl_seconds` (Fidesops uses the redis cache to temporarily
 store identity data).  At this point, your PrivacyRequest will be given an `error` status, and you would have to resubmit
the PrivacyRequest.

## Webhook response format

Your webhook should respond immediately. If more processing time is needed, either make sure it is configured as a
`one-way` webhook, or reply with `halt=True` if you want to pause execution and wait for your processing to finish.
Note that only `PolicyPreWebhooks` can pause execution.

We don't expect a response from `one-way` webhooks, but `two-way` webhooks should respond with the following:
>>>>>>> unified-fides-2:docs/fidesops/docs/guides/policy_webhooks.md

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
<<<<<<< HEAD:docs/fides/docs/guides/policy_webhooks.md
Once a paused webhook has completed processing, send a request to the `reply-to` URL sent in the original request header, along with the `reply-to-token` auth token.
=======

If your webhook needed more processing time, once completed, send a request to the `reply-to` URL
given to you in the original request header with the `reply-to-token` auth token.
>>>>>>> unified-fides-2:docs/fidesops/docs/guides/policy_webhooks.md

```json title="<code>POST privacy_request/{privacy-request-id}/resume</code>"
{
  "derived_identity": {
    "email": "customer-1@gmail.com",
    "phone_number": "555-5555"
  }
}

```

<<<<<<< HEAD:docs/fides/docs/guides/policy_webhooks.md
If there are no derived identities, send an empty `{}` request body.

The `reply-to-token` is a JWE containing the current webhook ID, scopes to access the callback endpoint, and the datetime the token is issued.  Fides unpacks this and resumes the privacy request execution after the specified webhook. The `reply-to-token` expires after a set amount of time, (the `privacy_request_delay_timeout` in your Fides [config](../installation/configuration.md)). Once the Redis cache expires, Fides no longer has the original identity data and the privacy request should be resubmitted.
=======
If there are no derived identities, an empty `{}` request body will suffice.

The `reply-to-token` is a JWE containing the current webhook id, scopes to access the callback endpoint,
and the datetime the token is issued.  We unpack this and resume the privacy request execution after the
specified webhook. The `reply-to-token` expires after a set amount of time, specified by the `config.execution.privacy_request_delay_timeout` config variable. Once the redis cache expires, fidesops no longer has the original identity data and the privacy request should be resubmitted.
>>>>>>> unified-fides-2:docs/fidesops/docs/guides/policy_webhooks.md
