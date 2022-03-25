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
    path: /3.0/lists

  endpoints:
  - name: messages
    requests:
      read:
        path: /3.0/conversations/<conversation_id>/messages
        request_params:
          - name: conversation_id
            type: path
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
        path: /3.0/conversations
        request_params:
          - name: count
            type: query
            default_value: 1000
          - name: offset
            type: query
            default_value: 0
          - name: placeholder
            type: query
            identity: email
        data_path: conversations
  - name: member
    requests:
      read:
        path: /3.0/search-members
        request_params:
          - name: query
            type: query
            identity: email
            data_type: string
        data_path: exact_matches.members
      update:
        path: /3.0/lists/<list_id>/members/<subscriber_hash>
        request_params:
          - name: list_id
            type: path
            references:
              - dataset: mailchimp_connector_example
                field: member.list_id
                direction: from
          - name: subscriber_hash
            type: path
            references:
              - dataset: mailchimp_connector_example
                field: member.id
                direction: from
```


A SaaS config schema contains the following metadata fields:

- `fides_key` Used to uniquely identify the connector, this field is used to link a SaaS config to a dataset.
- `name` A human readable name for the connector.
- `description` Used to add a useful description.
- `version` Used to track different versions of the SaaS config.

And the following complex fields which we will cover in detail below:

- `connector_params`
- `client_config`
- `test_request`
- `endpoints`
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
  path: /3.0/lists
```
#### Endpoints
This is where we define how we are going to access and update each collection in the corresponding Dataset. The endpoint section contains the following members:

- `name` This name corresponds to a Collection in the corresponding Dataset.
- `requests` A map of `read` and `update` requests for this collection. Each collection can define a way to read and a way to update the data. Each request is made up of:
    - `path` A static or dynamic resource path. The dynamic portions of the path are enclosed within angle brackets `<dynamic_value>` and are replaced with values from `request_params`.
    - `method` (optional) HTTP method. Defaults to `GET` for read requests, `PUT` for update requests. Other options are `POST`, `PATCH`, or `DELETE`.
    - `body` (optional) static or dynamic request body, with dynamic portions enclosed in brackets, just like `path`. These dynamic values will be replaced with values from `request_params`. For update requests, you'll need to additionally annotated `<masked_object_fields>` as a placeholder for the fidesops generated update values.
    - `request_params`
        - `name` Used as the key for query param values, or to map this param to a value placeholder in the path.
        - `type` Can be "query", "path", or "body".
        - `references` These are the same as `references` in the Dataset schema. It is used to define the source of the value for the given request_param.
        - `identity` Used to access the identity values passed into the privacy request such as email or phone number.
        - `default_value` Hard-coded default value for a `request_param`. This is most often used for query params since a static path param can just be included in the `path`.
        - `connector_param` Used to access the user-configured secrets for the connection.
    - `data_path`: The expression used to access the collection information from the raw JSON response.
    - `postprocessors` An optional list of response post-processing strategies. We will ignore this for the example scenarios below but an in depth-explanation can be found under [SaaS Post-Processors](saas_postprocessors.md)
    - `pagination` An optional strategy used to get the next set of results from APIs with resources spanning multiple pages. Details can be found under [SaaS Pagination](saas_pagination.md)
    - `grouped_inputs` An optional list of reference fields whose inputs are dependent upon one another.  For example, an endpoint may need both an `organization_id` and a `project_id` from another endpoint.  These aren't independent values, as a `project_id` belongs to an `organization_id`.  You would specify this as ["organization_id", "project_id"].

## Example scenarios
#### Dynamic path with dataset references
```yaml
endpoints:
  - name: messages
    requests:
      read:
        path: /3.0/conversations/<conversation_id>/messages
        request_params:
          - name: conversation_id
            type: path
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
        path: /3.0/search-members
        request_params:
          - name: query
            type: query
            identity: email
```
In this example, the `email` identity value is used as a param named "query" and would look like this:
```
GET /3.0/search-members?query=name@email.com
```

#### Data update with a dynamic path
```yaml
endpoints:
  - name: member
    requests:
      update:
        path: /3.0/lists/<list_id>/members/<subscriber_hash>
        request_params:
          - name: list_id
            type: path
            references:
              - dataset: mailchimp_connector_example
                field: member.list_id
                direction: from
          - name: subscriber_hash
            type: path
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
```yml
update:
  path: /crm/v3/objects/contacts
  body: {
    "properties": {
      <masked_object_fields>
      "user_ref_id": <user_ref_id>            
    }
  }
  request_params:
    - name: user_ref_id
      type: body
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

Fidesops uses the available Datasets to [generate a graph](query_execution.md) of all reachable data and the dependencies between Datasets. For SaaS connectors, all the references and identities are stored in the `request_params`, therefore we must merge both the SaaS config and Dataset to provide a complete picture for the graph traversal. Using Mailchimp as an example the Dataset collection and SaaS config endpoints for `messages` looks like this:

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
        path: /3.0/conversations/<conversation_id>/messages
        request_params:
          - name: conversation_id
            type: path
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
In the Mailchimp example, you might have noticed the `placeholder` query param.
```yaml
endpoints:
  - name: conversations
    requests:
      read:
        path: /3.0/conversations
        request_params:
          - name: count
            type: query
            default_value: 1000
          - name: offset
            type: query
            default_value: 0
          - name: placeholder
            type: query
            identity: email
```
Some endpoints might not have any external dependencies on `identity` or Dataset `reference` values. The way the Fidesops [graph traversal](query_execution.md) interprets this is as an unreachable collection. At this time, the way to mark this as reachable is to include `request_param` with a "synthetic link" (an unused query param) to an identity or a reference. In the future we plan on having collections like these still be considered reachable even without this synthetic placeholder (the request_param name is not relevant, we just chose placeholder for this example).