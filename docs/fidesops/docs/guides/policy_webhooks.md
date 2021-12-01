# How-To: Configure Policy Webhooks

In this section we'll cover:

- What's a Policy Webhook?
- How do I configure Policy Webhooks?
    - Create a ConnectionConfig
    - Add ConnectionConfig secrets
    - Define PolicyPreWebhooks or PolicyPostWebhooks
- Expected webhook request and response format

Take me directly to the [Policy Webhooks API documentation](/fidesops/api/#operations-Policy_Webhooks-get_policy_pre_execution_webhooks_api_v1_policy__policy_key__webhook_pre_execution_get).


## Policy Webhook Defined

A Policy Webhook is an HTTPS Callback that you've defined on a Policy to call an external
REST API endpoint *before* or *after* a PrivacyRequest executes.

You can define as many webhooks as you'd like.  Webhooks can be `one_way`, 
where we will just ping your API and move on, or `two_way`, where we will wait for a response. Any `derived_identities`
returned from a `two_way` webhook will be saved and can be used to locate other user information.  For example, a webhook
might take a known `email` `identity` and use that to find a `phone_number` `identity`.

Another use case for a Policy Webhook might be to log a user out of your mobile app after you've cleared
their data from your system.  In this case, you'd create a `Policy` and a `ConnectionConfig` to describe the URL to hit
to clear the cache. You'd then create a `one-way` `PolicyPostWebhook` to run after your PrivacyRequest executes. 


## Configuration

Big picture, you will define an `https` `ConnectionConfig` that contains the details to
make a request to your API endpoint.  You will then define a `PolicyPreWebhook` or a `PolicyPostWebhook`
for a specific `Policy` using that `ConnectionConfig`.

### Creating an HTTPS ConnectionConfig

The information that describes how to connect to your API endpoint lives on a `ConnectionConfig`. We also use
`ConnectionConfigs` to connect to databases like `PostgreSQL` and `MongoDB`.  This same construct can help us store
how to connect to an external API endpoint. 

For more information on ConnectionConfigs, see how to [Create a ConnectionConfig.](/fidesops/api/#operations-Connections-put_connections_api_v1_connection_put)

To start, send a `PATCH` request to `/v1/connection` to add an `https` ConnectionConfig:

```json
[
    {
      "name": "My Webhook Connection Configuration",
      "key": "test_webhook_connection_config",
      "connection_type": "https",
      "access": "read"
    }
]
```

### Adding ConnectionConfig Secrets

The secret details needed to talk to your API endpoint are defined by making a PUT to the ConnectionConfig Secrets endpoint:
These credentials are stored encrypted in the `fidesops` `app` database.

See API docs on how to [Set a ConnectionConfig's Secrets](/fidesops/api#operations-Connections-put_connection_config_secrets_api_v1_connection__connection_key__secret_put).

`PUT` `/v1/connection/test_webhook_connection_config`

```json
    {
        "url": "example.com",
        "authorization": "test_authorization"
    }
```

### Defining Pre-Execution or Post-Execution Policy Webhooks
After you've defined a ConnectionConfig, you can create lists of webhooks to run *before* (PolicyPreWebhooks)
or *after* (PolicyPostWebhooks) a PrivacyRequest is executed.

If you are defining PolicyPreWebhooks, all desired PolicyPreWebhooks should be included in the request
body in the desired order.  Any PolicyPreWebhooks on the Policy *not* included in the request, will be removed from the 
Policy. The same applies for PolicyPostWebhooks.

To update your list of PolicyPreWebhooks:

`PUT /policy/<policy_key>/webhook/pre_execution`

```json
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

This creates two webhooks that are run sequentially for the Policy before a PrivacyRequest runs.

Similarly, to update your list of Post-Execution webhooks on a Policy:

`PUT /policy/<policy_key>/webhook/post_execution`


See API docs for more information on how to [Update PolicyPreWebhooks](/fidesops/api#operations-Policy_Webhooks-create_or_update_pre_execution_webhooks_api_v1_policy__policy_key__webhook_pre_execution_put)
and how to [Update PolicyPostWebhooks](/fidesops/api#operations-Policy_Webhooks-create_or_update_post_execution_webhooks_api_v1_policy__policy_key__webhook_post_execution_put).


### Updating a Single Webhook

To update a single PolicyPreWebhook or PolicyPostWebhook, send a PATCH request to update selected attributes.
Note that updates to order can likewise update the order of related webhooks.

The following example will update the PolicyPreWebhook with key `webhook_hook` to be `two_way` instead of 
`one_way` and will update its order from 0 to 1.  Because we've defined two PolicyPreWebhooks, this causes the 
webhook at position 1 to move to position 0. 


`PATCH /policy/<policy_key>/webhook/pre-execution/wake_up_snowflake_db`

```json
{
    "direction": "two_way",
    "order": 1
}
```

#### Response
Because this PATCH request updated the order of other webhooks, a reordered summary is included under the 
`new_order` attribute:
```json
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

Similarly, to update your a Post-Execution webhook on a Policy:

`PATCH /policy/<policy_key>/webhook/post_execution/<post_execution_key>`

See API docs for more information on how to [PATCH a PolicyPreWebhook](/fidesops/api#operations-Policy_Webhooks-update_pre_execution_webhook_api_v1_policy__policy_key__webhook_pre_execution__pre_webhook_key__patch)
and how to [PATCH a PolicyPostWebhook](/fidesops/api#operations-Policy_Webhooks-update_post_execution_webhook_api_v1_policy__policy_key__webhook_post_execution__post_webhook_key__patch).


## Expected Webhook Request and Response Format

In progress, this will be added in the next release.  For now, you have the ability to configure webhooks. The work
to trigger those callbacks is ongoing.