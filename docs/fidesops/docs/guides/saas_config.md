## What is a SaaS configuration schema?

A SaaS connector is defined in two parts, the [Dataset](datasets.md) and the SaaS config. The Dataset describes the data that is available from the connector and the SaaS config describes how to connect and retrieve/update the data in the connector. If you contrast this to a [database connector](database_connectors.md), the ways to retrieve/update data conform to a specification (such as SQL) and are consistent. When accessing data from APIs, each application or even different endpoints within the same application can follow different patterns. It was necessary to have a flexible configuration to be able to define the different access/update patterns. Keep in mind that SaaS configs are only applicable to SaaS connectors, not database connectors.

In short, you can think of the Dataset as the "what" (what data is available from this API) and the SaaS config as the "how" (how to access and update the data).
#### An example SaaS config

For this guide, we will use the SaaS config to connect to Mailchimp, this config defines:

- The domain and authentication requirements for an HTTP client to Mailchimp
- A test request for verifying the connection was set up correctly
- Endpoints to the following resources within the Mailchimp API:
    - `GET` and `PUT` for the [members](https://mailchimp.com/developer/marketing/api/list-members/) resource
    - `GET` for the [conversations](https://mailchimp.com/developer/marketing/api/conversations/) resource
    - `GET` for the [messages](https://mailchimp.com/developer/marketing/api/conversation-messages/) resource


The following is an example SaaS config for Mailchimp:
```yaml
saas_config:
  fides_key: mailchimp_connector_example
  name: Mailchimp SaaS Config
  description: A sample schema representing the Mailchimp connector for Fidesops
  version: 0.0.1

  connector_params:
    - name: domain
    - name: username
    - name: api_key

  client_config:
    protocol: https
    host:
      connector_param: domain
    authentication:
      strategy: basic_authentication
      configuration:
        username:
          connector_param: username
        password:
          connector_param: api_key

  test_request:
    method: GET
    path: /3.0/lists
    
  endpoints:
  - name: messages
    requests:
      read:
        method: GET
        path: /3.0/conversations/<conversation_id>/messages
        param_values:
          - name: conversation_id
            references:
              - dataset: mailchimp_connector_example
                field: conversations.id
                direction: from
        data_path: conversation_messages
        postprocessors:
          - strategy: filter
            configuration:
              field: from_email
              value:
                identity: email
  - name: conversations
    requests:
      read:
        method: GET
        path: /3.0/conversations
        query_params:
          - name: count
            value: 1000
          - name: offset
            value: 0
        param_values:
          - name: placeholder
            identity: email
        data_path: conversations
        pagination:
          strategy: offset
          configuration:
            incremental_param: offset
            increment_by: 1000
            limit: 10000
  - name: member
    requests:
      read:
        method: GET
        path: /3.0/search-members
        query_params:
          - name: query
            value: <email>
        param_values:
          - name: email
            identity: email
        data_path: exact_matches.members
      update:
        method: PUT
        path: /3.0/lists/<list_id>/members/<subscriber_hash>
        param_values:
          - name: list_id
            references:
              - dataset: mailchimp_connector_example
                field: member.list_id
                direction: from
          - name: subscriber_hash
            references:
              - dataset: mailchimp_connector_example
                field: member.id
                direction: from
```


A SaaS config schema contains the following metadata fields:

- `fides_key` Used to uniquely identify the connector, this field is used to link a SaaS config to a dataset.
- `name` A human-readable name for the connector.
- `description` Used to add a useful description.
- `version` Used to track different versions of the SaaS config.

And the following complex fields which we will cover in detail below:

- `connector_params`
- `client_config`
- `test_request`
- `endpoints`
- `data_protection_request`

#### Connector params
The `connector_params` field is used to describe a list of settings which a user must configure as part of the setup. This section should just include the name of the parameter but not the actual value. These are added as part of the ConnectionConfig [secrets](database_connectors.md#set-the-connectionconfigs-secrets).

```yaml
connector_params:
  - name: host
  - name: username
  - name: password
```

#### Client config
The `client_config` describes the necessary information to be able to create a base HTTP client. Notice that the values for host, username, and password are not defined here, only references in the form of a `connector_param` which Fidesops uses to insert the actual value from the stored secrets.

```yaml
client_config:
  protocol: https
  host:
    connector_param: host
  authentication:
    strategy: basic_authentication
    configuration:
      username:
        connector_param: username
      password:
        connector_param: password
```

The authentication strategies are swappable. In this example we used the `basic_authentication` strategy which uses a `username` and `password` in the configuration. An alternative to this is to use `bearer_authentication` which looks like this:
```yaml
authentication:
  strategy: bearer_authentication
  configuration:
    token:
      connector_param: api_key
```

#### Test request
Once the base client is defined we can use a `test_request` to verify our hostname and credentials. This is in the form of an idempotent request (usually a read). The testing approach is the same for any [ConnectionConfig test](database_connectors.md#testing-your-connection).
```yaml
test_request:
  method: GET
  path: /3.0/lists
```

#### Data Protection Request
If your third party integration supports something like a GDPR delete endpoint, that can be configured as a `data_protection_request`.  It has similar attributes to the test request or endpoint requests, but it is generally one endpoint that removes all user PII in one go. 
```yaml
  data_protection_request:
    method: POST
    path: /v1beta/workspaces/<workspace_name>/regulations
    param_values:
      - name: workspace_name
        connector_param: workspace
      - name: user_id
        identity: email
    body: '{"regulation_type": "Suppress_With_Delete", "attributes": {"name": "userId", "values": ["<user_id>",]}}'
    client_config:
      protocol: https
      host:
        connector_param: config_domain
      authentication:
        strategy: bearer_authentication
        configuration:
          username:
            connector_param: access_token

```
#### Endpoints
This is where we define how we are going to access and update each collection in the corresponding Dataset. The endpoint section contains the following members:

- `name` This name corresponds to a Collection in the corresponding Dataset.
- `after` To configure if this endpoint should run after other endpoints or collections. This should be a list of collection addresses, for example: `after: [ mailchimp_connector_example.member ]` would cause the current endpoint to run after the member endpoint.
- `requests` A map of `read`, `update`, and `delete` requests for this collection. Each collection can define a way to read and a way to update the data. Each request is made up of:
    - `method` The HTTP method used for the endpoint.
    - `path` A static or dynamic resource path. The dynamic portions of the path are enclosed within angle brackets `<dynamic_value>` and are replaced with values from `param_values`.
    - `headers` and `query_params` The HTTP headers and query parameters to include in the request.
        - `name` the value to use for the header or query param name.
        - `value` can be a static value, one or more of `<dynamic_value>`, or a mix of static and dynamic values (prefix `<value>`) which will be replaced with the value sourced from the `request_param` with a matching name.
    - `body` (optional) static or dynamic request body, with dynamic portions enclosed in brackets, just like `path`. These dynamic values will be replaced with values from `param_values`.
    - `param_values`
        - `name` Used as the key to reference this value from dynamic values in the path, headers, query, or body params.
        - `references` These are the same as `references` in the Dataset schema. It is used to define the source of the value for the given request_param.
        - `identity` Used to access the identity values passed into the privacy request such as email or phone number.
        - `connector_param` Used to access the user-configured secrets for the connection.
    - `ignore_errors` A boolean. If true, we will ignore non-200 status codes.
    - `data_path`: The expression used to access the collection information from the raw JSON response.
    - `postprocessors` An optional list of response post-processing strategies. We will ignore this for the example scenarios below but an in depth-explanation can be found under [SaaS Post-Processors](saas_postprocessors.md)
    - `pagination` An optional strategy used to get the next set of results from APIs with resources spanning multiple pages. Details can be found under [SaaS Pagination](saas_pagination.md).
    - `grouped_inputs` An optional list of reference fields whose inputs are dependent upon one another.  For example, an endpoint may need both an `organization_id` and a `project_id` from another endpoint.  These aren't independent values, as a `project_id` belongs to an `organization_id`.  You would specify this as ["organization_id", "project_id"].
    - `client_config` Specify optional embedded Client Configs if an individual request needs a different protocol, host, or authentication strategy from the base Client Config

## Param values in more detail
The `param_values` list is what provides the values to our various placeholders in the path, headers, query params and body. Values can be `identities` such as email or phone number, `references` to fields in other collections, or `connector_params` which are defined as part of configuring a SaaS connector. Whenever a placeholder is encountered, the placeholder name is looked up in the list of `param_values` and corresponding value is used instead. Here is an example of placeholders being used in various locations:

```yaml
messages:
  requests:
    read:
      method: GET
      path: /<version>/messages
      headers:
        - name: Content-Type
          value: application/json
        - name: On-Behalf-Of
          value: <email>
        - name: Token
          value: Custom <api_key>
      query_params:
        - name: count
          value: 100
        - name: organization:
          value: <org_id>
        - name: where:
          value: properties["$email"]=="<email>"
      param_values:
        - name: email
          identity: email
        - name: api_key
          connector_param: api_key
        - name: org_id
          connector_param: org_id
        - name: version
          connector_param: version
```
## How are requests generated?
The following HTTP request properties are generated for each request based on the endpoint configuration:

- method
- path
- headers
- query params
- body

#### Method
This is a required field since a read, update, or delete endpoint might use any of the HTTP methods to perform the given action.

#### Path
This can be a static value or use placeholders. If the placeholders to build the path are not found at request-time, the request will fail.

#### Headers and query params
These can also be static or use placeholders. If a placeholder is missing, the request will continue and omit the given header or query param in the request.

If reference values are used for the placeholders, each value will be processed independently unless the `grouped_inputs` field is set. The following examples use query params but this applies to headers as well.

**With ungrouped inputs (default)**
```yaml
read:
  method: GET
  path: /v1/disputes
  query_params:
    - name: charge
      value: <charge_id>
    - name: line_item
      value: <line_item_id>
  param_values:
  - name: charge_id
    references:
      - dataset: connector_example
        field: charge.id
        direction: from
  - name: line_item_id
    references:
      - dataset: connector_example
        field: charge.line_item.id
        direction: from
```
```yaml
GET /v1/disputes?charge=1
GET /v1/disputes?charge=2
GET /v1/disputes?charge=3
GET /v1/disputes?line_item=a
GET /v1/disputes?line_item=b
GET /v1/disputes?line_item=c
```

**With grouped inputs**
```yaml
read:
  method: GET
  path: /v1/disputes
  grouped_inputs: [charge_id, payment_intent_id]
  query_params:
    - name: charge
      value: <charge_id>
    - name: line_item
      value: <line_item_id>
  param_values:
  - name: charge_id
    references:
      - dataset: connector_example
        field: charge.id
        direction: from
  - name: line_item_id
    references:
      - dataset: connector_example
        field: charge.line_item.id
        direction: from
```
```yaml
GET /v1/disputes?charge=1&line_item=a
GET /v1/disputes?charge=2&line_item=b
GET /v1/disputes?charge=3&line_item=c
```

#### Body
The body can be static or use placeholders. If the placeholders to build the body are not found at request-time, the request will fail.

**Placeholder options for updates**

The following placeholders can be included in the body of an update:

- `<masked_object_fields>` - any masked fields, along with their masked value
- `<all_object_fields>` - all object fields, including the masked fields and values

Fidesops will automatically fill in the value of these placeholders with the appropriate contents.

**Example**

An access request returned the following row: 
```json
{
  "id": 123,
  "name": "Bobby Hill",
  "address": "Arlen TX"
}
```

With the `name` field masked, the value of each placeholder would be:

| Placeholder | Value |
|---|---|
| `<masked_object_fields>` | `"name":"MASKED"` |
| `<all_object_fields>` | `"id":123,"name":"MASKED","address":"Arlen TX"` |

!!! Tip "`all_object_fields` should be used if non-masked fields are required as part of the update payload."

**Read-Only fields** 

A field can be flagged as `read-only` in the dataset to exclude it from the value of `<all_object_fields>` (for example, if including the `id` would cause an error).

```yaml
- name: id
  data_categories: [system.operations]
  fidesops_meta:
    read_only: True
```
This would result in the following change, with `id` removed from the result:

| Placeholder | Value |
|---|---|
| `<all_object_fields>` | `"name":"MASKED","address":"Arlen TX"` |


## Example scenarios
#### Dynamic path with dataset references
```yaml
endpoints:
  - name: messages
    requests:
      read:
        method: GET
        path: /3.0/conversations/<conversation_id>/messages
        param_values:
          - name: conversation_id
            references:
              - dataset: mailchimp_connector_example
                field: conversations.id
                direction: from
```
In this example, we define `/3.0/conversations/<conversation_id>/messages` as the resource path for messages and define the path param of `conversation_id` as coming from the `id` field of the `conversations` collection. A separate GET HTTP request will be issued for each `conversations.id` value.

```yaml
# For three conversations with IDs of 1,2,3
GET /3.0/conversations/1/messages
GET /3.0/conversations/2/messages
GET /3.0/conversations/2/messages
```

#### Identity as a query param
```yaml
endpoints:
  - name: member
    requests:
      read:
        method: GET
        path: /3.0/search-members
        query_params:
          - name: query
            value: <email>
        param_values:
          - name: email
            identity: email
```
In this example, the placeholder in the `query` query param would be replaced with the value of the `request_param` with a name of `email`, which is the `email` identity. The result would look like this:
```
GET /3.0/search-members?query=name@email.com
```

#### Data update with a dynamic path
```yaml
endpoints:
  - name: member
    requests:
      update:
        method: PUT
        path: /3.0/lists/<list_id>/members/<subscriber_hash>
        param_values:
          - name: list_id
            references:
              - dataset: mailchimp_connector_example
                field: member.list_id
                direction: from
          - name: subscriber_hash
            references:
              - dataset: mailchimp_connector_example
                field: member.id
                direction: from
```
This example uses two dynamic path variables, one from `member.id` and one from `member.list_id`. Since both of these are references to the `member` collection, we must first issue a data retrieval (which will happen automatically if the `read` request is defined). If a call to `GET /3.0/search-members` returned the following `member` object:
```yaml
{
    "list_id": "123",
    "id": "456",
    "merge_fields": {
      "FNAME": "First",
      "LNAME": "Last"
    }
}
```
Then the update request would be:
```yaml
PUT /3.0/lists/123/members/456

{
    "list_id": "123",
    "id": "456",
    "merge_fields": {
      "FNAME": "MASKED",
      "LNAME": "MASKED"
    }
}
```
and the contents of the body would be masked according to the configured [policy](policies.md).


#### Data update with a dynamic HTTP body

Sometimes, the update request needs a different body structure than what we obtain from the read request. In this example, we use a custom HTTP body that contains our masked object fields.
```yaml
update:
  method: PUT
  path: /crm/v3/objects/contacts
  body: '{
    "properties": {
      <masked_object_fields>
      "user_ref_id": <user_ref_id>            
    }
  }'
  param_values:
    - name: user_ref_id
      references:
        - dataset: dataset_test
          field: contacts.user_ref_id
          direction: from
```

Fidesops will replace the `<masked_object_fields>` placeholder with the result of the policy-driven masking service, for example `{'company': None, 'email': None}`.

This results in the following update request:
```yaml
PUT /crm/v3/objects/contacts

{
  "properties": {
      "company": "None",
      "email": "None"
      "user_ref_id": "p983u4ncp3q8u4r"
  }
}
```


## How does this relate to graph traversal?

Fidesops uses the available Datasets to [generate a graph](query_execution.md) of all reachable data and the dependencies between Datasets. For SaaS connectors, all the references and identities are stored in the `param_values`, therefore we must merge both the SaaS config and Dataset to provide a complete picture for the graph traversal. Using Mailchimp as an example the Dataset collection and SaaS config endpoints for `messages` looks like this:

```yaml
collections:
  - name: messages
    fields:
      - name: id
        data_categories: [system.operations]
      - name: conversation_id
        data_categories: [system.operations]
      - name: from_label
        data_categories: [system.operations]
      - name: from_email
        data_categories: [user.provided.identifiable.contact.email]
      - name: subject
        data_categories: [system.operations]
      - name: message
        data_categories: [system.operations]
      - name: read
        data_categories: [system.operations]
      - name: timestamp
        data_categories: [system.operations]
```

```yaml
endpoints:
  - name: messages
    requests:
      read:
        method: GET
        path: /3.0/conversations/<conversation_id>/messages
        param_values:
          - name: conversation_id
            references:
              - dataset: mailchimp_connector_example
                field: conversations.id
                direction: from
        postprocessors:
          - strategy: unwrap
            configuration:
              data_path: conversation_messages
          - strategy: filter
            configuration:
              field: from_email
              value:
                identity: email
```

An example of the augmented Dataset with the SaaS Config references would look like this:
```yaml
collections:
  - name: messages
    fields:
      - name: id
        data_categories: [system.operations]
      - name: conversation_id
        data_categories: [system.operations]
        fidesops_meta:
          references:
            - dataset: mailchimp_connector_example
              field: conversations.id
              direction: from
      - name: from_label
        data_categories: [system.operations]
      - name: from_email
        data_categories: [user.provided.identifiable.contact.email]
      - name: subject
        data_categories: [system.operations]
      - name: message
        data_categories: [system.operations]
      - name: read
        data_categories: [system.operations]
      - name: timestamp
        data_categories: [system.operations]
```
Notice how the `conversation_id` field is updated with a reference from `mailchimp_connector_example.conversations.id`. This means that the `conversations` collection must be retrieved first to forward the conversation IDs to the messages collection for further processing.

## What if a collection has no dependencies?
In the Mailchimp example, you might have noticed the `placeholder` request param.
```yaml
endpoints:
  - name: conversations
    requests:
      read:
        method: GET
        path: /3.0/conversations
        query_params:
          - name: count
            value: 1000
          - name: offset
            value: 0
        param_values:
          - name: placeholder
            identity: email
```
Some endpoints might not have any external dependencies on `identity` or Dataset `reference` values. The way the Fidesops [graph traversal](query_execution.md) interprets this is as an unreachable collection. At this time, the way to mark this as reachable is to include a `request_param` with an identity or a reference. In the future we plan on having collections like these still be considered reachable even without this placeholder (the request_param name is not relevant, we just chose placeholder for this example).